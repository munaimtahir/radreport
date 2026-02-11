import React from "react";
import "./radiology-master-print.css";

export type RadiologyMeasurement = {
  label: string;
  value: string;
  unit?: string;
};

export type RadiologyFindingSection = {
  heading?: string;
  lines?: string[];
  paragraphs?: string[];
  bullets?: string[];
};

export type RadiologyMasterPayload = {
  header?: {
    logo_url?: string;
    center_lines?: string[];
    right_lines?: string[];
  };
  patient?: {
    name?: string;
    age?: string;
    sex?: string;
    mrn?: string;
    mobile?: string;
    ref_no?: string;
    referred_by?: string;
    study_datetime?: string;
    report_datetime?: string;
    clinical_indication?: string;
  };
  report_title?: string;
  sections?: {
    technique?: string[];
    comparison?: string[];
    findings?: RadiologyFindingSection[];
    measurements?: RadiologyMeasurement[];
    impression?: string[];
    recommendations?: string[];
  };
  signatories?: Array<{
    verification_label?: string;
    name?: string;
    credentials?: string;
    registration?: string;
  }>;
  footer?: {
    disclaimer?: string;
  };
};

type Props = {
  payload: RadiologyMasterPayload;
  actions?: React.ReactNode;
};

function hasText(value?: string | null): value is string {
  return !!value && value.trim().length > 0;
}

function row(label: string, value?: string | null) {
  if (!hasText(value)) return null;
  return (
    <div className="rm-field-row" key={label}>
      <div className="rm-field-label">{label}</div>
      <div className="rm-field-value">{value}</div>
    </div>
  );
}

function renderLines(lines?: string[]) {
  const clean = (lines || []).map((x) => (x || "").trim()).filter(Boolean);
  if (!clean.length) return null;
  return clean.map((line, idx) => (
    <p className="rm-paragraph" key={`${line}-${idx}`}>
      {line}
    </p>
  ));
}

export default function RadiologyMasterPrintLayout({ payload, actions }: Props) {
  const header = payload.header || {};
  const patient = payload.patient || {};
  const sections = payload.sections || {};
  const findings = sections.findings || [];
  const measurements = sections.measurements || [];
  const impression = (sections.impression || []).map((x) => x.trim()).filter(Boolean);
  const recommendations = (sections.recommendations || []).map((x) => x.trim()).filter(Boolean);
  const centerLines = (header.center_lines || []).map((x) => x.trim()).filter(Boolean);
  const rightLines = (header.right_lines || []).map((x) => x.trim()).filter(Boolean);
  const signatories = payload.signatories || [];

  const ageSex = [patient.age, patient.sex].filter(hasText).join(" / ");

  return (
    <div className="radiology-master-page">
      {actions ? <div className="radiology-master-toolbar">{actions}</div> : null}

      <article className="radiology-master-paper">
        <header className="rm-header">
          <div className="rm-logo-box">{hasText(header.logo_url) ? <img src={header.logo_url} alt="logo" /> : null}</div>

          <div className="rm-center-block">
            {centerLines.map((line, idx) => (
              <div key={`${line}-${idx}`} className={idx === 0 ? "rm-center-line-strong" : "rm-center-line"}>
                {line}
              </div>
            ))}
          </div>

          <div className="rm-right-block">
            {rightLines.map((line, idx) => (
              <div key={`${line}-${idx}`}>{line}</div>
            ))}
          </div>
        </header>

        <div className="rm-divider" />

        <section className="rm-patient">
          <div className="rm-patient-grid">
            <div>
              {row("Patient Name", patient.name)}
              {row("Age / Sex", ageSex)}
              {row("MRN / Patient ID", patient.mrn)}
              {row("Mobile", patient.mobile)}
            </div>
            <div>
              {row("Ref No / Accession", patient.ref_no)}
              {row("Referred By", patient.referred_by)}
              {row("Study Date/Time", patient.study_datetime)}
              {row("Report Date/Time", patient.report_datetime)}
            </div>
          </div>
          {hasText(patient.clinical_indication) ? (
            <div className="rm-indication">
              <span className="rm-field-label">Clinical Indication: </span>
              <span>{patient.clinical_indication}</span>
            </div>
          ) : null}
        </section>

        <h1 className="rm-title">{payload.report_title || "RADIOLOGY REPORT"}</h1>
        <div className="rm-divider" />

        {renderLines(sections.technique) ? (
          <section className="rm-section">
            <h2 className="rm-section-title">Technique</h2>
            {renderLines(sections.technique)}
          </section>
        ) : null}

        {renderLines(sections.comparison) ? (
          <section className="rm-section">
            <h2 className="rm-section-title">Comparison</h2>
            {renderLines(sections.comparison)}
          </section>
        ) : null}

        <section className="rm-section">
          <h2 className="rm-section-title">Findings</h2>
          {findings.length ? (
            findings.map((block, idx) => {
              const lines = (block.lines || []).map((x) => x.trim()).filter(Boolean);
              const paragraphs = (block.paragraphs || []).map((x) => x.trim()).filter(Boolean);
              const bullets = (block.bullets || []).map((x) => x.trim()).filter(Boolean);
              if (!lines.length && !paragraphs.length && !bullets.length) return null;
              return (
                <div key={`finding-${idx}`}>
                  {hasText(block.heading) ? <h3 className="rm-subheading">{block.heading}</h3> : null}
                  {lines.map((line, lineIdx) => (
                    <p className="rm-paragraph" key={`line-${lineIdx}`}>{line}</p>
                  ))}
                  {paragraphs.map((line, paraIdx) => (
                    <p className="rm-paragraph" key={`para-${paraIdx}`}>{line}</p>
                  ))}
                  {bullets.length ? (
                    <ul className="rm-list">
                      {bullets.map((item, bIdx) => (
                        <li key={`bullet-${bIdx}`}>{item}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              );
            })
          ) : (
            <p className="rm-paragraph">No findings provided.</p>
          )}
        </section>

        {measurements.length ? (
          <section className="rm-section">
            <h2 className="rm-section-title">Measurements</h2>
            <table className="rm-measurements">
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {measurements.map((m, idx) => (
                  <tr key={`m-${idx}`}>
                    <td>{m.label}</td>
                    <td>{m.value}{hasText(m.unit) ? ` ${m.unit}` : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ) : null}

        {impression.length ? (
          <section className="rm-impression">
            <h2 className="rm-section-title" style={{ marginTop: 0 }}>Impression</h2>
            <ul className="rm-list">
              {impression.map((line, idx) => (
                <li key={`impression-${idx}`}>{line}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {recommendations.length ? (
          <section className="rm-section">
            <h2 className="rm-section-title">Recommendations / Advice</h2>
            <ul className="rm-list">
              {recommendations.map((line, idx) => (
                <li key={`recommend-${idx}`}>{line}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {signatories.length ? (
          <section className="rm-signatures">
            <div className="rm-signature-stack">
              {signatories.map((sig, idx) => (
                <div className="rm-signature-item" key={`sig-${idx}`}>
                  <div>{sig.verification_label || "Electronically Verified"}</div>
                  {hasText(sig.name) ? <div className="rm-signature-name">{sig.name}</div> : null}
                  {hasText(sig.credentials) ? <div>{sig.credentials}</div> : null}
                  {hasText(sig.registration) ? <div>{sig.registration}</div> : null}
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <footer className="rm-footer">
          {payload.footer?.disclaimer ||
            "This report is based on imaging findings at the time of examination. Clinical correlation is advised."}
        </footer>
      </article>
    </div>
  );
}
