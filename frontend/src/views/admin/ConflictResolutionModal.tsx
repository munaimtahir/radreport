
import React from 'react';
import { FieldDef } from '../../utils/reporting/v2Builder';

type Props = {
    conflictingKeys: FieldDef[];
    renameMapping: Record<string, string>;
    onRenameChange: (oldKey: string, newKey: string) => void;
    onResolve: () => void;
    onCancel: () => void;
    existingKeys: string[];
};

export default function ConflictResolutionModal({ conflictingKeys, renameMapping, onRenameChange, onResolve, onCancel, existingKeys }: Props) {
    const [errors, setErrors] = React.useState<Record<string, string>>({});

    const validate = () => {
        const newErrors: Record<string, string> = {};
        const allNewKeys = conflictingKeys.map(field => renameMapping[field.key] || `${field.key}_block`);

        conflictingKeys.forEach(field => {
            const newKey = renameMapping[field.key] || `${field.key}_block`;
            if (existingKeys.includes(newKey)) {
                newErrors[field.key] = "This key already exists in the template.";
            }
            if (allNewKeys.filter(k => k === newKey).length > 1) {
                newErrors[field.key] = "This key is not unique among the new keys.";
            }
        });

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleResolve = () => {
        if (validate()) {
            onResolve();
        }
    };

    return (
        <div className="modal-backdrop">
            <div className="modal-content">
                <h2>Resolve Key Conflicts</h2>
                <p>The following field keys from the block already exist in your template. Please rename them to continue.</p>
                {conflictingKeys.map(field => (
                    <div key={field.key} style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 10 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span>{field.key}</span>
                            <input
                                type="text"
                                value={renameMapping[field.key] || `${field.key}_block`}
                                onChange={(e) => onRenameChange(field.key, e.target.value)}
                                placeholder="New key"
                            />
                        </div>
                        {errors[field.key] && <span style={{ color: 'red', fontSize: 12 }}>{errors[field.key]}</span>}
                    </div>
                ))}
                <div style={{ marginTop: 20 }}>
                    <button onClick={handleResolve} disabled={Object.keys(errors).length > 0}>Resolve and Insert</button>
                    <button onClick={onCancel} style={{ marginLeft: 10 }}>Cancel</button>
                </div>
            </div>
        </div>
    );
}
