from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Any

# --- Composition Configuration (safe defaults) ---

# Keep deterministic organ ordering across all reports.
ORGAN_ORDER = [
    "liver",
    "gallbladder_cbd",
    "pancreas",
    "spleen",
    "kidneys",
    "bladder",
    "uterus",
    "ovaries",
    "prostate",
    "peritoneum",
    "misc",
]

ORGAN_LABELS = {
    "liver": "Liver",
    "gallbladder_cbd": "Gallbladder/CBD",
    "pancreas": "Pancreas",
    "spleen": "Spleen",
    "kidneys": "Kidneys",
    "bladder": "Urinary bladder",
    "uterus": "Uterus",
    "ovaries": "Ovaries",
    "prostate": "Prostate",
    "peritoneum": "Peritoneal cavity",
    "misc": "Other findings",
}

# Prefix mapping keeps rule keys/logic untouched and only drives composition grouping.
# NOTE: This is only effective when atoms carry a source_key. The composer supports it,
# but legacy templates that emit plain strings won't provide source keys.
ORGAN_PREFIX_MAP = {
    "liv_": "liver",
    "gbl_": "gallbladder_cbd",
    "gb_": "gallbladder_cbd",
    "cbd_": "gallbladder_cbd",
    "pan_": "pancreas",
    "panc_": "pancreas",
    "spl_": "spleen",
    "kid_": "kidneys",
    "kid_r_": "kidneys",
    "kid_l_": "kidneys",
    "bla_": "bladder",
    "uter_": "uterus",
    "ovy_": "ovaries",
    "ovr_": "ovaries",
    "pros_": "prostate",
    "asc_": "peritoneum",
    "aff_": "peritoneum",
}

SECTION_TITLE_MAP = {
    "liver": "liver",
    "gallbladder": "gallbladder_cbd",
    "biliary": "gallbladder_cbd",
    "pancreas": "pancreas",
    "spleen": "spleen",
    "kidney": "kidneys",
    "bladder": "bladder",
    "uterus": "uterus",
    "ovary": "ovaries",
    "prostate": "prostate",
    "ascites": "peritoneum",
    "peritone": "peritoneum",
    "free fluid": "peritoneum",
}

NEGATIVE_PREFIX = re.compile(r"^\s*no\s+", re.IGNORECASE)
MEASUREMENT_HINT = re.compile(r"\b(measures?|measuring|diameter|length|size|bipolar)\b|\b\d+(?:\.\d+)?\s?(cm|mm)\b", re.IGNORECASE)
STATUS_HINT = re.compile(r"\b(normal|unremarkable|not dilated|preserved|satisfactory)\b", re.IGNORECASE)

NOT_VISUALIZED_HINT = re.compile(r"\b(not\s+visuali[sz]ed|not\s+seen|non\s*visuali[sz]ed|obscured|poorly\s+seen)\b", re.IGNORECASE)
GENERIC_NORMAL_HINT = re.compile(r"\b(normal|unremarkable|within\s+normal|no\s+abnormal)\b", re.IGNORECASE)

TOPIC_HINTS = [
    ("visibility", re.compile(r"\b(not\s+visuali[sz]ed|not\s+seen|obscured|poorly\s+seen)\b", re.IGNORECASE)),
    ("size", re.compile(r"\b(measures?|measuring|diameter|length|size|bipolar)\b|\b\d+(?:\.\d+)?\s?(cm|mm)\b", re.IGNORECASE)),
    ("parenchyma", re.compile(r"\b(echogenic|echotexture|coars|fatty|heterogeneous|homogeneous|attenuation)\b", re.IGNORECASE)),
    ("lesion", re.compile(r"\b(lesion|mass|cyst|nodule|tumou?r|hemangioma|collection|abscess)\b", re.IGNORECASE)),
    ("ducts", re.compile(r"\b(cbd|common\s+bile\s+duct|biliary|intrahepatic|ducts?|dilat|dilation|dilatation)\b", re.IGNORECASE)),
    ("vascular", re.compile(r"\b(portal\s+vein|hepatic\s+vein|ivc|aorta|artery|vein|vascular)\b", re.IGNORECASE)),
    ("stones", re.compile(r"\b(stone|stones|calculus|calculi)\b", re.IGNORECASE)),
    ("fluid", re.compile(r"\b(ascites|free\s+fluid|peritoneal\s+fluid|pleural\s+effusion)\b", re.IGNORECASE)),
]

