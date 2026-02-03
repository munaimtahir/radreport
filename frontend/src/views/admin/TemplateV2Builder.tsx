
import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../ui/auth';
import { apiGet, apiPatch, apiPost } from '../../ui/api';
import { theme } from '../../theme';
import Button from '../../ui/components/Button';
import ErrorAlert from '../../ui/components/ErrorAlert';
import SuccessAlert from '../../ui/components/SuccessAlert';
import {
    BuilderState,
    parseBuilderState,
    buildJsonSchema,
    buildUiSchema,
    buildNarrativeRules,
    SectionDef,
    FieldDef,
    NarrativeLine,
    Condition,
    ConditionOp,
    applyKeyRenames
} from '../../utils/reporting/v2Builder';
import InsertBlockModal from './InsertBlockModal';
import ConflictResolutionModal from './ConflictResolutionModal';

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

const ConditionEditor = ({ condition, onChange }: { condition: Condition, onChange: (c: Condition) => void }) => {
    return (
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            <input
                placeholder="Field"
                value={condition.field}
                onChange={e => onChange({ ...condition, field: e.target.value })}
                style={{ width: 100, padding: 4, fontSize: 11 }}
            />
            <select
                value={condition.op}
                onChange={e => onChange({ ...condition, op: e.target.value as ConditionOp })}
                style={{ width: 80, padding: 4, fontSize: 11 }}
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
            {/* Show value input if not unary operator */}
            {!["is_empty", "is_not_empty"].includes(condition.op) && (
                <input
                    placeholder="Value"
                    value={condition.value}
                    onChange={e => onChange({ ...condition, value: e.target.value })} // Note: simple string for now, need type awareness but skipping for complexity
                    style={{ width: 80, padding: 4, fontSize: 11 }}
                />
            )}
        </div>
    );
}

