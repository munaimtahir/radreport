import React from 'react';
import { FieldDef } from '../../../utils/reporting/v2Builder';
import { FieldRenderer } from './FieldRenderer';

interface PairedFieldGroupProps {
    leftField: FieldDef;
    rightField: FieldDef;
    values: Record<string, any>;
    onChange: (key: string, value: any) => void;
    disabled?: boolean;
    basicMode?: boolean;
}

export const PairedFieldGroup: React.FC<PairedFieldGroupProps> = ({
    leftField,
    rightField,
    values,
    onChange,
    disabled,
    basicMode
}) => {
    return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 16 }}>
            <div>
                <FieldRenderer
                    field={leftField}
                    value={values[leftField.key]}
                    onChange={(val) => onChange(leftField.key, val)}
                    disabled={disabled}
                    basicMode={basicMode}
                />
            </div>
            <div>
                <FieldRenderer
                    field={rightField}
                    value={values[rightField.key]}
                    onChange={(val) => onChange(rightField.key, val)}
                    disabled={disabled}
                    basicMode={basicMode}
                />
            </div>
        </div>
    );
};

export function getPairedFields(fields: FieldDef[]): { pairs: [FieldDef, FieldDef][], singles: FieldDef[] } {
    const pairs: [FieldDef, FieldDef][] = [];
    const singles: FieldDef[] = [];
    const processed = new Set<string>();

    fields.forEach(f => {
        if (processed.has(f.key)) return;

        if (f.key.includes('_l_')) {
            const rightKey = f.key.replace('_l_', '_r_');
            const rightField = fields.find(x => x.key === rightKey);
            if (rightField) {
                pairs.push([f, rightField]);
                processed.add(f.key);
                processed.add(rightKey);
            } else {
                singles.push(f);
                processed.add(f.key);
            }
        } else if (f.key.includes('_r_')) {
            const leftKey = f.key.replace('_r_', '_l_');
            const leftField = fields.find(x => x.key === leftKey);
            if (leftField) {
                // Already handled by the _l_ check or will be if we just let it be
            } else {
                singles.push(f);
                processed.add(f.key);
            }
        } else {
            singles.push(f);
            processed.add(f.key);
        }
    });

    return { pairs, singles };
}