TOPIC_ORDER_BY_ORGAN = {
    "liver": ["visibility", "size", "parenchyma", "lesion", "ducts", "vascular", "other"],
    "gallbladder_cbd": ["visibility", "stones", "ducts", "size", "other"],
    "kidneys": ["visibility", "size", "parenchyma", "stones", "lesion", "ducts", "other"],
    "spleen": ["visibility", "size", "parenchyma", "lesion", "other"],
    "pancreas": ["visibility", "size", "parenchyma", "lesion", "other"],
    "peritoneum": ["visibility", "fluid", "lesion", "other"],
    "bladder": ["visibility", "size", "lesion", "stones", "other"],
    "uterus": ["visibility", "size", "lesion", "other"],
    "ovaries": ["visibility", "size", "lesion", "other"],
    "prostate": ["visibility", "size", "lesion", "other"],
    "misc": ["other"],
}

MAX_NEGATIVE_ITEMS = 6


@dataclass
class NarrativeAtom:
    organ: str
    side: str
    kind: str
    priority: int
    text: str
    source_key: str = ""
    topic: str = "other"
    role: str = ""


def compose_narrative(narrative_json: dict, values_json: Optional[dict] = None, include_debug: bool = False) -> dict:
    sections = narrative_json.get("sections", []) if isinstance(narrative_json, dict) else []
    atoms = _sections_to_atoms(sections)
    grouped: Dict[str, List[NarrativeAtom]] = {}
    for atom in atoms:
        grouped.setdefault(atom.organ, []).append(atom)

    narrative_by_organ = []
    debug_atoms = {}
    debug_paragraphs = {}

    for organ in ORGAN_ORDER:
        organ_atoms = grouped.get(organ, [])
        if not organ_atoms:
            continue
        paragraph = compose_organ_paragraph(organ_atoms, organ)
        if not paragraph:
            continue
        narrative_by_organ.append(
            {
                "organ": organ,
                "label": ORGAN_LABELS.get(organ, organ.title()),
                "paragraph": paragraph,
            }
        )
        if include_debug:
            debug_atoms[organ] = [asdict(a) for a in organ_atoms]
            debug_paragraphs[organ] = paragraph

    narrative_text = "\n".join(f"{item['label']}: {item['paragraph']}" for item in narrative_by_organ)

    out = dict(narrative_json or {})
    out["narrative_by_organ"] = narrative_by_organ
    out["narrative_text"] = narrative_text
    if include_debug:
        out["composer_debug"] = {
            "atoms_by_organ": debug_atoms,
            "paragraphs_by_organ": debug_paragraphs,
        }
    return out


def _sections_to_atoms(sections: Iterable[dict]) -> List[NarrativeAtom]:
    """Convert generator sections into NarrativeAtoms.

    Backward compatible:
    - legacy sections: lines are strings
    Forward compatible:
    - lines can also be dicts: {text, source_key, organ, side, kind, priority, topic, role}
    """
    atoms: List[NarrativeAtom] = []
    for section_idx, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        title = str(section.get("title", ""))
        lines = section.get("lines", [])
        if not isinstance(lines, list):
            continue

        for line_idx, raw_line in enumerate(lines):
            payload: Dict[str, Any]
            if isinstance(raw_line, dict):
                payload = dict(raw_line)
                raw_text = str(payload.get("text", "") or "")
            else:
                payload = {}
                raw_text = str(raw_line or "")

            text = _normalize_text(raw_text)
            if not text:
                continue

            source_key = str(payload.get("source_key", "") or "")
            organ = str(payload.get("organ") or _infer_organ(title, text, source_key))
            kind = str(payload.get("kind") or _infer_kind(text))
            side = str(payload.get("side") or _infer_side(source_key, text))
            topic = str(payload.get("topic") or _infer_topic(text, organ))
            role = str(payload.get("role") or _infer_role(kind, topic, text))

            priority = payload.get("priority")
            if isinstance(priority, int):
                pr = priority
            else:
                pr = section_idx * 100 + line_idx

            atoms.append(
                NarrativeAtom(
                    organ=organ,
                    side=side,
                    kind=kind,
                    priority=pr,
                    text=text,
                    source_key=source_key,
                    topic=topic,
                    role=role,
                )
            )
    return atoms


