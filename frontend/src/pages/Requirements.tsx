import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import {
  FileText,
  Plus,
  Search,
  History,
  X,
  Layers,
  CheckCircle,
} from 'lucide-react';

export const Requirements: React.FC = () => {
  const { activeProject } = useAuth();
  const [requirements, setRequirements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedReq, setSelectedReq] = useState<any>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    display_id: '',
    title: '',
    description: '',
    requirement_type: 'FUNCTIONAL',
    priority: 'MEDIUM',
    criticality: 3,
    acceptance_criteria: '',
    rationale: '',
  });

  const loadRequirements = () => {
    if (!activeProject) return;
    setLoading(true);
    api.getRequirements(activeProject.id, { search })
      .then((res) => setRequirements(res.items || []))
      .catch((err) => console.error('Failed to load requirements', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRequirements();
  }, [activeProject?.id, search]);

  const handleSelectReq = async (req: any) => {
    setSelectedReq(req);
    try {
      const vers = await api.getRequirementVersions(req.id);
      setVersions(vers);
    } catch (err) {
      console.error('Failed to load versions', err);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      const acList = formData.acceptance_criteria
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);

      await api.createRequirement(activeProject.id, {
        ...formData,
        acceptance_criteria: acList,
      });
      setShowCreateModal(false);
      setFormData({
        display_id: '',
        title: '',
        description: '',
        requirement_type: 'FUNCTIONAL',
        priority: 'MEDIUM',
        criticality: 3,
        acceptance_criteria: '',
        rationale: '',
      });
      loadRequirements();
    } catch (err: any) {
      alert(`Error creating requirement: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
            <FileText className="w-5 h-5 text-brand-400" />
            <span>Requirements Repository</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Structured, versioned specifications. Changes create immutable historical baselines.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-brand-600/25 transition flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Requirement</span>
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-3 bg-slate-900 p-3 rounded-xl border border-slate-800">
        <Search className="w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search by ID, title or description keyword..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent text-sm text-slate-200 placeholder-slate-500 w-full focus:outline-none"
        />
      </div>

      {/* Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Requirements Table */}
        <div className={`space-y-4 ${selectedReq ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase font-mono text-slate-400 border-b border-slate-800 bg-slate-950/40">
                  <tr>
                    <th className="py-3 px-4">ID</th>
                    <th className="py-3 px-4">Title</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Version</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                        Loading requirements...
                      </td>
                    </tr>
                  ) : requirements.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                        No requirements found.
                      </td>
                    </tr>
                  ) : (
                    requirements.map((r) => (
                      <tr
                        key={r.id}
                        onClick={() => handleSelectReq(r)}
                        className={`cursor-pointer transition ${
                          selectedReq?.id === r.id ? 'bg-brand-950/40' : 'hover:bg-slate-800/40'
                        }`}
                      >
                        <td className="py-3 px-4 font-mono font-bold text-brand-400 text-xs">{r.display_id}</td>
                        <td className="py-3 px-4 font-medium text-slate-200">
                          {r.current_version?.title || r.title || r.display_id}
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-400 font-mono">{r.requirement_type}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                              r.priority === 'CRITICAL'
                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                : r.priority === 'HIGH'
                                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {r.priority}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-xs font-mono text-slate-400">
                          v{r.current_version?.version_number || 1}
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
                            {r.lifecycle_status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Selected Detail Drawer */}
        {selectedReq && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-6 self-start lg:sticky lg:top-24 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-brand-400">{selectedReq.display_id}</span>
                <span className="text-xs px-2 py-0.5 bg-slate-800 rounded text-slate-300">
                  Criticality: {selectedReq.criticality}/5
                </span>
              </div>
              <button
                onClick={() => setSelectedReq(null)}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <h3 className="text-base font-bold text-white mb-2">
                {selectedReq.current_version?.title || selectedReq.display_id}
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {selectedReq.current_version?.description}
              </p>
            </div>

            {selectedReq.current_version?.acceptance_criteria_json?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 font-mono">
                  Acceptance Criteria
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-300">
                  {selectedReq.current_version.acceptance_criteria_json.map((ac: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{ac}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Version History */}
            <div className="pt-4 border-t border-slate-800">
              <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-slate-300">
                <History className="w-4 h-4 text-brand-400" />
                <span>Immutable Version History ({versions.length})</span>
              </div>
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {versions.map((v) => (
                  <div
                    key={v.id}
                    className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between font-mono font-semibold">
                      <span className="text-brand-400">Version {v.version_number}</span>
                      <span className="text-[10px] text-slate-400">
                        {new Date(v.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="text-slate-200 font-medium">{v.title}</div>
                    <div className="text-[11px] text-slate-400 italic">
                      Rationale: {v.rationale || 'Baseline version'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Create New Requirement</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Display ID (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. REQ-011"
                    value={formData.display_id}
                    onChange={(e) => setFormData({ ...formData, display_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Requirement Type</label>
                  <select
                    value={formData.requirement_type}
                    onChange={(e) => setFormData({ ...formData, requirement_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="FUNCTIONAL">Functional</option>
                    <option value="NON_FUNCTIONAL">Non-Functional</option>
                    <option value="SECURITY">Security</option>
                    <option value="PERFORMANCE">Performance</option>
                    <option value="REGULATORY">Regulatory</option>
                    <option value="USABILITY">Usability</option>
                    <option value="BUSINESS">Business</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Event Capacity Limit Validation"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Description</label>
                <textarea
                  required
                  rows={3}
                  placeholder="The system shall prevent registration once the maximum seat limit is reached."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Priority</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Criticality (1 - 5)</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={formData.criticality}
                    onChange={(e) => setFormData({ ...formData, criticality: parseInt(e.target.value) || 3 })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Acceptance Criteria (1 per line)</label>
                <textarea
                  rows={2}
                  placeholder="Displays sold-out banner&#10;Rejects submission if seat limit = 0"
                  value={formData.acceptance_criteria}
                  onChange={(e) => setFormData({ ...formData, acceptance_criteria: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold rounded-xl text-slate-300 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl transition shadow-lg shadow-brand-600/25"
                >
                  Create Requirement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
