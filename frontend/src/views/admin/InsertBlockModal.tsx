
import React, { useMemo, useState } from 'react';
import { normalizeBlockToBuilderFragment } from '../../utils/reporting/v2Builder';

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
        <div className="modal-backdrop">
            <div className="modal-content">
                <h2>Insert Block</h2>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                    <input
                        type="text"
                        placeholder="Search by name..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        style={{ flex: 1, padding: 8 }}
                    />
                    <input
                        type="text"
                        placeholder="Filter by modality"
                        value={modality}
                        onChange={e => setModality(e.target.value)}
                        style={{ width: 160, padding: 8 }}
                    />
                </div>
                <input
                    type="checkbox"
                    checked={merge}
                    onChange={() => setMerge(!merge)}
                    disabled={!isSectionSelected}
                />{" "}
                <label>
                    <label>
                        Merge into selected section
                    </label>
                </label>
                {!isSectionSelected && <div style={{ color: '#b26a00', fontSize: 12, marginTop: 4 }}>Select a section to enable merge mode.</div>}
                <div style={{ margin: '10px 0' }}>
                    <button onClick={onReload} style={{ marginRight: 8 }}>Reload</button>
                    <button onClick={onClose}>Close</button>
                </div>
                {loading && <p>Loading blocks...</p>}
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <div style={{ maxHeight: 360, overflowY: 'auto' }}>
                    {filteredBlocks.map(block => {
                        const summary = getSummary(block);
                        const isExpanded = expanded[block.id];
                        return (
                            <div key={block.id} style={{ border: '1px solid #ddd', padding: 10, marginBottom: 8, borderRadius: 6, background: 'white' }}>
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
                                        {summary.ok && <button onClick={() => onInsert(block, merge)} disabled={!summary.ok}>Insert</button>}
                                        <button onClick={() => setExpanded(prev => ({ ...prev, [block.id]: !isExpanded }))}>{isExpanded ? 'Hide' : 'Preview'}</button>
                                    </div>
                                </div>
                                {isExpanded && summary.ok && summary.fragment && (
                                    <div style={{ marginTop: 8, padding: 8, background: '#f9f9f9', borderRadius: 4 }}>
                                        {summary.fragment.sections.map((sec, idx) => (
                                            <div key={idx} style={{ marginBottom: 6 }}>
                                                <div style={{ fontWeight: 600 }}>{sec.title}</div>
                                                <div style={{ fontSize: 12, color: '#555' }}>{sec.fields.length} fields</div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                    {filteredBlocks.length === 0 && !loading && <div style={{ color: '#888' }}>No blocks found.</div>}
                </div>
            </div>
        </div>
    );
}
