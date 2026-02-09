import React from 'react';
import { BuilderState, SectionDef } from '../../../utils/reporting/v2Builder';
import { getPairedFields, PairedFieldGroup } from './PairedFieldGroup';
import { FieldRenderer } from './FieldRenderer';
import { theme } from '../../../theme';

interface FindingsStepProps {
    section: SectionDef;
    values: Record<string, any>;
    onChange: (key: string, value: any) => void;
    onBack: () => void;
    basicMode: boolean;
}

export const FindingsStep: React.FC<FindingsStepProps> = ({
    section,
    values,
    onChange,
    onBack,
    basicMode
}) => {
    const { pairs, singles } = getPairedFields(section.fields);

    return (
        <div>
            <div style={{ marginBottom: 32, display: 'flex', alignItems: 'center', gap: 16 }}>
                <button
                    onClick={onBack}
                    style={{
                        border: 'none',
                        background: 'none',
                        cursor: 'pointer',
                        fontSize: 20,
                        color: theme.colors.primary,
                        display: 'flex',
                        alignItems: 'center'
                    }}
                >←</button>
                <div>
                    <h1 style={{ fontSize: 24, margin: 0 }}>{section.title}</h1>
                    <p style={{ color: theme.colors.textSecondary, margin: '4px 0 0 0' }}>
                        Configure findings for this section. Side-by-side layout is automatically applied for paired organs.
                    </p>
                </div>
            </div>

            <div style={{ backgroundColor: 'white', border: `1px solid ${theme.colors.border}`, borderRadius: 12, padding: 32 }}>
                {/* Paired Fields First */}
                {pairs.map(([left, right]) => (
                    <PairedFieldGroup
                        key={`${left.key}-${right.key}`}
                        leftField={left}
                        rightField={right}
                        values={values}
                        onChange={onChange}
                        basicMode={basicMode}
                    />
                ))}

                {/* Single Fields */}
                {singles.map(field => (
                    <FieldRenderer
                        key={field.key}
                        field={field}
                        value={values[field.key]}
                        onChange={(val) => onChange(field.key, val)}
                        basicMode={basicMode}
                    />
                ))}

                {section.fields.length === 0 && (
                    <div style={{ textAlign: 'center', color: theme.colors.textSecondary, padding: 20 }}>
                        No fields defined in this section.
                    </div>
                )}
            </div>

            <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end' }}>
                <button
                    onClick={() => {
                        // "Normal Pack" logic: reset fields to defaults or clear them
                        section.fields.forEach(f => {
                            onChange(f.key, f.default || undefined);
                        });
                    }}
                    style={{
                        padding: '8px 16px',
                        borderRadius: 6,
                        border: `1px solid ${theme.colors.primary}`,
                        color: theme.colors.primary,
                        backgroundColor: 'white',
                        cursor: 'pointer',
                        fontSize: 13,
                        fontWeight: 500
                    }}
                >Reset to Normals</button>
            </div>
        </div>
    );
};
