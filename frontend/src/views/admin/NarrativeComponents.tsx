
import React from 'react';
import { Condition, ConditionOp, NarrativeLine } from '../../utils/reporting/v2Builder';

export const ConditionEditor = ({ condition, onChange, disabled }: { condition: Condition, onChange: (c: Condition) => void, disabled?: boolean }) => {
    return (
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            <input
                placeholder="Field"
                value={condition.field}
                onChange={e => onChange({ ...condition, field: e.target.value })}
                style={{ width: 100, padding: 4, fontSize: 11, borderRadius: 3, border: '1px solid #ccc' }}
                disabled={disabled}
            />
            <select
                value={condition.op}
                onChange={e => onChange({ ...condition, op: e.target.value as ConditionOp })}
                style={{ width: 80, padding: 4, fontSize: 11, borderRadius: 3, border: '1px solid #ccc' }}
                disabled={disabled}
            >
                <option value="equals">=</option>
                <option value="not_equals">!=</option>
                <option value="gt">&gt;</option>
                <option value="gte">&gt;=</option>
                <option value="lt">&lt;</option>
                <option value="lte">&lt;=</option>
                <option value="is_empty">Empty</option>
                <option value="is_not_empty">Not Empty</option>
                <option value="in">In</option>
            </select>
            {!["is_empty", "is_not_empty"].includes(condition.op) && (
                <input
                    placeholder="Value"
                    value={condition.value}
                    onChange={e => onChange({ ...condition, value: e.target.value })}
                    style={{ width: 80, padding: 4, fontSize: 11, borderRadius: 3, border: '1px solid #ccc' }}
                    disabled={disabled}
                />
            )}
        </div>
    );
}

export const NarrativeLineEditor = ({ line, onChange, onDelete, disabled }: { line: NarrativeLine, onChange: (l: NarrativeLine) => void, onDelete: () => void, disabled?: boolean }) => {
    if (line.kind === 'text') {
        return (
            <div style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'flex-start' }}>
                <span style={{ fontSize: 10, paddingTop: 6, color: '#888', minWidth: 20 }}>TXT</span>
                <textarea
                    value={line.template}
                    onChange={e => onChange({ ...line, template: e.target.value })}
                    style={{ flex: 1, padding: 6, fontSize: 12, borderRadius: 4, border: '1px solid #ddd', fontFamily: 'inherit' }}
                    rows={2}
                    disabled={disabled}
                />
                <button onClick={onDelete} disabled={disabled} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#d32f2f', opacity: disabled ? 0.4 : 1, padding: 4 }}>×</button>
            </div>
        );
    } else {
        return (
            <div style={{ border: '1px solid #eee', padding: '8px 8px 8px 12px', borderRadius: 4, marginBottom: 4, backgroundColor: '#f9f9f9' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 10, fontWeight: 'bold', color: '#1976d2' }}>IF</span>
                        <ConditionEditor condition={line.if} onChange={c => onChange({ ...line, if: c })} disabled={disabled} />
                    </div>
                    <button onClick={onDelete} disabled={disabled} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#d32f2f', opacity: disabled ? 0.4 : 1 }}>×</button>
                </div>
                <div style={{ paddingLeft: 12, borderLeft: '2px solid #ddd', marginLeft: 4 }}>
                    <div style={{ fontSize: 10, color: '#666', marginBottom: 4 }}>THEN</div>
                    <div style={{ color: '#e65100', fontSize: 11, fontStyle: 'italic' }}>
                        {/* Nested lines simplified due to recursion limits in this editor */}
                        {Array.isArray(line.then) && line.then.length > 0
                            ? `${line.then.length} lines (Click to edit - coming soon)`
                            : "(Empty block)"}
                    </div>
                </div>
            </div>
        );
    }
}
