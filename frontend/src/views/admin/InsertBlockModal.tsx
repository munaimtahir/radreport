
import React, { useState, useEffect } from 'react';
import { apiGet } from '../../ui/api';
import { useAuth } from '../../ui/auth';

type Block = {
    id: number;
    name: string;
    description: string;
};

type Props = {
    onClose: () => void;
    onInsert: (blockId: number, merge: boolean) => void;
    isSectionSelected: boolean;
};

export default function InsertBlockModal({ onClose, onInsert, isSectionSelected }: Props) {
    const { token } = useAuth();
    const [blocks, setBlocks] = useState<Block[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [merge, setMerge] = useState(false);

    useEffect(() => {
        if (!token) return;
        apiGet('/report-block-library/', token)
            .then(data => {
                setBlocks(data.results);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message || "Failed to load blocks.");
                setLoading(false);
            });
    }, [token]);

    const filteredBlocks = blocks.filter(block =>
        block.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="modal-backdrop">
            <div className="modal-content">
                <h2>Insert Block</h2>
                <input
                    type="text"
                    placeholder="Search by name..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    style={{ marginBottom: 10, width: '100%', padding: 8 }}
                />
                <div style={{ marginBottom: 10 }}>
                    <label>
                        <input
                            type="checkbox"
                            checked={merge}
                            onChange={() => setMerge(!merge)}
                            disabled={!isSectionSelected}
                        />
                        Merge into selected section
                    </label>
                </div>
                {loading && <p>Loading blocks...</p>}
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <ul>
                    {filteredBlocks.map(block => (
                        <li key={block.id}>
                            <strong>{block.name}</strong>: {block.description}
                            <button onClick={() => onInsert(block.id, merge)} style={{ marginLeft: 10 }}>Insert</button>
                        </li>
                    ))}
                </ul>
                <button onClick={onClose}>Close</button>
            </div>
        </div>
    );
}
