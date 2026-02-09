import React from 'react';
import { FieldDef } from '../../../utils/reporting/v2Builder';
import { theme } from '../../../theme';
import { resolveLabel, formatUnit } from '../../../features/templatesV2/labels/labelResolver';

interface FieldRendererProps {
    field: FieldDef;
    value: any;
    onChange: (value: any) => void;
    disabled?: boolean;
    basicMode?: boolean;
}

export const FieldRenderer: React.FC<FieldRendererProps> = ({
    field,
    value,
    onChange,
    disabled = false,
    basicMode = true
}) => {
    const label = basicMode ? resolveLabel(field.key, field.title) : field.title;
    const unit = formatUnit(field.key);

    const renderRadio = (options: string[]) => (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 4 }}>
            {options.map(opt => (
                <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: disabled ? 'default' : 'pointer', fontSize: 13 }}>
                    <input
                        type="radio"
                        name={field.key}
                        value={opt}
                        checked={value === opt}
                        onChange={() => onChange(opt)}
                        disabled={disabled}
                    />
                    {opt}
                </label>
            ))}
        </div>
    );

    const renderChecklist = (options: string[]) => {
        const selected = Array.isArray(value) ? value : (value ? [value] : []);
        return (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 4 }}>
                {options.map(opt => (
                    <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: disabled ? 'default' : 'pointer', fontSize: 13 }}>
                        <input
                            type="checkbox"
                            checked={selected.includes(opt)}
                            onChange={(e) => {
                                if (e.target.checked) {
                                    onChange([...selected, opt]);
                                } else {
                                    onChange(selected.filter((s: string) => s !== opt));
                                }
                            }}
                            disabled={disabled}
                        />
                        {opt}
                    </label>
                ))}
            </div>
        );
    };

    const renderBooleanToggle = () => (
        <div style={{ display: 'flex', gap: 2, backgroundColor: theme.colors.backgroundGray, padding: 2, borderRadius: 6, width: 'fit-content', marginTop: 4 }}>
            {[
                { label: 'Yes', val: true },
                { label: 'No', val: false }
            ].map(item => (
                <button
                    key={item.label}
                    onClick={() => onChange(item.val)}
                    disabled={disabled}
                    style={{
                        padding: '4px 16px',
                        border: 'none',
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: value === item.val ? 'bold' : 'normal',
                        backgroundColor: value === item.val ? 'white' : 'transparent',
                        boxShadow: value === item.val ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                        cursor: disabled ? 'default' : 'pointer',
                        color: value === item.val ? theme.colors.primary : theme.colors.textPrimary
                    }}
                >
                    {item.label}
                </button>
            ))}
        </div>
    );

    const renderNumeric = () => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
            <div style={{ display: 'flex', alignItems: 'center', border: `1px solid ${theme.colors.border}`, borderRadius: 4, overflow: 'hidden' }}>
                <button
                    onClick={() => onChange((Number(value) || 0) - (field.type === 'integer' ? 1 : 0.1))}
                    disabled={disabled}
                    style={{ padding: '4px 8px', border: 'none', background: '#f5f5f5', cursor: 'pointer' }}
                >-</button>
                <input
                    type="number"
                    value={value ?? ''}
                    onChange={(e) => onChange(e.target.value === '' ? undefined : Number(e.target.value))}
                    disabled={disabled}
                    style={{ width: 60, border: 'none', textAlign: 'center', padding: '4px 0', fontSize: 13 }}
                />
                <button
                    onClick={() => onChange((Number(value) || 0) + (field.type === 'integer' ? 1 : 0.1))}
                    disabled={disabled}
                    style={{ padding: '4px 8px', border: 'none', background: '#f5f5f5', cursor: 'pointer' }}
                >+</button>
            </div>
            {unit && <span style={{ fontSize: 12, color: theme.colors.textSecondary }}>{unit}</span>}
        </div>
    );

    const renderText = (large = false) => (
        <div style={{ marginTop: 4 }}>
            {large ? (
                <textarea
                    value={value ?? ''}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    rows={3}
                    style={{
                        width: '100%',
                        padding: 8,
                        borderRadius: 4,
                        border: `1px solid ${theme.colors.border}`,
                        fontSize: 13,
                        resize: 'vertical'
                    }}
                />
            ) : (
                <input
                    type="text"
                    value={value ?? ''}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    style={{
                        width: '100%',
                        padding: 8,
                        borderRadius: 4,
                        border: `1px solid ${theme.colors.border}`,
                        fontSize: 13
                    }}
                />
            )}
        </div>
    );

    let control;
    if (field.type === 'enum') {
        // Decide between radio and checklist (default to checklist if widget say so, or prefer checklist)
        if (field.widget === 'select') {
            control = (
                <select
                    value={value ?? ''}
                    onChange={e => onChange(e.target.value)}
                    disabled={disabled}
                    style={{ width: '100%', padding: 8, borderRadius: 4, border: `1px solid ${theme.colors.border}`, marginTop: 4 }}
                >
                    <option value="">Select...</option>
                    {field.enumValues?.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                </select>
            );
        } else if (field.widget === 'checkbox') {
            control = renderChecklist(field.enumValues || []);
        } else {
            control = renderRadio(field.enumValues || []);
        }
    } else if (field.type === 'boolean') {
        control = renderBooleanToggle();
    } else if (field.type === 'number' || field.type === 'integer') {
        control = renderNumeric();
    } else if (field.type === 'string' || field.type === 'text') {
        control = renderText(field.type === 'text' || field.widget === 'textarea');
    } else {
        control = <div style={{ color: 'orange', fontSize: 12 }}>Unsupported type: {field.type}</div>;
    }

    return (
        <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 500, fontSize: 14, color: theme.colors.textPrimary }}>{label}</span>
                {!basicMode && <span style={{ fontSize: 10, color: '#999', fontFamily: 'monospace' }}>[{field.key}]</span>}
            </div>
            {control}
        </div>
    );
};