def _infer_organ(section_title: str, text: str, source_key: str = "") -> str:
    key = (source_key or "").lower()
    for prefix, organ in ORGAN_PREFIX_MAP.items():
        if key.startswith(prefix) or f"_{prefix}" in key:
            return organ

    lowered_title = (section_title or "").lower()
    for hint, organ in SECTION_TITLE_MAP.items():
        if hint in lowered_title:
            return organ

    lowered = text.lower()
    if "common bile duct" in lowered or " cbd" in f" {lowered} " or "gallbladder" in lowered:
        return "gallbladder_cbd"
    if "kidney" in lowered or "hydronephrosis" in lowered or "renal" in lowered:
        return "kidneys"
    if "liver" in lowered or "hepatic" in lowered or "portal vein" in lowered:
        return "liver"
    if "pancreas" in lowered:
        return "pancreas"
    if "spleen" in lowered:
        return "spleen"
    if "bladder" in lowered:
        return "bladder"
    if "uterus" in lowered:
        return "uterus"
    if "ovar" in lowered:
        return "ovaries"
    if "prostate" in lowered:
        return "prostate"
    if "ascites" in lowered or "free fluid" in lowered or "peritone" in lowered:
        return "peritoneum"
    return "misc"


def _normalize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = cleaned.rstrip(".").strip()
    return cleaned


def _infer_kind(text: str) -> str:
    if NEGATIVE_PREFIX.match(text):
        return "negative"
    if MEASUREMENT_HINT.search(text):
        return "measurement"
    if STATUS_HINT.search(text):
        return "status"
    return "positive"


def _infer_topic(text: str, organ: str) -> str:
    low = text.lower()
    for topic, rx in TOPIC_HINTS:
        if rx.search(low):
            return topic
    # organ-specific soft fallbacks
    if organ == "gallbladder_cbd" and ("stone" in low or "calculus" in low):
        return "stones"
    if organ == "peritoneum" and ("ascites" in low or "fluid" in low):
        return "fluid"
    return "other"


def _infer_role(kind: str, topic: str, text: str) -> str:
    # Simple role tagging used for composition decisions.
    if kind == "negative":
        return "negative"
    if kind == "status":
        return "status"
    if kind == "measurement":
        return "measurement"
    if topic == "visibility":
        return "visibility"
    return "positive"


def _infer_side(source_key: str, text: str) -> str:
    lowered = f"{source_key} {text}".lower()
    if "_r_" in lowered or lowered.startswith("kid_r_") or " right " in f" {lowered} ":
        return "R"
    if "_l_" in lowered or lowered.startswith("kid_l_") or " left " in f" {lowered} ":
        return "L"
    if "bilateral" in lowered or "both" in lowered:
        return "B"
    return "N"


def compose_organ_paragraph(atoms: List[NarrativeAtom], organ: str) -> str:
    if not atoms:
        return ""

    deduped = _dedupe_atoms(atoms)

    # Hard suppression: "not visualized" dominates the organ section.
    nv = _extract_visibility_statement(deduped)
    if nv:
        return _cap_sentences([nv])

    if organ == "kidneys":
        return _compose_kidneys(deduped)
    if organ == "gallbladder_cbd":
        return _compose_gallbladder_cbd(deduped)

    return _compose_generic_organ(deduped, organ)


