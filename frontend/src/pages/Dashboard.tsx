import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import {
  FileText,
  Boxes,
  GitFork,
  GitPullRequest,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ShieldAlert,
  Flame,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { activeProject } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!activeProject) return;
    setLoading(true);
    api.getDashboard(activeProject.id)
      .then(setData)
      .catch((err) => console.error('Dashboard load error', err))
      .finally(() => setLoading(false));
  }, [activeProject?.id]);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="animate-spin w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full mr-3"></div>
        Loading dashboard metrics...
      </div>
    );
  }

  const { traceability_health: health, change_debt: debt, recent_change_requests: crs } = data;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">{activeProject?.name}</h2>
          <p className="text-sm text-slate-400 mt-1">
            {activeProject?.domain} • {activeProject?.description || 'Traceability and Change Management'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/change-requests"
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-brand-600/25 transition flex items-center gap-2"
          >
            <GitPullRequest className="w-4 h-4" />
            <span>Submit Change Request</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-mono">{data.total_requirements}</div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">Requirements</div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
            <Boxes className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-mono">{data.total_artifacts}</div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">Artifacts</div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
            <GitFork className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-mono">{data.total_active_edges}</div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">Traceability Links</div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white font-mono">{data.open_change_requests_count}</div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">Open Changes</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Health & Debt */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Traceability Health Monitor */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Traceability Health Monitor</h3>
            </div>
            <Link to="/graph" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
              <span>Inspect Graph</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-300 font-medium">Requirements with Implementation Links</span>
                <span className="text-slate-400 font-mono">
                  {health.requirements_with_implementation} of {health.total_requirements} (
                  {Math.round((health.requirements_with_implementation / (health.total_requirements || 1)) * 100)}%)
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.round((health.requirements_with_implementation / (health.total_requirements || 1)) * 100)}%`,
                  }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-300 font-medium">Requirements with Verification Links</span>
                <span className="text-slate-400 font-mono">
                  {health.requirements_with_verification} of {health.total_requirements} (
                  {Math.round((health.requirements_with_verification / (health.total_requirements || 1)) * 100)}%)
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.round((health.requirements_with_verification / (health.total_requirements || 1)) * 100)}%`,
                  }}
                ></div>
              </div>
            </div>

            {health.critical_untested_count > 0 && (
              <div className="p-3 bg-rose-950/40 border border-rose-900/60 rounded-xl text-xs space-y-1">
                <div className="font-semibold text-rose-300 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  <span>{health.critical_untested_count} Critical Artifact(s) Missing Verification</span>
                </div>
                <div className="text-slate-400 text-[11px]">
                  {health.critical_untested.map((u: any) => `${u.display_id} (${u.title})`).join(', ')}
                </div>
              </div>
            )}

            {health.orphan_artifacts_count > 0 && (
              <div className="p-3 bg-amber-950/40 border border-amber-900/60 rounded-xl text-xs space-y-1">
                <div className="font-semibold text-amber-300 flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <span>{health.orphan_artifacts_count} Disconnected/Orphan Artifact(s)</span>
                </div>
                <div className="text-slate-400 text-[11px]">
                  {health.orphan_artifacts.map((o: any) => o.display_id).join(', ')}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Change Debt Dashboard */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-amber-400" />
              <h3 className="text-base font-bold text-white">Change Debt Dashboard</h3>
            </div>
            <Link to="/reports" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
              <span>View Volatility</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80">
              <div className="text-xs text-slate-400">Open Approved Changes</div>
              <div className="text-xl font-bold text-white font-mono mt-1">{debt.open_approved_changes_count}</div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80">
              <div className="text-xs text-slate-400">Unreviewed High/Crit Impacts</div>
              <div className={`text-xl font-bold font-mono mt-1 ${debt.unreviewed_high_critical_count > 0 ? 'text-amber-400' : 'text-slate-200'}`}>
                {debt.unreviewed_high_critical_count}
              </div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80">
              <div className="text-xs text-slate-400">Pending Retests</div>
              <div className={`text-xl font-bold font-mono mt-1 ${debt.pending_retests_count > 0 ? 'text-blue-400' : 'text-slate-200'}`}>
                {debt.pending_retests_count}
              </div>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800/80">
              <div className="text-xs text-slate-400">Failed / Blocked Tests</div>
              <div className={`text-xl font-bold font-mono mt-1 ${debt.failed_tests_count > 0 ? 'text-rose-400' : 'text-slate-200'}`}>
                {debt.failed_tests_count}
              </div>
            </div>
          </div>

          <div className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/50">
            💡 <strong className="text-slate-300">Change Debt</strong> represents engineering rework and testing tasks created by approved requirement changes that have not yet been completed or verified.
          </div>
        </div>
      </div>

      {/* Recent Change Requests */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <GitPullRequest className="w-5 h-5 text-brand-400" />
            <span>Recent Change Proposals</span>
          </h3>
          <Link to="/change-requests" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {crs.length === 0 ? (
          <div className="text-sm text-slate-400 py-6 text-center">
            No change requests submitted yet for this project.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase font-mono text-slate-400 border-b border-slate-800 bg-slate-950/30">
                <tr>
                  <th className="py-2.5 px-3">Title</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Urgency</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {crs.map((cr: any) => (
                  <tr key={cr.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3 font-medium text-slate-200">{cr.title}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                        {cr.status}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`text-xs font-semibold ${
                        cr.urgency === 'CRITICAL' ? 'text-rose-400' :
                        cr.urgency === 'HIGH' ? 'text-amber-400' : 'text-slate-300'
                      }`}>
                        {cr.urgency}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-xs text-slate-400 font-mono">
                      {new Date(cr.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        to={`/change-requests/${cr.id}`}
                        className="text-xs text-brand-400 hover:text-brand-300 font-semibold"
                      >
                        Workspace →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
