
import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../ui/auth';
import { apiGet, apiPatch, apiPost } from '../../ui/api';
import { theme } from '../../theme';
import Button from '../../ui/components/Button';
import ErrorAlert from '../../ui/components/ErrorAlert';
import SuccessAlert from '../../ui/components/SuccessAlert';
import {
    BuilderState,
    NarrativeState,
    parseBuilderState,
    buildJsonSchema,
    buildUiSchema,
    buildNarrativeRules,
    SectionDef,
    FieldDef,
    NarrativeLine,
    Condition,
    ConditionOp,
    applyKeyRenames,
    normalizeBlockToBuilderFragment,
    BuilderFragment
} from '../../utils/reporting/v2Builder';
import InsertBlockModal from './InsertBlockModal';
import ConflictResolutionModal from './ConflictResolutionModal';

// Redesigned Components
import { TemplateWizard } from './templateBuilderV2/TemplateWizard';
import { SectionsStep } from './templateBuilderV2/SectionsStep';
import { FindingsStep } from './templateBuilderV2/FindingsStep';
import { NarrativeStep } from './templateBuilderV2/NarrativeStep';
import { SectionStatus } from './templateBuilderV2/SectionCard';

// --- Components ---

const Panel = ({ title, children, style, actions }: { title: string, children: React.ReactNode, style?: React.CSSProperties, actions?: React.ReactNode }) => (
    <div style={{
        display: 'flex',
        flexDirection: 'column',
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radius.md,
        backgroundColor: 'white',
        overflow: 'hidden',
        height: '100%',
        ...style
    }}>
        <div style={{
            padding: '8px 12px',
            borderBottom: `1px solid ${theme.colors.border}`,
            backgroundColor: theme.colors.backgroundGray,
            fontWeight: 'bold',
            fontSize: 13,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
        }}>
            <span>{title}</span>
            {actions}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>
            {children}
        </div>
    </div>
);

const ConditionEditor = ({ condition, onChange, disabled }: { condition: Condition, onChange: (c: Condition) => void, disabled?: boolean }) => {
    return (
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            <input
                placeholder="Field"
                value={condition.field}
                onChange={e => onChange({ ...condition, field: e.target.value })}
                style={{ width: 100, padding: 4, fontSize: 11 }}
                disabled={disabled}
            />
            <select
                value={condition.op}
                onChange={e => onChange({ ...condition, op: e.target.value as ConditionOp })}
                style={{ width: 80, padding: 4, fontSize: 11 }}
                disabled={disabled}
            >
                <option value="equals">=</option>
                <option value="not_equals">!=</option>
                <option value="gt">&gt;</option>
                <option value="gte">&gt;=</option>
                <option value="lt">&lt;</option>
                <option value="lte">&lt;=</option>
                <option value="is_empty">Empty</option>
                <option value="is_not_empty">Not Empty</option>
                <option value="in">In</option>
            </select>
            {!["is_empty", "is_not_empty"].includes(condition.op) && (
                <input
                    placeholder="Value"
                    value={condition.value}
                    onChange={e => onChange({ ...condition, value: e.target.value })}
                    style={{ width: 80, padding: 4, fontSize: 11 }}
                    disabled={disabled}
                />
            )}
        </div>
    );
}

