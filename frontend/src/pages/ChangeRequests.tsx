import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import {
  GitPullRequest,
  Plus,
  ArrowRight,
  X,
  FileDiff,
  Flame,
  CheckCircle,
  Clock,
} from 'lucide-react';

export const ChangeRequests: React.FC = () => {
  const { activeProject } = useAuth();
  const [changeRequests, setChangeRequests] = useState<any[]>([]);
  const [requirements, setRequirements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    requirement_id: '',
    title: '',
    reason: '',
    business_justification: '',
    urgency: 'HIGH',
    proposed_title: '',
    proposed_description: '',
    proposed_acceptance_criteria: '',
  });

  const loadData = () => {
    if (!activeProject) return;
    setLoading(true);
    Promise.all([
      api.getChangeRequests(activeProject.id),
      api.getRequirements(activeProject.id),
    ])
      .then(([crs, reqs]) => {
        setChangeRequests(crs.items || []);
        setRequirements(reqs.items || []);
      })
      .catch((err) => console.error('Failed to load change requests', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [activeProject?.id]);

  const handleRequirementSelect = (reqId: string) => {
    const selected = requirements.find((r) => r.id === reqId);
    if (selected) {
      setFormData({
        ...formData,
        requirement_id: reqId,
        proposed_title: selected.current_version?.title || selected.title || '',
        proposed_description: selected.current_version?.description || '',
        proposed_acceptance_criteria: (selected.current_version?.acceptance_criteria_json || []).join('\n'),
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      const acList = formData.proposed_acceptance_criteria
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);

      const proposedFields: Record<string, any> = {};
      if (formData.proposed_title) proposedFields.title = formData.proposed_title;
      if (formData.proposed_description) proposedFields.description = formData.proposed_description;
      if (acList.length > 0) proposedFields.acceptance_criteria = acList;

      await api.createChangeRequest(activeProject.id, {
        requirement_id: formData.requirement_id,
        title: formData.title,
        reason: formData.reason,
        business_justification: formData.business_justification,
        urgency: formData.urgency,
        proposed_fields: proposedFields,
      });

      setShowModal(false);
      setFormData({
        requirement_id: '',
        title: '',
        reason: '',
        business_justification: '',
        urgency: 'HIGH',
        proposed_title: '',
        proposed_description: '',
        proposed_acceptance_criteria: '',
      });
      loadData();
    } catch (err: any) {
      alert(`Error submitting change request: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
            <GitPullRequest className="w-5 h-5 text-brand-400" />
            <span>Change Request Desk</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Propose, simulate ripple effects, analyze downstream impact, and approve requirement versions.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-brand-600/25 transition flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Submit Change Request</span>
        </button>
      </div>

      {/* Change Requests Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase font-mono text-slate-400 border-b border-slate-800 bg-slate-950/40">
              <tr>
                <th className="py-3 px-4">Change Proposal</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Urgency</th>
                <th className="py-3 px-4">Reason</th>
                <th className="py-3 px-4">Submitted</th>
                <th className="py-3 px-4 text-right">Workspace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                    Loading change proposals...
                  </td>
                </tr>
              ) : changeRequests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                    No change requests registered. Propose a change above to begin impact analysis.
                  </td>
                </tr>
              ) : (
                changeRequests.map((cr) => (
                  <tr key={cr.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-200">{cr.title}</div>
                      <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                        Target Requirement: {cr.requirement_id.slice(0, 8)}...
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {cr.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-xs font-bold font-mono ${
                          cr.urgency === 'CRITICAL'
                            ? 'text-rose-400'
                            : cr.urgency === 'HIGH'
                            ? 'text-amber-400'
                            : 'text-slate-300'
                        }`}
                      >
                        {cr.urgency}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-300 max-w-xs truncate">{cr.reason}</td>
                    <td className="py-3 px-4 text-xs font-mono text-slate-400">
                      {new Date(cr.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/change-requests/${cr.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-600/20 hover:bg-brand-600/30 text-brand-400 text-xs font-semibold rounded-lg border border-brand-500/30 transition"
                      >
                        <span>Analyse Impact</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Propose Change Request Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Propose Software Requirement Change</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-mono">Target Requirement to Change</label>
                <select
                  required
                  value={formData.requirement_id}
                  onChange={(e) => handleRequirementSelect(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="">Select requirement...</option>
                  {requirements.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.display_id} - {r.current_version?.title || r.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-mono">Change Request Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Require OTP Verification on Event Registration"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-mono">Reason for Change</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Security audit identified bot spam vulnerability."
                    value={formData.reason}
                    onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-mono">Urgency</label>
                  <select
                    value={formData.urgency}
                    onChange={(e) => setFormData({ ...formData, urgency: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <div className="text-[11px] font-bold text-brand-400 uppercase tracking-wider mb-2 font-mono flex items-center gap-1.5">
                  <FileDiff className="w-3.5 h-3.5" />
                  <span>Proposed Content Modifications</span>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-mono">Proposed Title</label>
                    <input
                      type="text"
                      value={formData.proposed_title}
                      onChange={(e) => setFormData({ ...formData, proposed_title: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1 font-mono">Proposed Description</label>
                    <textarea
                      rows={3}
                      value={formData.proposed_description}
                      onChange={(e) => setFormData({ ...formData, proposed_description: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1 font-mono">Proposed Acceptance Criteria (1 per line)</label>
                    <textarea
                      rows={2}
                      value={formData.proposed_acceptance_criteria}
                      onChange={(e) => setFormData({ ...formData, proposed_acceptance_criteria: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-xl text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl transition shadow-lg shadow-brand-600/25"
                >
                  Submit for Analysis
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