const NarrativeLineEditor = ({ line, onChange, onDelete }: { line: NarrativeLine, onChange: (l: NarrativeLine) => void, onDelete: () => void }) => {
    if (line.kind === 'text') {
        return (
            <div style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'flex-start' }}>
                <span style={{ fontSize: 10, paddingTop: 6, color: '#888' }}>TXT</span>
                <textarea
                    value={line.template}
                    onChange={e => onChange({ ...line, template: e.target.value })}
                    style={{ flex: 1, padding: 4, fontSize: 12, borderRadius: 4, border: '1px solid #ddd' }}
                    rows={2}
                />
                <button onClick={onDelete} style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'red' }}>×</button>
            </div>
        );
    } else {
        return (
            <div style={{ border: '1px solid #eee', padding: 8, borderRadius: 4, marginBottom: 4, backgroundColor: '#f9f9f9' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ fontSize: 10, fontWeight: 'bold' }}>IF</span>
                        <ConditionEditor condition={line.if} onChange={c => onChange({ ...line, if: c })} />
                    </div>
                    <button onClick={onDelete} style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'red' }}>×</button>
                </div>
                <div style={{ paddingLeft: 12, borderLeft: '2px solid #ddd' }}>
                    <div style={{ fontSize: 10, color: '#666', marginBottom: 2 }}>THEN</div>
                    {/* Recursive limit: 1 level for simplicity? Or simple list? */}
                    {/* Implementing full recursion is complex. Let's assume lines in THEN are just Texts for now or simple lines */}
                    <div style={{ color: 'orange', fontSize: 11 }}>[Nested lines support simplified]</div>
                    {/* For MVP, let's just show JSON for nested lines or a simpler UI */}
                </div>
            </div>
        );
    }
}

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
    const [blockStateToInsert, setBlockStateToInsert] = useState<BuilderState | null>(null);
    const [renameMapping, setRenameMapping] = useState<Record<string, string>>({});
    const [mergeIntoSection, setMergeIntoSection] = useState(false);

    const isFrozen = state?.meta.is_frozen;

    // Load Template
    useEffect(() => {
        if (!token || !id) return;
        setLoading(true);
        apiGet(`/templates-v2/${id}/`, token)
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

            const response = await apiPost(`/templates-v2/`, token, payload);
            navigate(`/settings/templates-v2/${response.id}`);
        } catch (err: any) {
            setError(err.message || "Failed to duplicate template");
        }
    };

    const handleSave = async () => {
        if (!token || !id || !state) return;
        try {
            setSuccess(null);
            setError(null);
            const payload = {
                json_schema: buildJsonSchema(state),
                ui_schema: buildUiSchema(state),
                narrative_rules: buildNarrativeRules(state)
            };
            await apiPatch(`/templates-v2/${id}/`, token, payload);
            setSuccess("Template saved successfully.");
        } catch (err: any) {
            setError(err.message || "Failed to save template");
        }
    };

    const handleInsertBlock = async (blockId: number, merge: boolean) => {
        if (!token || !state) return;

        try {
            const block = await apiGet(`/report-block-library/${blockId}/`, token);
            const blockState = parseBuilderState({}, block.json_schema || {}, block.ui_schema || {}, block.narrative_rules || {});

            const existingKeys = new Set(state.sections.flatMap(s => s.fields.map(f => f.key)));
            const conflictingKeysList = blockState.sections.flatMap(s => s.fields).filter(f => existingKeys.has(f.key));

            if (conflictingKeysList.length > 0) {
                setConflictingKeys(conflictingKeysList);
                setBlockStateToInsert(blockState);
                setMergeIntoSection(merge);
                setShowConflictModal(true);
                setShowInsertBlockModal(false);
            } else {
                if (merge && selectedSectionId) {
                    const blockFields = blockState.sections.flatMap(s => s.fields);
                    updateState(s => {
                        const newSections = [...s.sections];
                        const sectionIndex = newSections.findIndex(s => s.id === selectedSectionId);
                        if (sectionIndex > -1) {
                            newSections[sectionIndex].fields.push(...blockFields);
                        }
                        return { ...s, sections: newSections };
                    });

                } else {
                    // Append sections
                    updateState(s => ({
                        ...s,
                        sections: [...s.sections, ...blockState.sections]
                    }));
                }
                setShowInsertBlockModal(false);
                setSuccess("Block inserted successfully.");
            }

        } catch (err: any) {
            setError(err.message || "Failed to insert block");
        }
    };

    // --- Handlers ---
    const updateState = (updater: (s: BuilderState) => BuilderState) => {
        if (state) setState(updater(state));
    };



    // Section Helpers
    const addSection = () => updateState(s => ({ ...s, sections: [...s.sections, { id: crypto.randomUUID(), title: "New Section", fields: [] }] }));
    const deleteSection = (id: string) => updateState(s => ({ ...s, sections: s.sections.filter(x => x.id !== id) }));

    // Narrative Helper
    const addNarrSection = () => updateState(s => ({
        ...s, narrative: { ...s.narrative, sections: [...s.narrative.sections, { title: "New Section", lines: [] }] }
    }));
    const updateNarrSection = (idx: number, u: any) => updateState(s => {
        const ns = [...s.narrative.sections];
        ns[idx] = { ...ns[idx], ...u };
        return { ...s, narrative: { ...s.narrative, sections: ns } };
    });

    const handleResolveConflicts = () => {
        if (!blockStateToInsert) return;

        const renamedBlockState = { ...blockStateToInsert };

        // Apply renames
        renamedBlockState.sections.forEach(section => {
            section.fields.forEach(field => {
                if (renameMapping[field.key]) {
                    field.key = renameMapping[field.key];
                }
            });
        });

        const renamedNarrative = applyKeyRenames(renamedBlockState.narrative, renameMapping);
        renamedBlockState.narrative = renamedNarrative;

        if (mergeIntoSection && selectedSectionId) {
            const blockFields = renamedBlockState.sections.flatMap(s => s.fields);
            updateState(s => {
                const newSections = [...s.sections];
                const sectionIndex = newSections.findIndex(s => s.id === selectedSectionId);
                if (sectionIndex > -1) {
                    newSections[sectionIndex].fields.push(...blockFields);
                }
                return { ...s, sections: newSections };
            });
        } else {
            // Merge sections
            updateState(s => ({
                ...s,
                sections: [...s.sections, ...renamedBlockState.sections],
                narrative: {
                    ...s.narrative,
                    sections: [...s.narrative.sections, ...renamedBlockState.narrative.sections],
                    computed_fields: [...s.narrative.computed_fields, ...renamedBlockState.narrative.computed_fields],
                    impression_rules: [...s.narrative.impression_rules, ...renamedBlockState.narrative.impression_rules],
                }
            }));
        }

        // Reset state
        setShowConflictModal(false);
        setConflictingKeys([]);
        setBlockStateToInsert(null);
        setRenameMapping({});
        setMergeIntoSection(false);
        setSuccess("Block inserted successfully.");
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
                <div style={{ display: 'flex', gap: 10 }}>
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
                    <Button variant="primary" onClick={handleSave}>Save Changes</Button>
                </div>
            </div>

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
                                    <input value={sec.title} onChange={e => {
                                        const ns = [...state.sections]; ns[idx].title = e.target.value; setState({ ...state, sections: ns });
                                    }} style={{ border: 'none', background: 'transparent', width: '100%', fontWeight: 500 }} onClick={e => e.stopPropagation()} />
                                </div>
                            ))}
                            <Button variant="secondary" onClick={addSection}>+ Add Section</Button>
                            <Button variant="secondary" onClick={() => setShowInsertBlockModal(true)}>Insert Block</Button>
                        </Panel>

                        <Panel title="Fields">
                            {state.sections.find(s => s.id === selectedSectionId)?.fields.map((f, i) => (
                                <div key={i} style={{ border: '1px solid #eee', padding: 8, marginBottom: 8, borderRadius: 4 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <input value={f.title} onChange={e => {
                                            const ns = [...state.sections];
                                            const sec = ns.find(s => s.id === selectedSectionId)!;
                                            sec.fields[i].title = e.target.value;
                                            setState({ ...state, sections: ns });
                                        }} style={{ fontWeight: 'bold', border: 'none', background: 'transparent' }} />
                                        <button onClick={() => {
                                            const ns = [...state.sections];
                                            const sec = ns.find(s => s.id === selectedSectionId)!;
                                            sec.fields = sec.fields.filter((_, idx) => idx !== i);
                                            setState({ ...state, sections: ns });
        
                                        }} style={{ color: 'red', border: 'none', background: 'transparent', cursor: 'pointer' }}>×</button>
                                    </div>
                                    <div style={{ fontSize: 11, color: '#666' }}>Key: {f.key}</div>
                                    {/* Simplified editor */}
                                </div>
                            )) || <div style={{ color: '#888' }}>Select a section</div>}
                            {selectedSectionId && <Button variant="secondary" onClick={() => {
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
                                            <input value={nsec.title} onChange={e => updateNarrSection(idx, { title: e.target.value })}
                                                style={{ fontWeight: 'bold', marginBottom: 10, width: '100%', padding: 4 }} />
                                            <div>
                                                {nsec.lines.map((line, lidx) => (
                                                    <NarrativeLineEditor key={lidx} line={line}
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
                                                    <button onClick={() => {
                                                        const ns = [...state.narrative.sections];
                                                        ns[idx].lines.push({ kind: 'text', template: 'New line' });
                                                        setState({ ...state, narrative: { ...state.narrative, sections: ns } });
                                                    }}>+ Text</button>
                                                    <button onClick={() => {
                                                        const ns = [...state.narrative.sections];
                                                        ns[idx].lines.push({ kind: 'if', if: { field: '', op: 'equals', value: '' }, then: [], else: [] });
                                                        setState({ ...state, narrative: { ...state.narrative, sections: ns } });
                                                    }}>+ Condition</button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    <Button variant="secondary" onClick={addNarrSection}>+ Add Narrative Section</Button>
                                </div>
                            )}
                            {narrativeSubTab === 'computed' && <div>Computed Fields Editor Placeholder (JSON for now)<pre>{JSON.stringify(state.narrative.computed_fields, null, 2)}</pre></div>}
                            {narrativeSubTab === 'impressions' && <div>Impressions Editor Placeholder (JSON for now)<pre>{JSON.stringify(state.narrative.impression_rules, null, 2)}</pre></div>}
                        </Panel>

                        <Panel title="Preview Output">
                            <div style={{ color: '#888' }}>Select sample data to preview...</div>
                        </Panel>
                    </div>
                )}
            </div>

            {showInsertBlockModal && (
                <InsertBlockModal
                    onClose={() => setShowInsertBlockModal(false)}
                    onInsert={handleInsertBlock}
                    isSectionSelected={selectedSectionId !== null}
                />
            )}

            {showConflictModal && (
                <ConflictResolutionModal
                    conflictingKeys={conflictingKeys}
                    renameMapping={renameMapping}
                    onRenameChange={(oldKey, newKey) => setRenameMapping(prev => ({ ...prev, [oldKey]: newKey }))}
                    onResolve={handleResolveConflicts}
                    onCancel={() => setShowConflictModal(false)}
                    existingKeys={state.sections.flatMap(s => s.fields.map(f => f.key))}
                />
            )}
        </div>
    );
}

