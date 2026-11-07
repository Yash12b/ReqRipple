import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { Boxes, Plus, Search, Filter, X, Clock, ExternalLink } from 'lucide-react';

const ARTIFACT_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  USER_STORY: { label: 'User Story', color: 'bg-emerald-950 text-emerald-300 border-emerald-800' },
  ACCEPTANCE_CRITERIA: { label: 'Acceptance Criterion', color: 'bg-teal-950 text-teal-300 border-teal-800' },
  DESIGN_COMPONENT: { label: 'Design Component', color: 'bg-pink-950 text-pink-300 border-pink-800' },
  MODULE_SERVICE: { label: 'Module / Service', color: 'bg-indigo-950 text-indigo-300 border-indigo-800' },
  API_ENDPOINT: { label: 'API Endpoint', color: 'bg-blue-950 text-blue-300 border-blue-800' },
  DATABASE_ENTITY: { label: 'Database Entity', color: 'bg-amber-950 text-amber-300 border-amber-800' },
  UI_SCREEN: { label: 'UI Screen', color: 'bg-cyan-950 text-cyan-300 border-cyan-800' },
  TEST_CASE: { label: 'Test Case', color: 'bg-purple-950 text-purple-300 border-purple-800' },
  DOCUMENTATION: { label: 'Documentation', color: 'bg-slate-800 text-slate-300 border-slate-700' },
  DEPLOYMENT_CONFIG: { label: 'Deployment Config', color: 'bg-orange-950 text-orange-300 border-orange-800' },
};

export const Artifacts: React.FC = () => {
  const { activeProject } = useAuth();
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [showModal, setShowModal] = useState(false);

  const [formData, setFormData] = useState({
    display_id: '',
    artifact_type: 'MODULE_SERVICE',
    title: '',
    description: '',
    criticality: 3,
    estimated_effort_hours: 8,
    external_reference: '',
  });

  const loadArtifacts = () => {
    if (!activeProject) return;
    setLoading(true);
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (typeFilter) params.artifact_type = typeFilter;

    api.getArtifacts(activeProject.id, params)
      .then((res) => setArtifacts(res.items || []))
      .catch((err) => console.error('Failed to load artifacts', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadArtifacts();
  }, [activeProject?.id, search, typeFilter]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;
    try {
      await api.createArtifact(activeProject.id, formData);
      setShowModal(false);
      setFormData({
        display_id: '',
        artifact_type: 'MODULE_SERVICE',
        title: '',
        description: '',
        criticality: 3,
        estimated_effort_hours: 8,
        external_reference: '',
      });
      loadArtifacts();
    } catch (err: any) {
      alert(`Error creating artifact: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
            <Boxes className="w-5 h-5 text-purple-400" />
            <span>Engineering Artifact Registry</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Downstream technical components linked to requirements for ripple and impact assessment.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-brand-600/25 transition flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Artifact</span>
        </button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2 flex items-center gap-3 bg-slate-900 p-3 rounded-xl border border-slate-800">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search artifacts by ID or title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-sm text-slate-200 placeholder-slate-500 w-full focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-2 bg-slate-900 p-2 rounded-xl border border-slate-800">
          <Filter className="w-4 h-4 text-slate-400 ml-2" />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-transparent text-xs text-slate-300 w-full focus:outline-none cursor-pointer"
          >
            <option value="">All Artifact Types</option>
            {Object.keys(ARTIFACT_TYPE_LABELS).map((t) => (
              <option key={t} value={t} className="bg-slate-900">
                {ARTIFACT_TYPE_LABELS[t].label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Artifacts Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase font-mono text-slate-400 border-b border-slate-800 bg-slate-950/40">
              <tr>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Title</th>
                <th className="py-3 px-4">Criticality</th>
                <th className="py-3 px-4">Est. Effort</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                    Loading engineering artifacts...
                  </td>
                </tr>
              ) : artifacts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                    No artifacts found matching criteria.
                  </td>
                </tr>
              ) : (
                artifacts.map((a) => {
                  const meta = ARTIFACT_TYPE_LABELS[a.artifact_type] || {
                    label: a.artifact_type,
                    color: 'bg-slate-800 text-slate-300 border-slate-700',
                  };
                  return (
                    <tr key={a.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-mono font-bold text-purple-400 text-xs">{a.display_id}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono border font-semibold ${meta.color}`}>
                          {meta.label}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-200">
                        <div>{a.title}</div>
                        {a.description && (
                          <div className="text-[11px] text-slate-400 truncate max-w-md mt-0.5">{a.description}</div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-mono text-xs font-semibold text-slate-300">
                          {a.criticality} / 5
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs font-mono text-slate-400">
                        {a.estimated_effort_hours || 0} hrs
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                          {a.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white">Register Engineering Artifact</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Display ID (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. API-006"
                    value={formData.display_id}
                    onChange={(e) => setFormData({ ...formData, display_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Artifact Type</label>
                  <select
                    value={formData.artifact_type}
                    onChange={(e) => setFormData({ ...formData, artifact_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {Object.keys(ARTIFACT_TYPE_LABELS).map((t) => (
                      <option key={t} value={t}>
                        {ARTIFACT_TYPE_LABELS[t].label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Attendance Verification Endpoint"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Details of the technical contract, API method, or module."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Criticality (1-5)</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={formData.criticality}
                    onChange={(e) => setFormData({ ...formData, criticality: parseInt(e.target.value) || 3 })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Est. Effort (Hours)</label>
                  <input
                    type="number"
                    step={0.5}
                    min={0}
                    value={formData.estimated_effort_hours}
                    onChange={(e) => setFormData({ ...formData, estimated_effort_hours: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
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
                  Register Artifact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
