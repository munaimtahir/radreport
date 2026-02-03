
import React, { useEffect, useState } from 'react';
import { useAuth } from '../../ui/auth';
import { apiGet, apiPost, apiPatch, apiDelete } from '../../ui/api';
import { theme } from '../../theme';
import Button from '../../ui/components/Button';
import ErrorAlert from '../../ui/components/ErrorAlert';
import SuccessAlert from '../../ui/components/SuccessAlert';
import Modal from '../../ui/components/Modal';

interface Block {
    id: string;
    name: string;
    modality: string;
    sections: any; // validation schemas etc
    narrative_defaults: any;
}

const emptyBlock = {
    name: "New Block",
    modality: "USG",
    sections: [],
    narrative_defaults: {}
};

export default function BlockLibrary() {
    const { token } = useAuth();
    const [blocks, setBlocks] = useState<Block[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingBlock, setEditingBlock] = useState<Partial<Block>>(emptyBlock);

    const loadBlocks = async () => {
        if (!token) return;
        setLoading(true);
        try {
            const data = await apiGet('/block-library/', token);
            setBlocks(Array.isArray(data) ? data : data.results || []);
            setLoading(false);
        } catch (e: any) {
            setError(e.message || "Failed to load blocks");
            setLoading(false);
        }
    };

    useEffect(() => {
        loadBlocks();
    }, [token]);

    const handleSave = async () => {
        if (!token) return;
        setError(null);
        try {
            if (editingBlock.id) {
                await apiPatch(`/block-library/${editingBlock.id}/`, token, editingBlock);
                setSuccess("Block updated.");
            } else {
                await apiPost('/block-library/', token, editingBlock);
                setSuccess("Block created.");
            }
            setIsModalOpen(false);
            loadBlocks();
        } catch (e: any) {
            setError(e.message || "Failed to save block");
        }
    };

    const handleDelete = async (id: string) => {
        if (!token || !confirm("Delete this block?")) return;
        try {
            await apiDelete(`/block-library/${id}/`, token);
            setSuccess("Block deleted.");
            loadBlocks();
        } catch (e: any) {
            setError(e.message || "Failed to delete block");
        }
    };

    return (
        <div style={{ padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <h1>Block Library</h1>
                <Button variant="primary" onClick={() => { setEditingBlock(emptyBlock); setIsModalOpen(true); }}>
                    + Create Block
                </Button>
            </div>

            {error && <ErrorAlert message={error} />}
            {success && <SuccessAlert message={success} />}

            <div style={{ backgroundColor: 'white', border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.md }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead style={{ backgroundColor: theme.colors.backgroundGray }}>
                        <tr>
                            <th style={{ padding: 10, textAlign: 'left' }}>Name</th>
                            <th style={{ padding: 10, textAlign: 'left' }}>Modality</th>
                            <th style={{ padding: 10, textAlign: 'right' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {blocks.map(block => (
                            <tr key={block.id} style={{ borderTop: `1px solid ${theme.colors.border}` }}>
                                <td style={{ padding: 10 }}>{block.name}</td>
                                <td style={{ padding: 10 }}>{block.modality}</td>
                                <td style={{ padding: 10, textAlign: 'right' }}>
                                    <Button variant="secondary" onClick={() => { setEditingBlock(block); setIsModalOpen(true); }}>Edit</Button>
                                    <span style={{ marginLeft: 8 }}></span>
                                    <Button variant="primary" onClick={() => handleDelete(block.id)} style={{ backgroundColor: theme.colors.danger, borderColor: theme.colors.danger }}>Delete</Button>
                                </td>
                            </tr>
                        ))}
                        {blocks.length === 0 && (
                            <tr><td colSpan={3} style={{ padding: 20, textAlign: 'center', color: '#888' }}>No blocks found.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>

            {isModalOpen && (
                <Modal
                    isOpen={isModalOpen}
                    title={editingBlock.id ? "Edit Block" : "Create Block"}
                    onClose={() => setIsModalOpen(false)}
                >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <div>
                            <label style={{ display: 'block', fontSize: 12 }}>Name</label>
                            <input
                                value={editingBlock.name}
                                onChange={e => setEditingBlock({ ...editingBlock, name: e.target.value })}
                                style={{ width: '100%', padding: 6 }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: 12 }}>Modality</label>
                            <input
                                value={editingBlock.modality}
                                onChange={e => setEditingBlock({ ...editingBlock, modality: e.target.value })}
                                style={{ width: '100%', padding: 6 }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: 12 }}>Sections (JSON)</label>
                            <textarea
                                value={JSON.stringify(editingBlock.sections, null, 2)}
                                onChange={e => {
                                    try {
                                        const v = JSON.parse(e.target.value);
                                        setEditingBlock({ ...editingBlock, sections: v });
                                    } catch (err) {
                                        // ignore parse error while typing
                                    }
                                }}
                                style={{ width: '100%', height: 100, padding: 6, fontSize: 11, fontFamily: 'monospace' }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: 12 }}>Narrative Defaults (JSON)</label>
                            <textarea
                                value={JSON.stringify(editingBlock.narrative_defaults, null, 2)}
                                onChange={e => {
                                    try {
                                        const v = JSON.parse(e.target.value);
                                        setEditingBlock({ ...editingBlock, narrative_defaults: v });
                                    } catch (err) {
                                    }
                                }}
                                style={{ width: '100%', height: 100, padding: 6, fontSize: 11, fontFamily: 'monospace' }}
                            />
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 10 }}>
                            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                            <Button variant="primary" onClick={handleSave}>Save Block</Button>
                        </div>
                    </div>
                </Modal>
            )}
        </div>
    );
}
