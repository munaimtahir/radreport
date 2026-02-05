
import React from 'react';
import { FieldDef } from '../../utils/reporting/v2Builder';
import Modal from '../../ui/components/Modal';

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
        <Modal
            isOpen={true}
            title="Resolve Key Conflicts"
            onClose={onCancel}
        >
            <div style={{ display: 'flex', flexDirection: 'column', maxHeight: 600 }}>
                <p style={{ fontSize: 13, color: '#555', marginTop: 0 }}>The following field keys from the block already exist in your template. Please rename them to continue.</p>

                <div style={{ flex: 1, overflowY: 'auto', marginBottom: 20 }}>
                    {conflictingKeys.map(field => (
                        <div key={field.key} style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 12 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                <span style={{ width: 150, fontWeight: 500, fontSize: 13 }}>{field.key}</span>
                                <span style={{ fontSize: 12 }}>→</span>
                                <input
                                    type="text"
                                    value={renameMapping[field.key] || `${field.key}_block`}
                                    onChange={(e) => onRenameChange(field.key, e.target.value)}
                                    placeholder="New key"
                                    style={{ flex: 1, padding: 8, borderRadius: 4, border: errors[field.key] ? '1px solid red' : '1px solid #ccc' }}
                                />
                            </div>
                            {errors[field.key] && <span style={{ color: 'red', fontSize: 11, marginLeft: 175 }}>{errors[field.key]}</span>}
                        </div>
                    ))}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                    <button onClick={onCancel} style={{ padding: '8px 16px', background: 'transparent', border: '1px solid #ccc', borderRadius: 4, cursor: 'pointer' }}>Cancel</button>
                    <button
                        onClick={handleResolve}
                        disabled={Object.keys(errors).length > 0}
                        style={{ padding: '8px 16px', background: Object.keys(errors).length > 0 ? '#ccc' : '#007bff', color: 'white', border: 'none', borderRadius: 4, cursor: Object.keys(errors).length > 0 ? 'not-allowed' : 'pointer' }}
                    >
                        Resolve and Insert
                    </button>
                </div>
            </div>
        </Modal>
    );
}
