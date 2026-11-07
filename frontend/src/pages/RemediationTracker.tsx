import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import {
  CheckSquare,
  ShieldCheck,
  CheckCircle,
  AlertCircle,
  X,
  PlayCircle,
  Clock,
  Layers,
} from 'lucide-react';

export const RemediationTracker: React.FC = () => {
  const { activeProject } = useAuth();
  const [changeRequests, setChangeRequests] = useState<any[]>([]);
  const [selectedCrId, setSelectedCrId] = useState<string>('');
  const [crDetail, setCrDetail] = useState<any>(null);
  const [closureStatus, setClosureStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Test execution modal
  const [testModal, setTestModal] = useState<{ open: boolean; artifactId: string; artifactDisplay: string }>({
    open: false,
    artifactId: '',
    artifactDisplay: '',
  });
  const [testResult, setTestResult] = useState('PASSED');
  const [testNotes, setTestNotes] = useState('');

  const loadChangeRequests = () => {
    if (!activeProject) return;
    setLoading(true);
    api.getChangeRequests(activeProject.id)
      .then((res) => {
        const items = res.items || [];
        setChangeRequests(items);
        if (items.length > 0 && !selectedCrId) {
          const approved = items.find((c: any) => ['IMPLEMENTING', 'APPROVED', 'VERIFICATION_PENDING'].includes(c.status)) || items[0];
          setSelectedCrId(approved.id);
        }
      })
      .catch((err) => console.error('Failed to load change requests', err))
      .finally(() => setLoading(false));
  };

  const loadCrDetail = () => {
    if (!selectedCrId) return;
    api.getChangeRequest(selectedCrId).then((data) => {
      setCrDetail(data);
      checkClosure(selectedCrId);
    });
  };

  const checkClosure = async (crId: string) => {
    try {
      const res = await api.checkClosure(crId);
      setClosureStatus(res);
    } catch (err) {
      console.error('Failed to check closure', err);
    }
  };

  useEffect(() => {
    loadChangeRequests();
  }, [activeProject?.id]);

  useEffect(() => {
    if (selectedCrId) {
      loadCrDetail();
    }
  }, [selectedCrId]);

  const handleActionStatusChange = async (actionId: string, newStatus: string) => {
    try {
      await api.updateRemediationAction(actionId, {
        status: newStatus,
        completion_notes: `Marked as ${newStatus} on ${new Date().toLocaleDateString()}`,
      });
      loadCrDetail();
    } catch (err: any) {
      alert(`Error updating action: ${err.message}`);
    }
  };

  const handleRecordTestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.recordTestExecution(testModal.artifactId, {
        change_request_id: selectedCrId,
        result: testResult,
        notes: testNotes,
      });
      setTestModal({ open: false, artifactId: '', artifactDisplay: '' });
      setTestNotes('');
      loadCrDetail();
    } catch (err: any) {
      alert(`Error recording test: ${err.message}`);
    }
  };

  const handleCloseChangeRequest = async () => {
    if (!confirm('Are you sure you want to finalize and close this change request?')) return;
    try {
      await api.closeChange(selectedCrId);
      alert('Change request closed successfully!');
      loadCrDetail();
      loadChangeRequests();
    } catch (err: any) {
      alert(`Error closing change request: ${err.message}`);
    }
  };

  const results = crDetail?.latest_analysis?.results || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
            <CheckSquare className="w-5 h-5 text-emerald-400" />
            <span>Remediation & Verification Tracker</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Track implementation actions, retest executions, and verify change closure conditions.
          </p>
        </div>

        {changeRequests.length > 0 && (
          <select
            value={selectedCrId}
            onChange={(e) => setSelectedCrId(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
          >
            {changeRequests.map((cr) => (
              <option key={cr.id} value={cr.id}>
                {cr.title} ({cr.status})
              </option>
            ))}
          </select>
        )}
      </div>

      {crDetail && (
        <div className="space-y-6">
          {/* Closure Check Status Banner */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                {closureStatus?.can_close ? (
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-amber-400" />
                )}
                <span>
                  {closureStatus?.can_close
                    ? 'All Remediation & Verification Rules Passed'
                    : 'Closure Blocked: Unmet Engineering Tasks'}
                </span>
                <span className="text-xs px-2 py-0.5 rounded font-mono font-semibold bg-slate-800 text-slate-300">
                  Status: {crDetail.status}
                </span>
              </div>
              {closureStatus?.blocking_reasons?.length > 0 && (
                <ul className="list-disc list-inside text-xs text-amber-300/80 mt-2 space-y-1">
                  {closureStatus.blocking_reasons.map((r: string, idx: number) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              )}
            </div>

            {crDetail.status !== 'CLOSED' && (
              <button
                onClick={handleCloseChangeRequest}
                disabled={!closureStatus?.can_close}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-600/25 transition self-start sm:self-auto shrink-0"
              >
                Close Change Request
              </button>
            )}
          </div>

          {/* Remediation Actions List */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-brand-400" />
              <span>Assigned Remediation Actions for Impacted Artifacts</span>
            </h3>

            {results.length === 0 ? (
              <div className="text-xs text-slate-400 py-6 text-center">
                No impact analysis snapshot found for this change request.
              </div>
            ) : (
              <div className="space-y-4">
                {results.map((r: any) => {
                  const isTest = r.artifact_type === 'TEST_CASE';
                  const actions = r.actions || [];
                  return (
                    <div
                      key={r.id}
                      className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="font-mono font-bold text-xs text-brand-400">
                            {r.artifact_display_id}
                          </span>
                          <span className="text-xs font-semibold text-slate-200">
                            {r.artifact_title}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-slate-800 text-slate-400">
                            {r.artifact_type}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-slate-400">
                            Disposition: <strong className="text-slate-200">{r.disposition}</strong>
                          </span>
                          {isTest && (
                            <button
                              onClick={() =>
                                setTestModal({
                                  open: true,
                                  artifactId: r.artifact_id,
                                  artifactDisplay: r.artifact_display_id,
                                })
                              }
                              className="px-2.5 py-1 bg-purple-950/60 hover:bg-purple-900 border border-purple-800 text-purple-300 text-xs font-semibold rounded-lg transition flex items-center gap-1.5"
                            >
                              <PlayCircle className="w-3.5 h-3.5" />
                              <span>Record Test</span>
                            </button>
                          )}
                        </div>
                      </div>

                      {actions.length > 0 && (
                        <div className="space-y-2 pt-2 border-t border-slate-900">
                          {actions.map((act: any) => (
                            <div
                              key={act.id}
                              className="flex items-center justify-between text-xs p-2.5 bg-slate-900/60 rounded-lg border border-slate-800"
                            >
                              <div>
                                <span className="font-medium text-slate-200">{act.title}</span>
                                <span className="text-[11px] text-slate-400 ml-2">
                                  ({act.action_type})
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-[11px] text-slate-400">Status:</span>
                                <select
                                  value={act.status}
                                  onChange={(e) => handleActionStatusChange(act.id, e.target.value)}
                                  className={`px-2 py-1 rounded text-xs font-mono font-semibold focus:outline-none cursor-pointer ${
                                    act.status === 'DONE'
                                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                                      : act.status === 'WAIVED'
                                      ? 'bg-slate-800 text-slate-300 border border-slate-700'
                                      : 'bg-amber-950 text-amber-300 border border-amber-800'
                                  }`}
                                >
                                  <option value="OPEN">OPEN</option>
                                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                                  <option value="DONE">DONE</option>
                                  <option value="WAIVED">WAIVED</option>
                                  <option value="BLOCKED">BLOCKED</option>
                                </select>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Record Test Modal */}
      {testModal.open && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Record Verification Outcome</h3>
              <button
                onClick={() => setTestModal({ open: false, artifactId: '', artifactDisplay: '' })}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleRecordTestSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-mono">Test Case</label>
                <div className="font-mono font-bold text-purple-400 text-sm">
                  {testModal.artifactDisplay}
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Execution Result</label>
                <select
                  value={testResult}
                  onChange={(e) => setTestResult(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="PASSED">PASSED</option>
                  <option value="FAILED">FAILED</option>
                  <option value="BLOCKED">BLOCKED</option>
                  <option value="NOT_RUN">NOT_RUN</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Test Notes / Output Summary</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Verified OTP prompt and verified invalid code lockout."
                  value={testNotes}
                  onChange={(e) => setTestNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setTestModal({ open: false, artifactId: '', artifactDisplay: '' })}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-xl text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl transition shadow-lg shadow-purple-600/25"
                >
                  Save Test Result
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