def _compose_generic_organ(atoms: List[NarrativeAtom], organ: str) -> str:
    status, positives, measurements, negatives = _split_atoms(atoms)

    subject = _subject_for_organ(organ)

    # If we have positives, drop generic "normal/unremarkable" status lines to avoid contradiction.
    status_keep: List[NarrativeAtom] = []
    if positives:
        for s in status:
            if not GENERIC_NORMAL_HINT.search(s.text):
                status_keep.append(s)
    else:
        status_keep = status

    nonneg = status_keep + positives + measurements
    if not nonneg and negatives:
        # Rare: only negatives present.
        return _cap_sentences([_compress_negatives(negatives, standalone=True)])

    # Topic-driven ordering
    topic_order = TOPIC_ORDER_BY_ORGAN.get(organ, TOPIC_ORDER_BY_ORGAN["misc"])
    ordered_fragments: List[str] = []
    for topic in topic_order:
        for a in sorted([x for x in nonneg if x.topic == topic], key=lambda x: x.priority):
            ordered_fragments.append(_to_phrase(a.text, organ))
    # Any leftover "other" fragments not matched
    matched = set(ordered_fragments)
    for a in sorted([x for x in nonneg if x.topic not in topic_order], key=lambda x: x.priority):
        phrase = _to_phrase(a.text, organ)
        if phrase and phrase not in matched:
            ordered_fragments.append(phrase)

    # Build 1–2 main sentences for flow.
    main_sentences: List[str] = []
    if ordered_fragments:
        first = ordered_fragments[:3]
        rest = ordered_fragments[3:]

        main_sentences.append(_prefix_subject(subject, _join_clauses(first)))
        if rest:
            main_sentences.append(f"Additionally, {_prefix_subject(subject.lower(), _join_clauses(rest))}")

    neg_sentence = _compress_negatives(negatives, standalone=True)
    if neg_sentence:
        main_sentences.append(neg_sentence)

    return _cap_sentences(main_sentences)


def _subject_for_organ(organ: str) -> str:
    label = ORGAN_LABELS.get(organ, "Other findings")
    # Use clinically clean subjects.
    if organ == "peritoneum":
        return "The peritoneal cavity"
    return f"The {label.lower()}"


def _extract_visibility_statement(atoms: List[NarrativeAtom]) -> str:
    # If any atom explicitly says the organ is not visualized / not seen, keep only that sentence.
    for a in sorted(atoms, key=lambda x: x.priority):
        if NOT_VISUALIZED_HINT.search(a.text):
            # Keep original phrasing; just ensure it is a proper sentence.
            return a.text.strip().rstrip(".") + "."
    return ""


def _compose_kidneys(atoms: List[NarrativeAtom]) -> str:
    status, positives, measurements, negatives = _split_atoms(atoms)
    right_measure = _extract_side_measurement(measurements, "R")
    left_measure = _extract_side_measurement(measurements, "L")

    sentences: List[str] = []

    # Sentence 1: Measurements / baseline.
    if right_measure and left_measure:
        base = f"Both kidneys measure {right_measure} (right) and {left_measure} (left)"
    elif right_measure:
        base = f"The right kidney measures {right_measure}"
    elif left_measure:
        base = f"The left kidney measures {left_measure}"
    else:
        base = "Both kidneys are assessed"

    cmd = _common_phrase([a.text for a in status + positives], "corticomedullary differentiation")
    if cmd:
        base = f"{base} with {cmd}"

    sentences.append(base + ".")

    # Sentence 2+: Side-specific abnormalities, if any.
    asym = _side_specific_abnormalities(positives)
    if asym:
        sentences.extend(asym)

    neg_sentence = _compress_negatives(negatives, standalone=True)
    if neg_sentence:
        sentences.append(neg_sentence)

    return _cap_sentences(sentences)


