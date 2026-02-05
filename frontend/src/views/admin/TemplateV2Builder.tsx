
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
import ComputedFieldEditor from './ComputedFieldEditor';
import ImpressionRuleEditor from './ImpressionRuleEditor';
import { NarrativeLineEditor } from './NarrativeComponents';

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



export default function TemplateV2Builder() {
    const { id } = useParams<{ id: string }>();
    const { token } = useAuth();
    const navigate = useNavigate();

    const [state, setState] = useState<BuilderState | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const [showInsertBlockModal, setShowInsertBlockModal] = useState(false);
    const [activeTab, setActiveTab] = useState<'form' | 'narrative'>('form');
    const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
    const [narrativeSubTab, setNarrativeSubTab] = useState<'computed' | 'sections' | 'impressions'>('sections');
    const [selectedNarrSectionIdx, setSelectedNarrSectionIdx] = useState<number>(0);

    const [showConflictModal, setShowConflictModal] = useState(false);
    const [conflictingKeys, setConflictingKeys] = useState<FieldDef[]>([]);
    const [fragmentToInsert, setFragmentToInsert] = useState<BuilderFragment | null>(null);
    const [renameMapping, setRenameMapping] = useState<Record<string, string>>({});
    const [mergeIntoSection, setMergeIntoSection] = useState(false);
    const [incomingKeys, setIncomingKeys] = useState<string[]>([]);

    const [blockList, setBlockList] = useState<any[]>([]);
    const [blockListLoading, setBlockListLoading] = useState(false);
    const [blockListError, setBlockListError] = useState<string | null>(null);

    // Preview States
    const [previewData, setPreviewData] = useState('{\n  \n}');
    const [previewResult, setPreviewResult] = useState<any>(null);
    const [previewLoading, setPreviewLoading] = useState(false);

    const isFrozen = state?.meta.is_frozen;
    const editingDisabled = !!isFrozen;

    const existingFieldKeys = useMemo(() => state ? state.sections.flatMap(s => s.fields.map(f => f.key)) : [], [state]);
    const existingAndIncomingKeys = useMemo(
        () => [...existingFieldKeys, ...incomingKeys.filter(k => !existingFieldKeys.includes(k))],
        [existingFieldKeys, incomingKeys]
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
                setLoading(false);
            })
            .catch(err => {
                setError(err.message || "Failed to load template");
                setLoading(false);
            });
    }, [id, token]);

    // Load block library lazily and cache to avoid refetch storms
    const loadBlocks = useCallback(() => {
        if (!token || blockList.length > 0 || blockListLoading) return;
        setBlockListLoading(true);
        setBlockListError(null);
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

    const handleDuplicate = async () => {
        if (!token || !state) return;

        try {
            const newVersion = state.meta.version + 1;
            const newCode = `${state.meta.code.split('_v')[0]}_v${newVersion}`;

            const newTemplate = {
                ...state,
                meta: {
                    ...state.meta,
                    version: newVersion,
                    code: newCode,
                    is_frozen: false,
                    status: 'draft',
                },
            };

            const payload = {
                name: newTemplate.meta.name,
                code: newTemplate.meta.code,
                modality: newTemplate.meta.modality,
                version: newTemplate.meta.version,
                is_frozen: newTemplate.meta.is_frozen,
                status: newTemplate.meta.status,
                json_schema: buildJsonSchema(newTemplate),
                ui_schema: buildUiSchema(newTemplate),
                narrative_rules: buildNarrativeRules(newTemplate),
            };

            const response = await apiPost(`/reporting/templates-v2/`, token, payload);
            navigate(`/settings/templates-v2/${response.id}/builder`);
        } catch (err: any) {
            setError(err.message || "Failed to duplicate template");
        }
    };

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

    const handleInsertBlock = async (block: any, merge: boolean) => {
        if (!token || !state || editingDisabled) return;
        if (merge && !selectedSectionId) {
            setError("Select a section before merging a block into it.");
            return;
        }

        try {
            const fragment = normalizeBlockToBuilderFragment(block);

            const incomingFields = fragment.sections.flatMap(s => s.fields);
            const incomingKeysLocal = incomingFields.map(f => f.key);
            const existingKeys = new Set(existingFieldKeys);
            const conflicts = incomingFields.filter(f => existingKeys.has(f.key));

            if (conflicts.length > 0) {
                const suggestedMap: Record<string, string> = {};
                const allKeys = new Set([...existingKeys, ...incomingKeys]);
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
            setSuccess(fragment.narrative ? "Block inserted successfully. Narrative defaults applied." : "Block inserted successfully.");
        } catch (err: any) {
            setError(err.message || "Failed to insert block");
        }
    };

    const applyFragment = (fragment: BuilderFragment, merge: boolean) => {
        if (!state) return;
        if (merge && selectedSectionId) {
            const blockFields = fragment.sections.flatMap(s => s.fields);
            updateState(s => {
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
            updateState(s => ({
                ...s,
                sections: [...s.sections, ...fragment.sections],
                narrative: fragment.narrative ? mergeNarrative(s.narrative, fragment.narrative) : s.narrative
            }));
        }
    };

    const mergeNarrative = (base: NarrativeState, incoming: NarrativeState): NarrativeState => {
        return {
            computed_fields: [...(base?.computed_fields || []), ...(incoming?.computed_fields || [])],
            sections: [...(base?.sections || []), ...(incoming?.sections || [])],
            impression_rules: [...(base?.impression_rules || []), ...(incoming?.impression_rules || [])]
        };
    };

    const handlePreviewNarrative = async () => {
        if (!token || !state) return;
        try {
            const values = JSON.parse(previewData);
            setPreviewLoading(true);
            const payload = {
                json_schema: buildJsonSchema(state),
                narrative_rules: buildNarrativeRules(state),
                values
            };
            const res = await apiPost('/reporting/templates-v2/preview-narrative/', token, payload);
            setPreviewResult(res);
            setPreviewLoading(false);
        } catch (err: any) {
            setPreviewResult({ error: err.message || "Failed to generate preview" });
            setPreviewLoading(false);
        }
    };

    // --- Handlers ---
    const updateState = (updater: (s: BuilderState) => BuilderState) => {
        if (state) setState(updater(state));
    };



    // Section Helpers
    const addSection = () => {
        if (editingDisabled) return;
        updateState(s => ({ ...s, sections: [...s.sections, { id: crypto.randomUUID(), title: "New Section", fields: [] }] }));
    };
    const deleteSection = (id: string) => {
        if (editingDisabled) return;
        updateState(s => ({ ...s, sections: s.sections.filter(x => x.id !== id) }));
    };

    // Narrative Helper
    const addNarrSection = () => {
        if (editingDisabled) return;
        updateState(s => ({
            ...s, narrative: { ...s.narrative, sections: [...s.narrative.sections, { title: "New Section", lines: [] }] }
        }));
    };
    const updateNarrSection = (idx: number, u: any) => updateState(s => {
        const ns = [...s.narrative.sections];
        ns[idx] = { ...ns[idx], ...u };
        return { ...s, narrative: { ...s.narrative, sections: ns } };
    });

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

        // Reset state
        setShowConflictModal(false);
        setConflictingKeys([]);
        setFragmentToInsert(null);
        setRenameMapping({});
        setMergeIntoSection(false);
        setSuccess(renamedFragment.narrative ? "Block inserted successfully. Narrative defaults applied." : "Block inserted successfully.");
    };

    if (loading) return <div style={{ padding: 20 }}>Loading builder...</div>;
    if (!state) return <div style={{ padding: 20 }}>Failed to load state.</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 60px)' }}>
            {/* Header */}
            <div style={{ padding: '10px 20px', borderBottom: `1px solid ${theme.colors.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'white' }}>
                <div>
                    <nav style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
                        <span style={{ cursor: 'pointer' }} onClick={() => navigate('/settings/templates-v2')}>Templates</span> / {state.meta.code}
                    </nav>
                    <h1 style={{ fontSize: 18, margin: 0 }}>Template Builder: {state.meta.name}</h1>
                </div>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <div style={{ display: 'flex', backgroundColor: theme.colors.backgroundGray, borderRadius: theme.radius.md, padding: 2 }}>
                        {(['form', 'narrative'] as const).map(tab => (
                            <button key={tab}
                                style={{
                                    padding: '6px 12px', border: 'none', backgroundColor: activeTab === tab ? 'white' : 'transparent',
                                    borderRadius: theme.radius.sm, cursor: 'pointer', fontWeight: activeTab === tab ? 'bold' : 'normal',
                                    boxShadow: activeTab === tab ? '0 1px 2px rgba(0,0,0,0.1)' : 'none', textTransform: 'capitalize'
                                }}
                                onClick={() => setActiveTab(tab)}
                            >{tab === 'form' ? 'Form Design' : 'Narrative Logic'}</button>
                        ))}
                    </div>
                    {activeTab === 'form' && !editingDisabled && (
                        <Button variant="secondary" onClick={() => { setShowInsertBlockModal(true); loadBlocks(); }}>Insert Block</Button>
                    )}
                    {isFrozen && (
                        <Button variant="secondary" onClick={handleDuplicate}>Duplicate as New Version</Button>
                    )}
                    <Button variant="primary" onClick={handleSave} disabled={editingDisabled}>Save Changes</Button>
                </div>
            </div>

            {isFrozen && (
                <div style={{ backgroundColor: '#fff3cd', borderBottom: '1px solid #ffeeba', padding: '10px 20px', color: '#856404', fontWeight: 600 }}>
                    Frozen template — editing disabled.
                </div>
            )}

            {error && <div style={{ padding: '0 20px' }}><ErrorAlert message={error} /></div>}
            {success && <div style={{ padding: '0 20px' }}><SuccessAlert message={success} /></div>}

            <div style={{ flex: 1, padding: 20, overflow: 'hidden' }}>
                {activeTab === 'form' ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '250px 400px 1fr', gap: 20, height: '100%' }}>
                        <Panel title="Sections">
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
                            <Button variant="secondary" onClick={addSection} disabled={editingDisabled}>+ Add Section</Button>
                        </Panel>

                        <Panel title="Fields">
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

                                        }} style={{ color: 'red', border: 'none', background: 'transparent', cursor: 'pointer', opacity: editingDisabled ? 0.4 : 1 }}>×</button>
                                    </div>
                                    <div style={{ fontSize: 11, color: '#666' }}>Key: {f.key}</div>
                                    {/* Simplified editor */}
                                </div>
                            )) || <div style={{ color: '#888' }}>Select a section</div>}
                            {selectedSectionId && <Button variant="secondary" disabled={editingDisabled} onClick={() => {
                                const ns = [...state.sections];
                                const sec = ns.find(s => s.id === selectedSectionId)!;
                                sec.fields.push({ key: `new_field_${Date.now()}`, title: "New Field", type: "string" });
                                setState({ ...state, sections: ns });
                            }}>+ Add Field</Button>}
                        </Panel>

                        <Panel title="Preview (Live)">
                            <pre style={{ fontSize: 10 }}>{JSON.stringify(buildJsonSchema(state), null, 2)}</pre>
                        </Panel>
                    </div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr 300px', gap: 20, height: '100%' }}>
                        <Panel title="Narrative">
                            {(['sections', 'computed', 'impressions'] as const).map(sub => (
                                <div key={sub} onClick={() => setNarrativeSubTab(sub)}
                                    style={{ padding: 10, cursor: 'pointer', fontWeight: narrativeSubTab === sub ? 'bold' : 'normal', backgroundColor: narrativeSubTab === sub ? '#eee' : 'white' }}>
                                    {sub.charAt(0).toUpperCase() + sub.slice(1)}
                                </div>
                            ))}
                        </Panel>

                        <Panel title={narrativeSubTab === 'sections' ? "Narrative Sections" : "Configuration"}>
                            {narrativeSubTab === 'sections' && (
                                <div>
                                    {state.narrative.sections.map((nsec, idx) => (
                                        <div key={idx} style={{ marginBottom: 20, border: '1px solid #ddd', padding: 10 }}>
                                            <input value={nsec.title} disabled={editingDisabled} onChange={e => updateNarrSection(idx, { title: e.target.value })}
                                                style={{ fontWeight: 'bold', marginBottom: 10, width: '100%', padding: 4 }} />
                                            <div>
                                                {nsec.lines.map((line, lidx) => (
                                                    <NarrativeLineEditor key={lidx} line={line} disabled={editingDisabled}
                                                        onChange={nl => {
                                                            const ns = [...state.narrative.sections];
                                                            ns[idx].lines[lidx] = nl;
                                                            setState({ ...state, narrative: { ...state.narrative, sections: ns } });
                                                        }}
                                                        onDelete={() => {
                                                            const ns = [...state.narrative.sections];
                                                            ns[idx].lines = ns[idx].lines.filter((_, i) => i !== lidx);
                                                            setState({ ...state, narrative: { ...state.narrative, sections: ns } });
                                                        }}
                                                    />
                                                ))}
                                                <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                                                    <button disabled={editingDisabled} onClick={() => {
                                                        const ns = [...state.narrative.sections];
                                                        ns[idx].lines.push({ kind: 'text', template: 'New line' });
                                                        setState({ ...state, narrative: { ...state.narrative, sections: ns } });
                                                    }}>+ Text</button>
                                                    <button disabled={editingDisabled} onClick={() => {
                                                        const ns = [...state.narrative.sections];
                                                        ns[idx].lines.push({ kind: 'if', if: { field: '', op: 'equals', value: '' }, then: [], else: [] });
                                                        setState({ ...state, narrative: { ...state.narrative, sections: ns } });
                                                    }}>+ Condition</button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    <Button variant="secondary" onClick={addNarrSection} disabled={editingDisabled}>+ Add Narrative Section</Button>
                                </div>
                            )}
                            {narrativeSubTab === 'computed' && (
                                <ComputedFieldEditor
                                    fields={state.narrative.computed_fields}
                                    onChange={fields => setState({ ...state, narrative: { ...state.narrative, computed_fields: fields } })}
                                    disabled={editingDisabled}
                                />
                            )}
                            {narrativeSubTab === 'impressions' && (
                                <ImpressionRuleEditor
                                    rules={state.narrative.impression_rules}
                                    onChange={rules => setState({ ...state, narrative: { ...state.narrative, impression_rules: rules } })}
                                    disabled={editingDisabled}
                                />
                            )}
                        </Panel>

                        <Panel title="Preview Output">
                            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 10 }}>
                                <div style={{ height: '40%', display: 'flex', flexDirection: 'column' }}>
                                    <label style={{ fontSize: 11, fontWeight: 'bold' }}>Input Values (JSON)</label>
                                    <textarea
                                        value={previewData}
                                        onChange={e => setPreviewData(e.target.value)}
                                        style={{ flex: 1, fontFamily: 'monospace', fontSize: 11, padding: 6, border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.sm }}
                                    />
                                    <Button variant="secondary" onClick={handlePreviewNarrative} disabled={previewLoading} style={{ marginTop: 4 }}>
                                        {previewLoading ? 'Generating...' : 'Generate Preview'}
                                    </Button>
                                </div>
                                <div style={{ flex: 1, borderTop: '1px solid #eee', paddingTop: 8, overflowY: 'auto' }}>
                                    <label style={{ fontSize: 11, fontWeight: 'bold' }}>Generated Narrative</label>
                                    {previewResult?.error ? (
                                        <div style={{ color: 'red', fontSize: 12 }}>{previewResult.error}</div>
                                    ) : previewResult ? (
                                        <div>
                                            {previewResult.sections?.map((sec: any, i: number) => (
                                                <div key={i} style={{ marginBottom: 10 }}>
                                                    <div style={{ fontWeight: 600, fontSize: 13 }}>{sec.title}</div>
                                                    <div style={{ whiteSpace: 'pre-wrap', fontSize: 12, lineHeight: 1.4 }}>
                                                        {sec.lines.join('\n')}
                                                    </div>
                                                </div>
                                            ))}
                                            {previewResult.impression && previewResult.impression.length > 0 && (
                                                <div style={{ marginTop: 10, borderTop: '1px dashed #ccc', paddingTop: 6 }}>
                                                    <div style={{ fontWeight: 600, fontSize: 13 }}>Impression</div>
                                                    <ul style={{ paddingLeft: 20, margin: '4px 0', fontSize: 12 }}>
                                                        {previewResult.impression.map((imp: string, i: number) => (
                                                            <li key={i}>{imp}</li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                            {previewResult.computed && (
                                                <div style={{ marginTop: 10, fontSize: 10, color: '#666' }}>
                                                    <strong>Computed: </strong> {JSON.stringify(previewResult.computed)}
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div style={{ color: '#888', fontStyle: 'italic', fontSize: 12 }}>
                                            No result generated yet.
                                        </div>
                                    )}
                                </div>
                            </div>
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
