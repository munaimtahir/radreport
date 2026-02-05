
import React from 'react';
import { ImpressionRule } from '../../utils/reporting/v2Builder';
import Button from '../../ui/components/Button';
import { theme } from '../../theme';
import { ConditionEditor } from './NarrativeComponents';

type Props = {
    rules: ImpressionRule[];
    onChange: (rules: ImpressionRule[]) => void;
    disabled?: boolean;
};

export default function ImpressionRuleEditor({ rules, onChange, disabled }: Props) {
    const handleChange = (idx: number, rule: Partial<ImpressionRule>) => {
        const newRules = [...rules];
        newRules[idx] = { ...newRules[idx], ...rule };
        // Optional: sort by priority? Let's leave it manual for now to avoid jumping rows
        onChange(newRules);
    };

    const handleDelete = (idx: number) => {
        const newRules = rules.filter((_, i) => i !== idx);
        onChange(newRules);
    };

    const handleAdd = () => {
        const maxPriority = rules.reduce((max, r) => Math.max(max, r.priority || 0), 0);
        onChange([...rules, {
            priority: maxPriority + 1,
            when: { field: '', op: 'equals', value: '' },
            text: '',
            continue: false
        }]);
    };

    const sortedRules = [...rules].sort((a, b) => a.priority - b.priority);
    // But working with indices in sorted array maps back to original array?
    // It's safer to just iterate the passed array if we are editing in place,
    // or we sort them for display but we need to track index.
    // Let's just render in order given (users might want to group them logically despite priority, 
    // although execution is by priority). 
    // Actually, execution IS by priority.
    // Let's just render as is for now.

    return (
        <div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {rules.map((rule, idx) => (
                    <div key={idx} style={{
                        border: `1px solid ${theme.colors.border}`,
                        borderRadius: theme.radius.sm,
                        padding: 10,
                        backgroundColor: 'white',
                    }}>
                        <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 8 }}>
                            <div style={{ width: 60 }}>
                                <label style={{ display: 'block', fontSize: 10, marginBottom: 2, color: theme.colors.textSecondary }}>Priority</label>
                                <input
                                    type="number"
                                    value={rule.priority}
                                    onChange={e => handleChange(idx, { priority: parseInt(e.target.value) || 0 })}
                                    disabled={disabled}
                                    style={{ width: '100%', padding: 4, borderRadius: 3, border: '1px solid #ccc' }}
                                />
                            </div>
                            <div style={{ flex: 1 }}>
                                <label style={{ display: 'block', fontSize: 10, marginBottom: 2, color: theme.colors.textSecondary }}>Condition</label>
                                <ConditionEditor
                                    condition={rule.when}
                                    onChange={c => handleChange(idx, { when: c })}
                                    disabled={disabled}
                                />
                            </div>
                            <div style={{ width: 80, display: 'flex', alignItems: 'center', paddingTop: 14 }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, cursor: 'pointer' }}>
                                    <input
                                        type="checkbox"
                                        checked={rule.continue}
                                        onChange={e => handleChange(idx, { continue: e.target.checked })}
                                        disabled={disabled}
                                    />
                                    Continue
                                </label>
                            </div>
                            <button
                                onClick={() => handleDelete(idx)}
                                disabled={disabled}
                                style={{ border: 'none', background: 'transparent', color: theme.colors.danger, cursor: disabled ? 'not-allowed' : 'pointer' }}
                            >
                                &times;
                            </button>
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: 10, marginBottom: 2, color: theme.colors.textSecondary }}>Impression Text</label>
                            <textarea
                                value={rule.text}
                                onChange={e => handleChange(idx, { text: e.target.value })}
                                disabled={disabled}
                                rows={2}
                                style={{ width: '100%', padding: 6, borderRadius: 3, border: '1px solid #ccc', fontSize: 12, fontFamily: 'inherit' }}
                            />
                        </div>
                    </div>
                ))}

                {rules.length === 0 && (
                    <div style={{ textAlign: 'center', padding: 20, color: theme.colors.textSecondary, border: '1px dashed #ccc', borderRadius: theme.radius.sm }}>
                        No impression rules defined.
                    </div>
                )}
            </div>
            <div style={{ marginTop: 12 }}>
                <Button variant="secondary" onClick={handleAdd} disabled={disabled}>+ Add Impression Rule</Button>
            </div>
        </div>
    );
}
