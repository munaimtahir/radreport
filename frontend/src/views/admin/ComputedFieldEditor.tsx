
import React from 'react';
import { ComputedField } from '../../utils/reporting/v2Builder';
import Button from '../../ui/components/Button';
import { theme } from '../../theme';

type Props = {
    fields: ComputedField[];
    onChange: (fields: ComputedField[]) => void;
    disabled?: boolean;
};

export default function ComputedFieldEditor({ fields, onChange, disabled }: Props) {
    const handleChange = (idx: number, field: Partial<ComputedField>) => {
        const newFields = [...fields];
        newFields[idx] = { ...newFields[idx], ...field };
        onChange(newFields);
    };

    const handleDelete = (idx: number) => {
        const newFields = fields.filter((_, i) => i !== idx);
        onChange(newFields);
    };

    const handleAdd = () => {
        onChange([...fields, { key: '', expr: '' }]);
    };

    return (
        <div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {fields.map((field, idx) => (
                    <div key={idx} style={{
                        border: `1px solid ${theme.colors.border}`,
                        borderRadius: theme.radius.sm,
                        padding: 10,
                        backgroundColor: 'white',
                        display: 'flex',
                        gap: 10,
                        alignItems: 'flex-start'
                    }}>
                        <div style={{ flex: 1 }}>
                            <label style={{ display: 'block', fontSize: 11, marginBottom: 4, color: theme.colors.textSecondary }}>Target Key</label>
                            <input
                                value={field.key}
                                onChange={e => handleChange(idx, { key: e.target.value })}
                                placeholder="e.g. liver_volume"
                                disabled={disabled}
                                style={{ width: '100%', padding: 6, borderRadius: 4, border: '1px solid #ccc' }}
                            />
                        </div>
                        <div style={{ flex: 2 }}>
                            <label style={{ display: 'block', fontSize: 11, marginBottom: 4, color: theme.colors.textSecondary }}>Expression</label>
                            <input
                                value={field.expr}
                                onChange={e => handleChange(idx, { expr: e.target.value })}
                                placeholder="e.g. l * w * h * 0.52"
                                disabled={disabled}
                                style={{ width: '100%', padding: 6, borderRadius: 4, border: '1px solid #ccc', fontFamily: 'monospace' }}
                            />
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', paddingTop: 18 }}>
                            <button
                                onClick={() => handleDelete(idx)}
                                disabled={disabled}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: theme.colors.danger,
                                    cursor: disabled ? 'not-allowed' : 'pointer',
                                    padding: 4
                                }}
                            >
                                <span style={{ fontSize: 18 }}>&times;</span>
                            </button>
                        </div>
                    </div>
                ))}

                {fields.length === 0 && (
                    <div style={{ textAlign: 'center', padding: 20, color: theme.colors.textSecondary, border: '1px dashed #ccc', borderRadius: theme.radius.sm }}>
                        No computed fields defined.
                    </div>
                )}
            </div>

            <div style={{ marginTop: 12 }}>
                <Button variant="secondary" onClick={handleAdd} disabled={disabled}>+ Add Computed Field</Button>
            </div>
        </div>
    );
}
