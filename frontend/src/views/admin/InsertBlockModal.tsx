
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
    onInsert: (blockId: number) => void;
};

export default function InsertBlockModal({ onClose, onInsert }: Props) {
    const { token } = useAuth();
    const [blocks, setBlocks] = useState<Block[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

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

    return (
        <div className="modal-backdrop">
            <div className="modal-content">
                <h2>Insert Block</h2>
                {loading && <p>Loading blocks...</p>}
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <ul>
                    {blocks.map(block => (
                        <li key={block.id}>
                            <strong>{block.name}</strong>: {block.description}
                            <button onClick={() => onInsert(block.id)} style={{ marginLeft: 10 }}>Insert</button>
                        </li>
                    ))}
                </ul>
                <button onClick={onClose}>Close</button>
            </div>
        </div>
    );
}
