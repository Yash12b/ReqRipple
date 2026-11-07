import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../lib/api';
import {
  Layers,
  ArrowLeft,
  Sparkles,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  GitFork,
  HelpCircle,
  FileDiff,
  Download,
  Info,
} from 'lucide-react';

export const ImpactAnalysisView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [cr, setCr] = useState<any>(null);
  const [diffs, setDiffs] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [selectedPathItem, setSelectedPathItem] = useState<any>(null);
  const [selectedScoreItem, setSelectedScoreItem] = useState<any>(null);

  // Decision Modal
  const [decisionModal, setDecisionModal] = useState<{ open: boolean; type: string }>({
    open: false,
    type: 'APPROVE',
  });
  const [decisionRationale, setDecisionRationale] = useState('');

  // Disposition Modal
  const [dispositionModal, setDispositionModal] = useState<{ open: boolean; item: any }>({
    open: false,
    item: null,
  });
  const [dispositionChoice, setDispositionChoice] = useState('UPDATE_REQUIRED');
  const [dispositionRationale, setDispositionRationale] = useState('');

  const loadData = () => {
    if (!id) return;
    setLoading(true);
    api.getChangeRequest(id)
      .then((data) => {
        setCr(data);
        setDiffs(data.diffs || []);
        if (data.latest_analysis) {
          setAnalysis(data.latest_analysis);
        }
      })
      .catch((err) => console.error('Failed to load change request', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleSimulate = async () => {
    if (!id) return;
    setSimulating(true);
    try {
      const sim = await api.simulateChange(id);
      setAnalysis(sim);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const handleAnalyse = async () => {
    if (!id) return;
    setAnalyzing(true);
    try {
      const res = await api.analyseChange(id);
      setAnalysis(res);
      loadData();
    } catch (err: any) {
      alert(`Analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDecisionSubmit = async () => {
    if (!id) return;
    try {
      if (decisionModal.type === 'APPROVE') {
        await api.approveChange(id, { decision: 'APPROVE', rationale: decisionRationale });
      } else if (decisionModal.type === 'REJECT') {
        await api.rejectChange(id, { decision: 'REJECT', rationale: decisionRationale });
      } else if (decisionModal.type === 'DEFER') {
        await api.deferChange(id, { decision: 'DEFER', rationale: decisionRationale });
      }
      setDecisionModal({ open: false, type: 'APPROVE' });
      setDecisionRationale('');
      loadData();
    } catch (err: any) {
      alert(`Decision error: ${err.message}`);
    }
  };

  const handleDispositionSubmit = async () => {
    if (!dispositionModal.item) return;
    try {
      await api.updateDisposition(dispositionModal.item.id, {
        disposition: dispositionChoice,
        review_rationale: dispositionRationale,
      });
      setDispositionModal({ open: false, item: null });
      setDispositionRationale('');
      loadData();
    } catch (err: any) {
      alert(`Disposition error: ${err.message}`);
    }
  };

  const handleExportCsv = async () => {
    if (!analysis?.id) return;
    try {
      const blob = await api.exportCsv(analysis.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `impact_report_${cr.title.slice(0, 15)}.csv`;
      a.click();
    } catch (err: any) {
      alert(`CSV export failed: ${err.message}`);
    }
  };

  if (loading || !cr) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 text-xs">
        Loading impact workspace...
      </div>
    );
  }

  const results = analysis?.results || [];
  const summary = analysis?.summary_json || analysis?.summary || {};
  const isPreview = analysis?.is_preview;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Bar Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/change-requests"
          className="text-xs font-semibold text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Change Requests</span>
        </Link>
        {analysis?.id && (
          <button
            onClick={handleExportCsv}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-700/80 transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV Report</span>
          </button>
        )}
      </div>

      {/* Change Proposal Header Card */}
      <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-brand-950 text-brand-300 border border-brand-800">
                CR-{cr.id.slice(0, 8)}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                Status: {cr.status}
              </span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                cr.urgency === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                cr.urgency === 'HIGH' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                'bg-slate-800 text-slate-300'
              }`}>
                Urgency: {cr.urgency}
              </span>
            </div>
            <h1 className="text-xl font-bold text-white mt-2">{cr.title}</h1>
            <p className="text-xs text-slate-300 mt-1">Reason: {cr.reason}</p>
          </div>

          {/* Action Trigger Buttons */}
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={handleSimulate}
              disabled={simulating}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold rounded-xl text-slate-200 transition flex items-center gap-1.5 shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>{simulating ? 'Simulating...' : 'What-If Simulation'}</span>
            </button>

            <button
              onClick={handleAnalyse}
              disabled={analyzing}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-brand-600/25 transition flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{analyzing ? 'Computing...' : 'Run Impact Analysis'}</span>
            </button>
          </div>
        </div>

        {/* Before / After Field Differences Table */}
        {diffs.length > 0 && (
          <div className="pt-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 font-mono">
              <FileDiff className="w-4 h-4 text-brand-400" />
              <span>Requirement Field Diffs</span>
            </div>
            <div className="bg-slate-950 rounded-xl border border-slate-800/80 overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/60 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-3">Field</th>
                    <th className="py-2 px-3">Change Category</th>
                    <th className="py-2 px-3">Approved Value (Baseline)</th>
                    <th className="py-2 px-3">Proposed Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {diffs.map((d: any) => (
                    <tr key={d.id || d.field_name} className="hover:bg-slate-900/30">
                      <td className="py-2.5 px-3 font-mono font-semibold text-brand-300">{d.field_name}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-300 border border-slate-800">
                          {d.change_category}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 max-w-xs break-words">{d.old_value || 'None'}</td>
                      <td className="py-2.5 px-3 text-emerald-300 font-medium max-w-xs break-words">{d.new_value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Approver Decision Controls */}
        {cr.status !== 'APPROVED' && cr.status !== 'CLOSED' && (
          <div className="flex items-center justify-between pt-3 border-t border-slate-800">
            <div className="text-xs text-slate-400">
              {analysis
                ? 'Review impact results below before submitting approval decision.'
                : 'Run impact analysis to evaluate downstream risk before deciding.'}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setDecisionModal({ open: true, type: 'REJECT' })}
                className="px-3 py-1.5 bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/80 text-rose-300 text-xs font-semibold rounded-xl transition flex items-center gap-1.5"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject</span>
              </button>
              <button
                onClick={() => setDecisionModal({ open: true, type: 'DEFER' })}
                className="px-3 py-1.5 bg-amber-950/40 hover:bg-amber-900/60 border border-amber-800/80 text-amber-300 text-xs font-semibold rounded-xl transition flex items-center gap-1.5"
              >
                <Clock className="w-3.5 h-3.5" />
                <span>Defer</span>
              </button>
              <button
                onClick={() => setDecisionModal({ open: true, type: 'APPROVE' })}
                disabled={!analysis || isPreview}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-600/25 transition flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Approve Change</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Analysis Results Section */}
      {analysis && (
        <div className="space-y-6">
          {/* Simulation / Snapshot Banner */}
          <div className={`p-4 rounded-xl border flex items-center justify-between text-xs ${
            isPreview
              ? 'bg-amber-950/40 border-amber-800/80 text-amber-200'
              : 'bg-brand-950/40 border-brand-800/80 text-brand-200'
          }`}>
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 shrink-0" />
              <span>
                {isPreview
                  ? 'WHAT-IF SIMULATION PREVIEW: No permanent database baseline or remediation actions have been created.'
                  : `SAVED IMPACT SNAPSHOT: Derived from graph state hash ${summary.graph_snapshot_hash || 'latest'}.`}
              </span>
            </div>
            <div className="font-mono text-[11px] text-slate-400">Algorithm v1.0.0</div>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="text-xs text-slate-400">Total Affected Artifacts</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {results.length}
              </div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="text-xs text-slate-400">Critical / High Priority</div>
              <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                {(summary.priority_counts?.CRITICAL || 0) + (summary.priority_counts?.HIGH || 0)}
              </div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="text-xs text-slate-400">Est. Remediation Effort</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {summary.total_estimated_effort_hours || 0} hrs
              </div>
            </div>

            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
              <div className="text-xs text-slate-400">Proximity Max Depth</div>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                {results.length > 0 ? Math.max(...results.map((r: any) => r.shortest_distance)) : 0} hops
              </div>
            </div>
          </div>

          {/* Impacted Artifacts Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand-400" />
                <span>Impacted Engineering Artifacts (Ordered by Review Priority)</span>
              </h3>
              <div className="text-xs text-slate-400 font-mono">
                Click any score or path to inspect explainable evidence
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase font-mono text-slate-400 border-b border-slate-800 bg-slate-950/40">
                  <tr>
                    <th className="py-3 px-4">Artifact</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Distance</th>
                    <th className="py-3 px-4">Path Strength</th>
                    <th className="py-3 px-4">Priority Band</th>
                    <th className="py-3 px-4">Review Score</th>
                    <th className="py-3 px-4">Disposition</th>
                    <th className="py-3 px-4 text-right">Explanation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {results.map((r: any) => (
                    <tr key={r.artifact_id || r.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4">
                        <div className="font-mono font-bold text-xs text-brand-400">{r.artifact_display_id}</div>
                        <div className="text-xs font-medium text-slate-200 mt-0.5">{r.artifact_title}</div>
                      </td>
                      <td className="py-3 px-4 text-xs font-mono text-slate-400">{r.artifact_type}</td>
                      <td className="py-3 px-4 text-xs font-mono text-slate-300">
                        {r.shortest_distance} {r.shortest_distance === 1 ? 'hop (Direct)' : 'hops (Indirect)'}
                      </td>
                      <td className="py-3 px-4 text-xs font-mono text-slate-300">
                        {Math.round(r.path_strength * 100)}%
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          r.priority_band === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                          r.priority_band === 'HIGH' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                          r.priority_band === 'MEDIUM' ? 'bg-blue-950 text-blue-300 border border-blue-800' :
                          'bg-slate-800 text-slate-400'
                        }`}>
                          {r.priority_band}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => setSelectedScoreItem(r)}
                          className="font-mono font-bold text-sm text-white hover:text-brand-300 underline decoration-dotted underline-offset-4 cursor-pointer"
                        >
                          {r.impact_score} / 100
                        </button>
                      </td>
                      <td className="py-3 px-4">
                        {!isPreview ? (
                          <button
                            onClick={() => {
                              setDispositionModal({ open: true, item: r });
                              setDispositionChoice(r.disposition || 'UPDATE_REQUIRED');
                            }}
                            className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                          >
                            {r.disposition || 'UPDATE_REQUIRED'}
                          </button>
                        ) : (
                          <span className="text-xs text-slate-400 font-mono">{r.disposition}</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedPathItem(r)}
                          className="text-xs text-brand-400 hover:text-brand-300 font-semibold inline-flex items-center gap-1"
                        >
                          <GitFork className="w-3.5 h-3.5" />
                          <span>Inspect Path</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Explanation Path Modal */}
      {selectedPathItem && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <GitFork className="w-4 h-4 text-brand-400" />
                  <span>Explainable Impact Propagation Path</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Path from changed requirement to <strong className="text-brand-300">{selectedPathItem.artifact_display_id}</strong>
                </p>
              </div>
              <button onClick={() => setSelectedPathItem(null)} className="text-slate-400 hover:text-slate-200">
                <XCircle className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              {selectedPathItem.explanation_paths_json.map((path: any[], pathIdx: number) => (
                <div key={pathIdx} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="text-[11px] font-mono text-slate-400 font-semibold">
                    Shortest Propagation Route #{pathIdx + 1}
                  </div>
                  <div className="space-y-2 text-xs">
                    {path.map((step: any, stepIdx: number) => (
                      <div key={stepIdx} className="flex items-center gap-2 text-slate-300 font-mono">
                        <span className="font-bold text-brand-400">{step.source_display_id}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-sky-300 border border-slate-700">
                          {step.relation_type} ({Math.round(step.relationship_strength * 100)}%)
                        </span>
                        <span className="text-slate-500">➔</span>
                        <span className="font-bold text-purple-400">{step.target_display_id}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {selectedPathItem.warning_flags_json?.length > 0 && (
              <div className="p-3 bg-amber-950/40 border border-amber-900/60 rounded-xl text-xs space-y-1">
                <div className="font-semibold text-amber-300 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <span>Analysis Limitations & Traceability Warnings</span>
                </div>
                <ul className="list-disc list-inside text-[11px] text-slate-400 space-y-0.5">
                  {selectedPathItem.warning_flags_json.map((w: string, i: number) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Score Breakdown Modal */}
      {selectedScoreItem && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-brand-400" />
                <span>Review Priority Score Formula</span>
              </h3>
              <button onClick={() => setSelectedScoreItem(null)} className="text-slate-400 hover:text-slate-200">
                <XCircle className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono text-slate-300 leading-relaxed">
              Score = round(100 × (0.30×D + 0.20×P + 0.25×C + 0.25×V))
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Path Strength (D)</span>
                <span className="font-mono text-slate-200">{selectedScoreItem.path_strength}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Proximity Factor (P = 1/hops)</span>
                <span className="font-mono text-slate-200">{selectedScoreItem.proximity_factor}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Artifact Criticality (C = crit/5)</span>
                <span className="font-mono text-slate-200">{selectedScoreItem.criticality_factor}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Verification Gap Factor (V)</span>
                <span className="font-mono text-slate-200">{selectedScoreItem.verification_gap_factor}</span>
              </div>
              <div className="flex justify-between py-2 font-bold text-sm">
                <span className="text-white">Computed Score</span>
                <span className="font-mono text-brand-400">{selectedScoreItem.impact_score} ({selectedScoreItem.priority_band})</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 italic">
              Note: The score is a human review-priority heuristic, not an empirical probability of defect.
            </p>
          </div>
        </div>
      )}

      {/* Decision Modal (Approve / Reject / Defer) */}
      {decisionModal.open && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">
              {decisionModal.type === 'APPROVE' ? 'Approve Requirement Change' :
               decisionModal.type === 'REJECT' ? 'Reject Change Request' : 'Defer Change Request'}
            </h3>

            <p className="text-xs text-slate-300">
              {decisionModal.type === 'APPROVE'
                ? 'Approving will commit a new immutable requirement version (v2) and create owner-assigned remediation tasks for affected downstream artifacts.'
                : 'A written decision rationale is required for audit and review history.'}
            </p>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Decision Rationale {decisionModal.type !== 'APPROVE' && '(Required)'}
              </label>
              <textarea
                required={decisionModal.type !== 'APPROVE'}
                rows={3}
                placeholder="State the justification for this decision..."
                value={decisionRationale}
                onChange={(e) => setDecisionRationale(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setDecisionModal({ open: false, type: 'APPROVE' })}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-xl text-slate-300 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDecisionSubmit}
                className={`px-4 py-2 text-white text-xs font-semibold rounded-xl transition ${
                  decisionModal.type === 'APPROVE' ? 'bg-emerald-600 hover:bg-emerald-500' :
                  decisionModal.type === 'REJECT' ? 'bg-rose-600 hover:bg-rose-500' :
                  'bg-amber-600 hover:bg-amber-500'
                }`}
              >
                Confirm {decisionModal.type}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disposition Modal */}
      {dispositionModal.open && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Record Artifact Disposition</h3>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Disposition Status</label>
              <select
                value={dispositionChoice}
                onChange={(e) => setDispositionChoice(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="UPDATE_REQUIRED">UPDATE_REQUIRED</option>
                <option value="RETEST_REQUIRED">RETEST_REQUIRED</option>
                <option value="REVIEW_NO_CHANGE">REVIEW_NO_CHANGE</option>
                <option value="NOT_APPLICABLE">NOT_APPLICABLE</option>
                <option value="RISK_ACCEPTED">RISK_ACCEPTED</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">
                Justification Rationale {['NOT_APPLICABLE', 'RISK_ACCEPTED'].includes(dispositionChoice) && '(Required)'}
              </label>
              <textarea
                rows={3}
                placeholder="Provide evidence or rationale..."
                value={dispositionRationale}
                onChange={(e) => setDispositionRationale(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setDispositionModal({ open: false, item: null })}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-xl text-slate-300 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDispositionSubmit}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl transition"
              >
                Update Disposition
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
