
import React from 'react';
import { FieldDef } from '../../utils/reporting/v2Builder';

type Props = {
    conflictingKeys: FieldDef[];
    renameMapping: Record<string, string>;
    onRenameChange: (oldKey: string, newKey: string) => void;
    onResolve: () => void;
    onCancel: () => void;
};

export default function ConflictResolutionModal({ conflictingKeys, renameMapping, onRenameChange, onResolve, onCancel }: Props) {
    return (
        <div className="modal-backdrop">
            <div className="modal-content">
                <h2>Resolve Key Conflicts</h2>
                <p>The following field keys from the block already exist in your template. Please rename them to continue.</p>
                {conflictingKeys.map(field => (
                    <div key={field.key} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                        <span>{field.key}</span>
                        <input
                            type="text"
                            value={renameMapping[field.key] || ''}
                            onChange={(e) => onRenameChange(field.key, e.target.value)}
                            placeholder="New key"
                        />
                    </div>
                ))}
                <div style={{ marginTop: 20 }}>
                    <button onClick={onResolve}>Resolve and Insert</button>
                    <button onClick={onCancel} style={{ marginLeft: 10 }}>Cancel</button>
                </div>
            </div>
        </div>
    );
}