def _compose_gallbladder_cbd(atoms: List[NarrativeAtom]) -> str:
    status, positives, measurements, negatives = _split_atoms(atoms)

    all_items = status + positives + measurements + negatives
    cbd_items = [a for a in all_items if _mentions_cbd(a.text)]
    gb_items = [a for a in all_items if not _mentions_cbd(a.text)]

    gb_nonneg = [a for a in gb_items if a.kind != "negative"]
    gb_clause = _join_clauses([_to_phrase(a.text, "gallbladder_cbd") for a in gb_nonneg])
    gb_neg = _compress_negatives([a for a in gb_items if a.kind == "negative"], standalone=False)

    if not gb_clause:
        gb_text = "The gallbladder is unremarkable"
    else:
        gb_text = _prefix_subject("The gallbladder", gb_clause)

    if gb_neg:
        gb_text = f"{gb_text} with {gb_neg}"

    cbd_clause = _build_cbd_clause(cbd_items)
    if cbd_clause:
        return _cap_sentences([f"{gb_text}, and the CBD {cbd_clause}"])
    return _cap_sentences([gb_text])


def _build_cbd_clause(items: List[NarrativeAtom]) -> str:
    if not items:
        return ""
    phrases = [_to_phrase(item.text, "gallbladder_cbd") for item in items if item.kind != "negative"]
    negs = [item for item in items if item.kind == "negative"]

    preferred = [p for p in phrases if "not dilated" in p.lower()]
    clause = preferred[0] if preferred else _join_clauses(phrases)

    # Add negative CBD-specific items if present
    if negs:
        cbd_neg = _compress_negatives(negs, standalone=False)
        if cbd_neg:
            clause = _join_clauses([clause, cbd_neg])

    if clause.startswith("the cbd"):
        clause = clause[7:].strip()

    if clause.startswith(("is ", "measures", "measure", "shows", "demonstrates", "appears")):
        return clause
    return f"is {clause}"


def _split_atoms(atoms: List[NarrativeAtom]) -> Tuple[List[NarrativeAtom], List[NarrativeAtom], List[NarrativeAtom], List[NarrativeAtom]]:
    sorted_atoms = sorted(atoms, key=lambda x: x.priority)
    status = [a for a in sorted_atoms if a.kind in {"status", "qualifier"}]
    positives = [a for a in sorted_atoms if a.kind == "positive"]
    measurements = [a for a in sorted_atoms if a.kind == "measurement"]
    negatives = [a for a in sorted_atoms if a.kind == "negative"]
    return status, positives, measurements, negatives


