
import React, { useMemo, useState } from 'react';
import { normalizeBlockToBuilderFragment } from '../../utils/reporting/v2Builder';
import Modal from '../../ui/components/Modal';

type Block = {
    id: string;
    name: string;
    description: string;
    modality?: string;
    content?: any;
    narrative_defaults?: any;
};

type Props = {
    onClose: () => void;
    onInsert: (block: Block, merge: boolean) => void;
    isSectionSelected: boolean;
    blocks: Block[];
    loading: boolean;
    error: string | null;
    onReload: () => void;
};

export default function InsertBlockModal({ onClose, onInsert, isSectionSelected, blocks, loading, error, onReload }: Props) {
    const [searchTerm, setSearchTerm] = useState('');
    const [modality, setModality] = useState('');
    const [merge, setMerge] = useState(false);
    const [expanded, setExpanded] = useState<Record<string, boolean>>({});

    const filteredBlocks = useMemo(() => {
        return blocks.filter(block =>
            block.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
            (modality ? (block.modality || '').toLowerCase().includes(modality.toLowerCase()) : true)
        );
    }, [blocks, searchTerm, modality]);

    const getSummary = (block: Block) => {
        try {
            const fragment = normalizeBlockToBuilderFragment(block);
            const sectionsCount = fragment.sections.length;
            const fieldsCount = fragment.sections.reduce((acc, s) => acc + s.fields.length, 0);
            return { ok: true, sectionsCount, fieldsCount, fragment };
        } catch (err: any) {
            return { ok: false, error: err.message };
        }
    };

    return (
        <Modal
            isOpen={true}
            title="Insert Block"
            onClose={onClose}
        >
            <div style={{ display: 'flex', flexDirection: 'column', height: '60vh', maxHeight: 600 }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                    <input
                        type="text"
                        placeholder="Search by name..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        style={{ flex: 1, padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
                    />
                    <input
                        type="text"
                        placeholder="Filter by modality"
                        value={modality}
                        onChange={e => setModality(e.target.value)}
                        style={{ width: 160, padding: 8, borderRadius: 4, border: '1px solid #ccc' }}
                    />
                </div>

                <div style={{ marginBottom: 10 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            checked={merge}
                            onChange={() => setMerge(!merge)}
                            disabled={!isSectionSelected}
                        />
                        <span>Merge into selected section {isSectionSelected ? '' : '(Select a section first)'}</span>
                    </label>
                </div>

                {loading ? <p>Loading blocks...</p> : (
                    <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #eee', borderRadius: 4, padding: 4 }}>
                        {error && <p style={{ color: 'red' }}>{error}</p>}
                        {filteredBlocks.map(block => {
                            const summary = getSummary(block);
                            const isExpanded = expanded[block.id];
                            return (
                                <div key={block.id} style={{ border: '1px solid #eee', padding: 10, marginBottom: 8, borderRadius: 6, background: '#f9f9f9' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <div style={{ fontWeight: 600 }}>{block.name} {block.modality && <span style={{ color: '#666', fontSize: 12 }}>({block.modality})</span>}</div>
                                            <div style={{ fontSize: 12, color: '#555' }}>{block.description}</div>
                                            {summary.ok ? (
                                                <div style={{ fontSize: 12, color: '#0b6b37' }}>
                                                    {summary.sectionsCount} sections • {summary.fieldsCount} fields
                                                </div>
                                            ) : (
                                                <div style={{ fontSize: 12, color: '#b00020' }}>Invalid block: {summary.error}</div>
                                            )}
                                        </div>
                                        <div style={{ display: 'flex', gap: 6 }}>
                                            <button
                                                onClick={() => onInsert(block, merge)}
                                                disabled={!summary.ok}
                                                style={{ padding: '6px 12px', background: summary.ok ? '#007bff' : '#ccc', color: 'white', border: 'none', borderRadius: 4, cursor: summary.ok ? 'pointer' : 'not-allowed' }}
                                            >
                                                Insert
                                            </button>
                                            <button
                                                onClick={() => setExpanded(prev => ({ ...prev, [block.id]: !isExpanded }))}
                                                style={{ padding: '6px 12px', background: 'white', border: '1px solid #ccc', borderRadius: 4, cursor: 'pointer' }}
                                            >
                                                {isExpanded ? 'Hide' : 'Preview'}
                                            </button>
                                        </div>
                                    </div>
                                    {isExpanded && summary.ok && summary.fragment && (
                                        <div style={{ marginTop: 8, padding: 8, background: 'white', borderRadius: 4, border: '1px solid #eee' }}>
                                            {summary.fragment.sections.map((sec, idx) => (
                                                <div key={idx} style={{ marginBottom: 6 }}>
                                                    <div style={{ fontWeight: 600, fontSize: 12 }}>{sec.title}</div>
                                                    <div style={{ fontSize: 11, color: '#555' }}>
                                                        {sec.fields.map(f => f.key).join(', ')}
                                                    </div>
                                                </div>
                                            ))}
                                            {summary.fragment.narrative && (summary.fragment.narrative.sections.length > 0 || summary.fragment.narrative.impression_rules.length > 0) && (
                                                <div style={{ fontSize: 11, color: 'blue', marginTop: 4 }}>+ Narrative Rules</div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                        {filteredBlocks.length === 0 && <div style={{ padding: 20, textAlign: 'center', color: '#888' }}>No blocks found.</div>}
                    </div>
                )}

                <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                    <button onClick={onReload} style={{ padding: '8px 16px', background: 'transparent', border: '1px solid #ccc', borderRadius: 4, cursor: 'pointer' }}>Reload</button>
                    <button onClick={onClose} style={{ padding: '8px 16px', background: '#e0e0e0', border: 'none', borderRadius: 4, cursor: 'pointer' }}>Close</button>
                </div>
            </div>
        </Modal>
    );
}
