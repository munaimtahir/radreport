from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Tuple


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


@dataclass
class NarrativeAtom:
    organ: str
    side: str
    kind: str
    priority: int
    text: str
    source_key: str = ""


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
                "label": ORGAN_LABELS[organ],
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
    atoms: List[NarrativeAtom] = []
    for section_idx, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        title = str(section.get("title", ""))
        lines = section.get("lines", [])
        if not isinstance(lines, list):
            continue
        for line_idx, raw_line in enumerate(lines):
            line = _normalize_text(str(raw_line or ""))
            if not line:
                continue
            organ = _infer_organ(title, line)
            kind = _infer_kind(line)
            side = _infer_side("", line)
            priority = section_idx * 100 + line_idx
            atoms.append(
                NarrativeAtom(
                    organ=organ,
                    side=side,
                    kind=kind,
                    priority=priority,
                    text=line,
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
    if "common bile duct" in lowered or " cbd" in lowered or "gallbladder" in lowered:
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
    if organ == "kidneys":
        return _compose_kidneys(deduped)
    if organ == "gallbladder_cbd":
        return _compose_gallbladder_cbd(deduped)

    status, positives, measurements, negatives = _split_atoms(deduped)
    label = ORGAN_LABELS.get(organ, "Other findings").lower()

    sentence_parts = []
    main_fragments = []
    if status:
        main_fragments.append(_to_phrase(status[0].text, organ))
    for atom in positives:
        main_fragments.append(_to_phrase(atom.text, organ))
    for atom in measurements:
        main_fragments.append(_to_phrase(atom.text, organ))

    if main_fragments:
        sentence_parts.append(f"The {label} {_join_clauses(main_fragments)}")

    negative_sentence = _compress_negatives(negatives)
    if negative_sentence:
        sentence_parts.append(negative_sentence)

    return _cap_sentences(sentence_parts)


def _compose_kidneys(atoms: List[NarrativeAtom]) -> str:
    status, positives, measurements, negatives = _split_atoms(atoms)
    right_measure = _extract_side_measurement(measurements, "R")
    left_measure = _extract_side_measurement(measurements, "L")

    sentence_parts = []

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

    asym = _side_specific_abnormalities(positives)
    if asym:
        sentence_parts.extend(asym)
    else:
        sentence_parts.append(base)

    negative_sentence = _compress_negatives(negatives)
    if negative_sentence:
        sentence_parts.append(negative_sentence)

    return _cap_sentences(sentence_parts)


def _compose_gallbladder_cbd(atoms: List[NarrativeAtom]) -> str:
    status, positives, measurements, negatives = _split_atoms(atoms)

    cbd_items = [a for a in status + positives + measurements + negatives if _mentions_cbd(a.text)]
    gb_items = [a for a in status + positives + measurements + negatives if not _mentions_cbd(a.text)]

    gb_clause = _join_clauses([_to_phrase(a.text, "gallbladder_cbd") for a in gb_items if a.kind != "negative"])
    gb_neg = _compress_negatives([a for a in gb_items if a.kind == "negative"], standalone=False)

    if not gb_clause:
        gb_clause = "is unremarkable"
    elif not gb_clause.startswith("is "):
        gb_clause = f"{gb_clause}"

    gb_text = f"The gallbladder {gb_clause}" if gb_clause.startswith("is ") else f"The gallbladder is {gb_clause}"
    if gb_neg:
        gb_text = f"{gb_text} with {gb_neg}"

    cbd_clause = _build_cbd_clause(cbd_items)
    if cbd_clause:
        return _cap_sentences([f"{gb_text}, and the CBD {cbd_clause}"])
    return _cap_sentences([gb_text])


def _build_cbd_clause(items: List[NarrativeAtom]) -> str:
    if not items:
        return ""
    phrases = [_to_phrase(item.text, "gallbladder_cbd") for item in items]
    preferred = [p for p in phrases if "not dilated" in p.lower()]
    if preferred:
        clause = preferred[0]
    else:
        clause = _join_clauses(phrases)
    if clause.startswith("the cbd"):
        clause = clause[7:].strip()
    if clause.startswith("is "):
        return clause
    if clause.startswith("measures") or clause.startswith("measure") or clause.startswith("shows"):
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
    seen = set()
    deduped = []
    for atom in sorted(atoms, key=lambda x: x.priority):
        key = re.sub(r"\s+", " ", atom.text.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(atom)
    return deduped


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
    if t and t[0].isupper():
        t = t[0].lower() + t[1:]
    return t


def _join_clauses(fragments: List[str]) -> str:
    clean = [f.strip(" ,") for f in fragments if f.strip(" ,")]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    if len(clean) == 2:
        return f"{clean[0]} and {clean[1]}"
    return f"{', '.join(clean[:-1])}, and {clean[-1]}"


def _compress_negatives(negatives: List[NarrativeAtom], standalone: bool = True) -> str:
    if not negatives:
        return ""
    items = []
    for atom in negatives:
        txt = _to_phrase(atom.text, atom.organ)
        txt = re.sub(r"^no\s+", "", txt, flags=re.IGNORECASE).strip(" .,")
        if not txt:
            continue
        items.append(txt)

    deduped = []
    seen = set()
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    if not deduped:
        return ""

    capped = deduped[:3]
    if len(capped) == 1:
        body = capped[0]
    elif len(capped) == 2:
        body = f"{capped[0]} or {capped[1]}"
    else:
        body = f"{', '.join(capped[:-1])}, or {capped[-1]}"

    return f"No {body}" + ("." if standalone else "")


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

    out = []
    if right:
        out.append(f"The right kidney {_join_clauses([_to_phrase(p.text, 'kidneys') for p in right])}.")
    if left:
        out.append(f"The left kidney {_join_clauses([_to_phrase(p.text, 'kidneys') for p in left])}.")
    return out


def _cap_sentences(sentences: List[str]) -> str:
    clean = []
    for s in sentences:
        sentence = s.strip()
        if not sentence:
            continue
        if not sentence.endswith("."):
            sentence += "."
        clean.append(sentence)
    return " ".join(clean[:2])