const NarrativeLineEditor = ({ line, onChange, onDelete, disabled }: { line: NarrativeLine, onChange: (l: NarrativeLine) => void, onDelete: () => void, disabled?: boolean }) => {
    if (line.kind === 'text') {
        return (
            <div style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'flex-start' }}>
                <span style={{ fontSize: 10, paddingTop: 6, color: '#888' }}>TXT</span>
                <textarea
                    value={line.template}
                    onChange={e => onChange({ ...line, template: e.target.value })}
                    style={{ flex: 1, padding: 4, fontSize: 12, borderRadius: 4, border: '1px solid #ddd' }}
                    rows={2}
                    disabled={disabled}
                />
                <button onClick={onDelete} disabled={disabled} style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'red', opacity: disabled ? 0.4 : 1 }}>×</button>
            </div>
        );
    } else {
        return (
            <div style={{ border: '1px solid #eee', padding: 8, borderRadius: 4, marginBottom: 4, backgroundColor: '#f9f9f9' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ fontSize: 10, fontWeight: 'bold' }}>IF</span>
                        <ConditionEditor condition={line.if} onChange={c => onChange({ ...line, if: c })} disabled={disabled} />
                    </div>
                    <button onClick={onDelete} disabled={disabled} style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'red', opacity: disabled ? 0.4 : 1 }}>×</button>
                </div>
                <div style={{ paddingLeft: 12, borderLeft: '2px solid #ddd' }}>
                    <div style={{ fontSize: 10, color: '#666', marginBottom: 2 }}>THEN</div>
                    <div style={{ color: 'orange', fontSize: 11 }}>[Nested lines support simplified]</div>
                </div>
            </div>
        );
    }
}

