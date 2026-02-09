import React from 'react';
import { BuilderState } from '../../../utils/reporting/v2Builder';
import { SectionCard, SectionStatus } from './SectionCard';
import { theme } from '../../../theme';

interface SectionsStepProps {
    state: BuilderState;
    sectionStatuses: Record<string, SectionStatus>;
    onStatusChange: (sectionId: string, status: SectionStatus) => void;
    onGoToFindings: (sectionId: string) => void;
    validationErrors: Record<string, string>;
}

export const SectionsStep: React.FC<SectionsStepProps> = ({
    state,
    sectionStatuses,
    onStatusChange,
    onGoToFindings,
    validationErrors
}) => {
    return (
        <div>
            <div style={{ marginBottom: 32 }}>
                <h1 style={{ fontSize: 24, marginBottom: 8 }}>Sections</h1>
                <p style={{ color: theme.colors.textSecondary }}>
                    Manage the main sections of your report. Mark sections as Normal or Not Assessed to quickly fill defaults.
                </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {state.sections.map(section => (
                    <SectionCard
                        key={section.id}
                        title={section.title}
                        status={sectionStatuses[section.id] || 'not_assessed'}
                        onStatusChange={(status) => onStatusChange(section.id, status)}
                        onEdit={() => onGoToFindings(section.id)}
                        validationError={validationErrors[section.id]}
                    />
                ))}
            </div>

            {state.sections.length === 0 && (
                <div style={{
                    padding: 40,
                    textAlign: 'center',
                    border: `2px dashed ${theme.colors.border}`,
                    borderRadius: 12,
                    color: theme.colors.textSecondary
                }}>
                    No sections defined yet. Switch to Advanced Mode to add sections or insert a block.
                </div>
            )}
        </div>
    );
};
