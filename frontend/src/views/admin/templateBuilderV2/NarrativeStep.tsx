import React, { useState, useEffect } from 'react';
import { theme } from '../../../theme';

interface NarrativeStepProps {
    autoNarrative: string;
    finalNarrative: string;
    onFinalNarrativeChange: (text: string) => void;
    onResetToAuto: () => void;
}

export const NarrativeStep: React.FC<NarrativeStepProps> = ({
    autoNarrative,
    finalNarrative,
    onFinalNarrativeChange,
    onResetToAuto
}) => {
    const [lastActions, setLastActions] = useState<string[]>([]);

    const handleInsertAuto = () => {
        onFinalNarrativeChange(finalNarrative + '\n' + autoNarrative);
        setLastActions([...lastActions, 'insert']);
    };

    const handleUndo = () => {
        // Simple undo placeholder
        setLastActions(lastActions.slice(0, -1));
    };

    return (
        <div>
            <div style={{ marginBottom: 32 }}>
                <h1 style={{ fontSize: 24, marginBottom: 8 }}>Narrative</h1>
                <p style={{ color: theme.colors.textSecondary }}>
                    Compare the automatically generated narrative with your final report text.
                </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                {/* Auto Narrative (Read-only) */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 'bold', fontSize: 13, color: theme.colors.textSecondary }}>Auto Narrative</span>
                        <span style={{ fontSize: 11, backgroundColor: '#ebf8ff', color: '#2b6cb0', padding: '2px 8px', borderRadius: 4 }}>Generated</span>
                    </div>
                    <div style={{
                        flex: 1,
                        minHeight: 300,
                        padding: 16,
                        backgroundColor: '#f8f9fa',
                        border: `1px solid ${theme.colors.border}`,
                        borderRadius: 8,
                        fontSize: 14,
                        lineHeight: 1.6,
                        color: '#444',
                        whiteSpace: 'pre-wrap'
                    }}>
                        {autoNarrative || 'No auto-narrative generated yet. Select findings to see results.'}
                    </div>
                    <button
                        onClick={handleInsertAuto}
                        style={{
                            padding: '8px',
                            borderRadius: 6,
                            border: `1px solid ${theme.colors.primary}`,
                            backgroundColor: 'white',
                            color: theme.colors.primary,
                            cursor: 'pointer',
                            fontSize: 12,
                            fontWeight: 500
                        }}
                    >Insert Auto Narrative ↓</button>
                </div>

                {/* Final Narrative (Editable) */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 'bold', fontSize: 13, color: theme.colors.textPrimary }}>Final Narrative</span>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button onClick={onResetToAuto} style={{ fontSize: 11, background: 'none', border: 'none', color: theme.colors.primary, cursor: 'pointer', textDecoration: 'underline' }}>Reset to Auto</button>
                            <button onClick={handleUndo} disabled={lastActions.length === 0} style={{ fontSize: 11, background: 'none', border: 'none', color: '#999', cursor: 'pointer' }}>Undo</button>
                        </div>
                    </div>
                    <textarea
                        value={finalNarrative}
                        onChange={(e) => onFinalNarrativeChange(e.target.value)}
                        placeholder="Start typing your final report here..."
                        style={{
                            flex: 1,
                            minHeight: 300,
                            padding: 16,
                            backgroundColor: 'white',
                            border: `2px solid ${theme.colors.primary}`,
                            borderRadius: 8,
                            fontSize: 14,
                            lineHeight: 1.6,
                            color: '#1a202c',
                            resize: 'none'
                        }}
                    />
                    <div style={{
                        padding: 12,
                        backgroundColor: '#fffaf0',
                        border: '1px solid #feebc8',
                        borderRadius: 6,
                        fontSize: 12,
                        color: '#744210'
                    }}>
                        <b>Pro Tip:</b> You can edit the final narrative freely before saving. The auto-narrative is a calculated draft based on your findings.
                    </div>
                </div>
            </div>

            {/* Preview Panel */}
            <div style={{ marginTop: 40, border: `1px solid ${theme.colors.border}`, borderRadius: 12, overflow: 'hidden' }}>
                <div style={{ padding: '12px 20px', backgroundColor: '#f1f1f1', borderBottom: `1px solid ${theme.colors.border}`, fontWeight: 'bold', fontSize: 13 }}>
                    Final Report Preview
                </div>
                <div style={{ padding: 40, backgroundColor: 'white', minHeight: 100 }}>
                    <div style={{ maxWidth: 700, margin: '0 auto', fontFamily: 'serif', fontSize: 16, lineHeight: 1.5 }}>
                        <div style={{ borderBottom: '2px solid #333', marginBottom: 20, paddingBottom: 10, textAlign: 'center' }}>
                            <h2 style={{ margin: 0 }}>RADIOLOGY REPORT</h2>
                        </div>
                        <div style={{ whiteSpace: 'pre-wrap' }}>
                            {finalNarrative || 'Report content will appear here...'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
