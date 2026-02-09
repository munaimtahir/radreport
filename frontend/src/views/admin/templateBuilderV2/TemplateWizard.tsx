import React from 'react';
import { theme } from '../../../theme';

interface TemplateWizardProps {
    currentStep: 'sections' | 'findings' | 'narrative';
    onStepChange: (step: 'sections' | 'findings' | 'narrative') => void;
    children: React.ReactNode;
}

export const TemplateWizard: React.FC<TemplateWizardProps> = ({
    currentStep,
    onStepChange,
    children
}) => {
    const steps = [
        { id: 'sections', label: '1. Sections' },
        { id: 'findings', label: '2. Findings' },
        { id: 'narrative', label: '3. Narrative' }
    ] as const;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: '#fcfcfc' }}>
            {/* Stepper Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                padding: '20px 0',
                borderBottom: `1px solid ${theme.colors.border}`,
                backgroundColor: 'white'
            }}>
                <div style={{ display: 'flex', gap: 40 }}>
                    {steps.map(step => (
                        <div
                            key={step.id}
                            onClick={() => onStepChange(step.id)}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                cursor: 'pointer',
                                opacity: currentStep === step.id ? 1 : 0.5,
                                transition: 'opacity 0.2s'
                            }}
                        >
                            <div style={{
                                width: 24,
                                height: 24,
                                borderRadius: '50%',
                                backgroundColor: currentStep === step.id ? theme.colors.primary : '#ccc',
                                color: 'white',
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                fontSize: 12,
                                fontWeight: 'bold'
                            }}>
                                {steps.indexOf(step) + 1}
                            </div>
                            <span style={{
                                fontWeight: currentStep === step.id ? 'bold' : 'normal',
                                color: currentStep === step.id ? theme.colors.primary : theme.colors.textSecondary
                            }}>
                                {step.label.split('. ')[1]}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Content Area */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
                <div style={{ maxWidth: 900, margin: '0 auto' }}>
                    {children}
                </div>
            </div>

            {/* Footer Navigation */}
            <div style={{
                padding: '20px 40px',
                borderTop: `1px solid ${theme.colors.border}`,
                backgroundColor: 'white',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <button
                    disabled={currentStep === 'sections'}
                    onClick={() => onStepChange(currentStep === 'narrative' ? 'findings' : 'sections')}
                    style={{
                        padding: '10px 24px',
                        borderRadius: 8,
                        border: `1px solid ${theme.colors.border}`,
                        backgroundColor: 'white',
                        cursor: currentStep === 'sections' ? 'default' : 'pointer',
                        opacity: currentStep === 'sections' ? 0.5 : 1
                    }}
                >Back</button>

                <div style={{ fontSize: 13, color: theme.colors.textTertiary }}>
                    Auto-saving draft...
                </div>

                <button
                    disabled={currentStep === 'narrative'}
                    onClick={() => onStepChange(currentStep === 'sections' ? 'findings' : 'narrative')}
                    style={{
                        padding: '10px 32px',
                        borderRadius: 8,
                        border: 'none',
                        backgroundColor: theme.colors.primary,
                        color: 'white',
                        fontWeight: 'bold',
                        cursor: currentStep === 'narrative' ? 'default' : 'pointer',
                        opacity: currentStep === 'narrative' ? 0.5 : 1
                    }}
                >Next Step</button>
            </div>
        </div>
    );
};