def _dedupe_atoms(atoms: List[NarrativeAtom]) -> List[NarrativeAtom]:
    # Exact dedupe + safe substring dedupe to reduce repetition.
    seen = set()
    deduped: List[NarrativeAtom] = []
    for atom in sorted(atoms, key=lambda x: x.priority):
        key = re.sub(r"\s+", " ", atom.text.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(atom)

    # Substring prune: if a short statement is fully contained in a longer one, drop the short one.
    texts = [a.text.lower() for a in deduped]
    drop = set()
    for i, ti in enumerate(texts):
        if i in drop:
            continue
        for j, tj in enumerate(texts):
            if i == j:
                continue
            if len(ti) < 14:
                continue
            if ti in tj and len(tj) > len(ti) + 8:
                drop.add(i)
                break

    return [a for idx, a in enumerate(deduped) if idx not in drop]


def _to_phrase(text: str, organ: str) -> str:
    t = _normalize_text(text)
    patterns = [
        r"^the\s+liver\s+",
        r"^liver\s+",
        r"^the\s+gallbladder\s+",
        r"^gallbladder\s+",
        r"^the\s+pancreas\s+",
        r"^pancreas\s+",
        r"^the\s+spleen\s+",
        r"^spleen\s+",
        r"^the\s+right\s+kidney\s+",
        r"^the\s+left\s+kidney\s+",
        r"^right\s+kidney\s+",
        r"^left\s+kidney\s+",
        r"^the\s+kidneys\s+",
        r"^kidneys\s+",
        r"^common\s+bile\s+duct\s+",
        r"^the\s+common\s+bile\s+duct\s+",
        r"^the\s+cbd\s+",
        r"^cbd\s+",
    ]
    for p in patterns:
        t = re.sub(p, "", t, flags=re.IGNORECASE)

    t = t.strip()
    if t and t[0].isupper():
        t = t[0].lower() + t[1:]
    return t


def _join_clauses(fragments: List[str]) -> str:
    clean = [f.strip(" ,") for f in fragments if str(f).strip(" ,")]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


def _prefix_subject(subject: str, clause: str) -> str:
    """Attach a clause to a subject without creating 'is shows' type grammar."""
    c = (clause or "").strip()
    if not c:
        return subject.strip()

    # If the clause already starts with a valid verb phrase, don't insert "is".
    if c.startswith(("is ", "are ", "shows", "show", "demonstrates", "demonstrate", "appears", "appear", "measures", "measure", "contains", "contain", "reveals", "reveal", "has ", "have ")):
        return f"{subject.strip()} {c}"
    # Otherwise, default to copula.
    return f"{subject.strip()} is {c}"


def _compress_negatives(negatives: List[NarrativeAtom], standalone: bool = True) -> str:
    if not negatives:
        return ""

    items: List[str] = []
    for atom in negatives:
        txt = _to_phrase(atom.text, atom.organ)
        txt = re.sub(r"^no\s+", "", txt, flags=re.IGNORECASE).strip(" .,")
        if txt:
            items.append(txt)

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    if not deduped:
        return ""

    if len(deduped) > MAX_NEGATIVE_ITEMS:
        keep = deduped[: MAX_NEGATIVE_ITEMS - 1]
        keep.append("other abnormality")
        deduped = keep

    if len(deduped) == 1:
        body = deduped[0]
    elif len(deduped) == 2:
        body = f"{deduped[0]} or {deduped[1]}"
    else:
        body = f"{', '.join(deduped[:-1])}, or {deduped[-1]}"

    prefix = "No" if standalone else "no"
    return f"{prefix} {body}" + ("." if standalone else "")


def _extract_side_measurement(measurements: List[NarrativeAtom], side: str) -> str:
    for atom in measurements:
        if atom.side != side and atom.side != "N":
            continue
        if side == "R" and "left" in atom.text.lower():
            continue
        if side == "L" and "right" in atom.text.lower():
            continue
        match = re.search(r"(\d+(?:\.\d+)?\s?(?:cm|mm))", atom.text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _mentions_cbd(text: str) -> bool:
    low = text.lower()
    return "common bile duct" in low or " cbd" in f" {low} "


def _common_phrase(texts: List[str], needle: str) -> str:
    for text in texts:
        low = text.lower()
        if needle in low:
            phrase = _to_phrase(text, "kidneys")
            if phrase.startswith("is "):
                phrase = phrase[3:]
            phrase = re.sub(r"\bis\b\s+", "", phrase, count=1)
            return phrase
    return ""


def _side_specific_abnormalities(positives: List[NarrativeAtom]) -> List[str]:
    right = [p for p in positives if p.side == "R"]
    left = [p for p in positives if p.side == "L"]
    if not right and not left:
        return []

    out: List[str] = []
    if right:
        out.append(f"The right kidney {_join_clauses([_to_phrase(p.text, 'kidneys') for p in right])}.")
    if left:
        out.append(f"The left kidney {_join_clauses([_to_phrase(p.text, 'kidneys') for p in left])}.")
    return out


def _cap_sentences(sentences: List[str]) -> str:
    # One paragraph per organ: keep all sentences (no hard truncation).
    clean = []
    for s in sentences:
        sentence = str(s or "").strip()
        if not sentence:
            continue
        if not sentence.endswith("."):
            sentence += "."
        # Normalize spacing around punctuation
        sentence = re.sub(r"\s+", " ", sentence)
        sentence = re.sub(r"\s+([,.;:])", r"\1", sentence)
        clean.append(sentence)
    return " ".join(clean).strip()
