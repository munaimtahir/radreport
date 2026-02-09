
import React from 'react';
import { theme } from '../../../theme';

export type SectionStatus = 'normal' | 'abnormal' | 'not_assessed';

interface SectionCardProps {
    title: string;
    status: SectionStatus;
    onStatusChange: (status: SectionStatus) => void;
    onEdit: () => void;
    validationError?: string;
    disabled?: boolean;
}

export const SectionCard: React.FC<SectionCardProps> = ({
    title,
    status,
    onStatusChange,
    onEdit,
    validationError,
    disabled
}) => {
    const getStatusStyle = () => {
        switch (status) {
            case 'normal': return { bg: '#e6fffa', border: '#b2f5ea', text: '#234e52', label: 'Normal' };
            case 'abnormal': return { bg: '#fff5f5', border: '#fed7d7', text: '#822727', label: 'Abnormal' };
            case 'not_assessed': return { bg: '#f7fafc', border: '#edf2f7', text: '#4a5568', label: 'Not Assessed' };
        }
    };

    const style = getStatusStyle();

    return (
        <div style={{
            border: `1px solid ${validationError ? theme.colors.danger : style.border}`,
            borderRadius: 12,
            padding: 16,
            backgroundColor: style.bg,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 12,
            transition: 'all 0.2s',
            opacity: disabled ? 0.6 : 1
        }}>
            <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <h3 style={{ margin: 0, fontSize: 16, color: theme.colors.textPrimary }}>{title}</h3>
                    <span style={{
                        fontSize: 10,
                        fontWeight: 'bold',
                        textTransform: 'uppercase',
                        padding: '2px 8px',
                        borderRadius: 999,
                        backgroundColor: style.border,
                        color: style.text
                    }}>{style.label}</span>
                </div>
                {validationError && (
                    <div style={{ color: theme.colors.danger, fontSize: 12, marginTop: 4 }}>
                        {validationError}
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
                <button
                    onClick={() => onStatusChange('normal')}
                    disabled={disabled}
                    style={{
                        padding: '6px 12px',
                        borderRadius: 6,
                        border: '1px solid #cbd5e0',
                        backgroundColor: status === 'normal' ? style.border : 'white',
                        cursor: 'pointer',
                        fontSize: 12
                    }}
                >Mark Normal</button>
                <button
                    onClick={() => onStatusChange('not_assessed')}
                    disabled={disabled}
                    style={{
                        padding: '6px 12px',
                        borderRadius: 6,
                        border: '1px solid #cbd5e0',
                        backgroundColor: status === 'not_assessed' ? style.border : 'white',
                        cursor: 'pointer',
                        fontSize: 12
                    }}
                >Not Assessed</button>
                <button
                    onClick={onEdit}
                    disabled={disabled}
                    style={{
                        padding: '6px 16px',
                        borderRadius: 6,
                        border: 'none',
                        backgroundColor: theme.colors.primary,
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: 'bold'
                    }}
                >Go to Findings</button>
            </div>
        </div>
    );
};