export default function TemplateV2Builder() {
    const { id } = useParams<{ id: string }>();
    const { token } = useAuth();
    const navigate = useNavigate();

    // Core Template State
    const [state, setState] = useState<BuilderState | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // UI Redesign State
    const [mode, setMode] = useState<'basic' | 'advanced'>('basic');
    const [wizardStep, setWizardStep] = useState<'sections' | 'findings' | 'narrative'>('sections');
    const [sectionStatuses, setSectionStatuses] = useState<Record<string, SectionStatus>>({});
    const [testValues, setTestValues] = useState<Record<string, any>>({});
    const [autoNarrative, setAutoNarrative] = useState('');
    const [finalNarrative, setFinalNarrative] = useState('');
    const [generatingNarrative, setGeneratingNarrative] = useState(false);

    // Existing UI State
    const [showInsertBlockModal, setShowInsertBlockModal] = useState(false);
    const [activeTab, setActiveTab] = useState<'form' | 'narrative'>('form');
    const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
    const [narrativeSubTab, setNarrativeSubTab] = useState<'computed' | 'sections' | 'impressions'>('sections');

    // Conflict/Block state
    const [showConflictModal, setShowConflictModal] = useState(false);
    const [conflictingKeys, setConflictingKeys] = useState<FieldDef[]>([]);
    const [fragmentToInsert, setFragmentToInsert] = useState<BuilderFragment | null>(null);
    const [renameMapping, setRenameMapping] = useState<Record<string, string>>({});
    const [mergeIntoSection, setMergeIntoSection] = useState(false);
    const [incomingKeys, setIncomingKeys] = useState<string[]>([]);
    const [blockList, setBlockList] = useState<any[]>([]);
    const [blockListLoading, setBlockListLoading] = useState(false);
    const [blockListError, setBlockListError] = useState<string | null>(null);

    const isFrozen = state?.meta.is_frozen;
    const editingDisabled = !!isFrozen;

    const existingFieldKeys = useMemo(() => state ? state.sections.flatMap(s => s.fields.map(f => f.key)) : [], [state]);
    const existingAndIncomingKeys = useMemo(
        () => [...existingFieldKeys, ...incomingKeys.filter(k => !existingFieldKeys.includes(k))],
        [existingFieldKeys]
    );

    // Load Template
    useEffect(() => {
        if (!token || !id) return;
        setLoading(true);
        apiGet(`/reporting/templates-v2/${id}/`, token)
            .then(data => {
                const builderState = parseBuilderState(data, data.json_schema || {}, data.ui_schema || {}, data.narrative_rules || {});
                setState(builderState);
                if (builderState.sections.length > 0) setSelectedSectionId(builderState.sections[0].id);

                // Initialize section statuses
                const statuses: Record<string, SectionStatus> = {};
                builderState.sections.forEach(s => statuses[s.id] = 'not_assessed');
                setSectionStatuses(statuses);

                setLoading(false);
            })
            .catch(err => {
                setError(err.message || "Failed to load template");
                setLoading(false);
            });
    }, [id, token]);

    // Narrative Generation during design
    useEffect(() => {
        if (wizardStep === 'narrative' && state && token && id) {
            handleGenerateNarrative();
        }
    }, [wizardStep, testValues, state]);

    const handleGenerateNarrative = async () => {
        if (!token || !id || !state) return;
        setGeneratingNarrative(true);
        try {
            // We use the new preview endpoint
            const res = await apiPost(`/reporting/templates-v2/${id}/preview-narrative/`, token, { values_json: testValues });
            const narr = res.narrative_json;

            // Format for display
            let text = '';
            if (narr.sections) {
                narr.sections.forEach((s: any) => {
                    text += `${s.title}\n${s.lines.join(' ')}\n\n`;
                });
            }
            if (narr.impression && narr.impression.length > 0) {
                text += `IMPRESSION:\n${narr.impression.join('\n')}`;
            }
            setAutoNarrative(text.trim());
            // If final narrative is empty, initialize it with auto
            if (!finalNarrative) setFinalNarrative(text.trim());
        } catch (err) {
            console.error("Narrative preview failed", err);
        } finally {
            setGeneratingNarrative(false);
        }
    };

    const loadBlocks = useCallback(() => {
        if (!token || blockList.length > 0 || blockListLoading) return;
        setBlockListLoading(true);
        apiGet('/reporting/block-library/', token)
            .then(data => {
                const results = Array.isArray(data) ? data : data.results || [];
                setBlockList(results);
                setBlockListLoading(false);
            })
            .catch(err => {
                setBlockListError(err.message || "Failed to load block library");
                setBlockListLoading(false);
            });
    }, [token, blockList.length, blockListLoading]);

    const handleSave = async () => {
        if (!token || !id || !state) return;
        if (editingDisabled) return;
        try {
            setSuccess(null);
            setError(null);
            const payload = {
                json_schema: buildJsonSchema(state),
                ui_schema: buildUiSchema(state),
                narrative_rules: buildNarrativeRules(state)
            };
            await apiPatch(`/reporting/templates-v2/${id}/`, token, payload);
            setSuccess("Template saved successfully.");
        } catch (err: any) {
            setError(err.message || "Failed to save template");
        }
    };

    const handleDuplicate = async () => {
        if (!token || !state) return;
        try {
            const newVersion = state.meta.version + 1;
            const newCode = `${state.meta.code.split('_v')[0]}_v${newVersion}`;
            const payload = {
                name: state.meta.name,
                code: newCode,
                modality: state.meta.modality,
                version: newVersion,
                is_frozen: false,
                status: 'draft',
                json_schema: buildJsonSchema(state),
                ui_schema: buildUiSchema(state),
                narrative_rules: buildNarrativeRules(state),
            };
            const response = await apiPost(`/reporting/templates-v2/`, token, payload);
            navigate(`/settings/templates-v2/${response.id}/builder`);
        } catch (err: any) {
            setError(err.message || "Failed to duplicate template");
        }
    };

    const handleInsertBlock = async (block: any, merge: boolean) => {
        if (!token || !state || editingDisabled) return;
        try {
            const fragment = normalizeBlockToBuilderFragment(block);
            const incomingFields = fragment.sections.flatMap(s => s.fields);
            const incomingKeysLocal = incomingFields.map(f => f.key);
            const existingKeysSet = new Set(existingFieldKeys);
            const conflicts = incomingFields.filter(f => existingKeysSet.has(f.key));

            if (conflicts.length > 0) {
                const suggestedMap: Record<string, string> = {};
                const allKeys = new Set([...existingFieldKeys, ...incomingKeysLocal]);
                conflicts.forEach(f => {
                    let suggestion = `${f.key}_block`;
                    let counter = 1;
                    while (allKeys.has(suggestion)) {
                        suggestion = `${f.key}_${counter}`;
                        counter += 1;
                    }
                    suggestedMap[f.key] = suggestion;
                });
                setConflictingKeys(conflicts);
                setFragmentToInsert(fragment);
                setMergeIntoSection(merge);
                setRenameMapping(suggestedMap);
                setIncomingKeys(incomingKeysLocal);
                setShowConflictModal(true);
                setShowInsertBlockModal(false);
                return;
            }

            applyFragment(fragment, merge);
            setShowInsertBlockModal(false);
        } catch (err: any) {
            setError(err.message || "Failed to insert block");
        }
    };

    const applyFragment = (fragment: BuilderFragment, merge: boolean) => {
        if (!state) return;
        if (merge && selectedSectionId) {
            const blockFields = fragment.sections.flatMap(s => s.fields);
            setState(s => {
                if (!s) return s;
                const newSections = [...s.sections];
                const sectionIndex = newSections.findIndex(sec => sec.id === selectedSectionId);
                if (sectionIndex > -1) {
                    newSections[sectionIndex].fields = [...newSections[sectionIndex].fields, ...blockFields];
                }
                return {
                    ...s,
                    sections: newSections,
                    narrative: fragment.narrative ? mergeNarrative(s.narrative, fragment.narrative) : s.narrative
                };
            });
        } else {
            setState(s => {
                if (!s) return s;
                return {
                    ...s,
                    sections: [...s.sections, ...fragment.sections],
                    narrative: fragment.narrative ? mergeNarrative(s.narrative, fragment.narrative) : s.narrative
                };
            });
        }
    };

    const mergeNarrative = (base: NarrativeState, incoming: NarrativeState): NarrativeState => {
        return {
            computed_fields: [...(base?.computed_fields || []), ...(incoming?.computed_fields || [])],
            sections: [...(base?.sections || []), ...(incoming?.sections || [])],
            impression_rules: [...(base?.impression_rules || []), ...(incoming?.impression_rules || [])]
        };
    };

    const handleResolveConflicts = () => {
        if (!fragmentToInsert) return;
        const renamedFragment: BuilderFragment = {
            sections: fragmentToInsert.sections.map(sec => ({
                ...sec,
                fields: sec.fields.map(f => ({
                    ...f,
                    key: renameMapping[f.key] || f.key
                }))
            })),
            narrative: fragmentToInsert.narrative ? applyKeyRenames(fragmentToInsert.narrative, renameMapping) : fragmentToInsert.narrative
        };
        applyFragment(renamedFragment, mergeIntoSection);
        setShowConflictModal(false);
        setConflictingKeys([]);
        setFragmentToInsert(null);
    };

    if (loading) return <div style={{ padding: 20 }}>Loading builder...</div>;
    if (!state) return <div style={{ padding: 20 }}>Failed to load state.</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 60px)' }}>
            {/* Redesigned Header */}
            <div style={{
                padding: '10px 20px',
                borderBottom: `1px solid ${theme.colors.border}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                backgroundColor: 'white'
            }}>
                <div>
                    <nav style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
                        <span style={{ cursor: 'pointer' }} onClick={() => navigate('/settings/templates-v2')}>Templates</span> / {state.meta.code}
                    </nav>
                    <h1 style={{ fontSize: 18, margin: 0 }}>{state.meta.name}</h1>
                </div>

                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                    {/* Mode Toggle */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, backgroundColor: '#f0f0f0', padding: '4px 8px', borderRadius: 20 }}>
                        <span style={{ opacity: mode === 'basic' ? 1 : 0.5, fontWeight: mode === 'basic' ? 'bold' : 'normal' }}>Basic</span>
                        <div
                            onClick={() => setMode(mode === 'basic' ? 'advanced' : 'basic')}
                            style={{
                                width: 36, height: 20, borderRadius: 10, backgroundColor: mode === 'advanced' ? theme.colors.primary : '#ccc',
                                position: 'relative', cursor: 'pointer', transition: 'all 0.2s'
                            }}
                        >
                            <div style={{
                                width: 14, height: 14, borderRadius: '50%', backgroundColor: 'white', position: 'absolute',
                                top: 3, left: mode === 'advanced' ? 19 : 3, transition: 'all 0.2s'
                            }} />
                        </div>
                        <span style={{ opacity: mode === 'advanced' ? 1 : 0.5, fontWeight: mode === 'advanced' ? 'bold' : 'normal' }}>Advanced</span>
                    </div>

                    <div style={{ display: 'flex', gap: 8 }}>
                        {isFrozen && (
                            <Button variant="secondary" onClick={handleDuplicate}>Duplicate</Button>
                        )}
                        <Button variant="primary" onClick={handleSave} disabled={editingDisabled}>Save Changes</Button>
                    </div>
                </div>
            </div>

            {isFrozen && (
                <div style={{ backgroundColor: '#fff3cd', borderBottom: '1px solid #ffeeba', padding: '6px 20px', color: '#856404', fontSize: 12, fontWeight: 600 }}>
                    Frozen template — editing disabled.
                </div>
            )}

            {error && <div style={{ padding: '0 20px' }}><ErrorAlert message={error} /></div>}
            {success && <div style={{ padding: '0 20px' }}><SuccessAlert message={success} /></div>}

            <div style={{ flex: 1, overflow: 'hidden' }}>
                {mode === 'basic' ? (
                    <TemplateWizard
                        currentStep={wizardStep}
                        onStepChange={(s) => setWizardStep(s)}
                    >
                        {wizardStep === 'sections' && (
                            <SectionsStep
                                state={state}
                                sectionStatuses={sectionStatuses}
                                onStatusChange={(id, stat) => {
                                    setSectionStatuses({ ...sectionStatuses, [id]: stat });
                                    if (stat === 'normal') {
                                        // Clear all non-default values in this section's fields
                                        const section = state.sections.find(s => s.id === id);
                                        if (section) {
                                            const newValues = { ...testValues };
                                            section.fields.forEach(f => {
                                                delete newValues[f.key];
                                            });
                                            setTestValues(newValues);
                                        }
                                    }
                                }}
                                onGoToFindings={(id) => {
                                    setSelectedSectionId(id);
                                    setWizardStep('findings');
                                }}
                                validationErrors={(() => {
                                    const errors: Record<string, string> = {};
                                    state.sections.forEach(sec => {
                                        if (sectionStatuses[sec.id] === 'abnormal') {
                                            const hasValue = sec.fields.some(f => testValues[f.key] !== undefined && testValues[f.key] !== '');
                                            if (!hasValue) {
                                                errors[sec.id] = "Section marked as Abnormal but no findings selected.";
                                            }
                                        }
                                    });
                                    return errors;
                                })()}
                            />
                        )}
                        {wizardStep === 'findings' && selectedSectionId && (
                            <FindingsStep
                                section={state.sections.find(s => s.id === selectedSectionId)!}
                                values={testValues}
                                onChange={(k, v) => setTestValues({ ...testValues, [k]: v })}
                                onBack={() => setWizardStep('sections')}
                                basicMode={true}
                            />
                        )}
                        {wizardStep === 'narrative' && (
                            <NarrativeStep
                                autoNarrative={autoNarrative}
                                finalNarrative={finalNarrative}
                                onFinalNarrativeChange={setFinalNarrative}
                                onResetToAuto={() => setFinalNarrative(autoNarrative)}
                            />
                        )}
                    </TemplateWizard>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: '250px 400px 1fr', gap: 20, height: '100%', padding: 20 }}>
                        {/* Advanced Mode: Restore previous UI logic but keep improved styling */}
                        <Panel title="Sections" actions={!editingDisabled && <Button variant="secondary" onClick={() => setState(s => s ? ({ ...s, sections: [...s.sections, { id: crypto.randomUUID(), title: "New Section", fields: [] }] }) : s)}>+ Add</Button>}>
                            {state.sections.map((sec, idx) => (
                                <div key={sec.id} onClick={() => setSelectedSectionId(sec.id)}
                                    style={{
                                        padding: 10, border: `1px solid ${sec.id === selectedSectionId ? theme.colors.primary : theme.colors.border}`, marginBottom: 8,
                                        borderRadius: theme.radius.sm, backgroundColor: sec.id === selectedSectionId ? '#f0f9ff' : 'white', cursor: 'pointer', display: 'flex', gap: 8
                                    }}>
                                    <input value={sec.title} disabled={editingDisabled} onChange={e => {
                                        const ns = [...state.sections]; ns[idx].title = e.target.value; setState({ ...state, sections: ns });
                                    }} style={{ border: 'none', background: 'transparent', width: '100%', fontWeight: 500 }} onClick={e => e.stopPropagation()} />
                                </div>
                            ))}
                        </Panel>

                        <Panel title="Fields" actions={selectedSectionId && !editingDisabled && <Button variant="secondary" onClick={() => {
                            const ns = [...state.sections];
                            const sec = ns.find(s => s.id === selectedSectionId)!;
                            sec.fields.push({ key: `new_field_${Date.now()}`, title: "New Field", type: "string" });
                            setState({ ...state, sections: ns });
                        }}>+ Add Field</Button>}>
                            {state.sections.find(s => s.id === selectedSectionId)?.fields.map((f, i) => (
                                <div key={i} style={{ border: '1px solid #eee', padding: 8, marginBottom: 8, borderRadius: 4 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <input value={f.title} disabled={editingDisabled} onChange={e => {
                                            const ns = [...state.sections];
                                            const sec = ns.find(s => s.id === selectedSectionId)!;
                                            sec.fields[i].title = e.target.value;
                                            setState({ ...state, sections: ns });
                                        }} style={{ fontWeight: 'bold', border: 'none', background: 'transparent' }} />
                                        <button disabled={editingDisabled} onClick={() => {
                                            const ns = [...state.sections];
                                            const sec = ns.find(s => s.id === selectedSectionId)!;
                                            sec.fields = sec.fields.filter((_, idx) => idx !== i);
                                            setState({ ...state, sections: ns });
                                        }} style={{ color: 'red', border: 'none', background: 'transparent', cursor: 'pointer' }}>×</button>
                                    </div>
                                    <div style={{ fontSize: 11, color: '#666' }}>Key: <span style={{ fontFamily: 'monospace' }}>{f.key}</span></div>
                                </div>
                            )) || <div style={{ color: '#888' }}>Select a section</div>}
                        </Panel>

                        <Panel title="Raw Schema (Live)">
                            <pre style={{ fontSize: 10, overflow: 'auto' }}>{JSON.stringify(buildJsonSchema(state), null, 2)}</pre>
                        </Panel>
                    </div>
                )}
            </div>

            {showInsertBlockModal && (
                <InsertBlockModal
                    onClose={() => setShowInsertBlockModal(false)}
                    onInsert={handleInsertBlock}
                    isSectionSelected={selectedSectionId !== null}
                    blocks={blockList}
                    loading={blockListLoading}
                    error={blockListError}
                    onReload={loadBlocks}
                />
            )}

            {showConflictModal && (
                <ConflictResolutionModal
                    conflictingKeys={conflictingKeys}
                    renameMapping={renameMapping}
                    onRenameChange={(oldKey, newKey) => setRenameMapping(prev => ({ ...prev, [oldKey]: newKey }))}
                    onResolve={handleResolveConflicts}
                    onCancel={() => setShowConflictModal(false)}
                    existingKeys={existingAndIncomingKeys}
                />
            )}
        </div>
    );
}
