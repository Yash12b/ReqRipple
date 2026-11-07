import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { BarChart3, Flame, AlertTriangle, ShieldCheck, History } from 'lucide-react';

export const Reports: React.FC = () => {
  const { activeProject } = useAuth();
  const [debt, setDebt] = useState<any>(null);
  const [volatility, setVolatility] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!activeProject) return;
    setLoading(true);
    Promise.all([
      api.getChangeDebt(activeProject.id),
      api.getVolatility(activeProject.id),
    ])
      .then(([d, v]) => {
        setDebt(d);
        setVolatility(v);
      })
      .catch((err) => console.error('Failed to load reports', err))
      .finally(() => setLoading(false));
  }, [activeProject?.id]);

  if (loading || !debt) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 text-xs">
        Loading reports & analytics...
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
          <BarChart3 className="w-5 h-5 text-amber-400" />
          <span>Change Debt & Requirement Volatility Reports</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Auditable quality assurance metrics: Track unstable requirements, unresolved engineering debt, and test coverage gaps.
        </p>
      </div>

      {/* Change Debt Indicators */}
      <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Flame className="w-4 h-4 text-amber-400" />
          <span>Project Change Debt Breakdown</span>
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400">Open Changes</div>
            <div className="text-xl font-bold font-mono text-white mt-1">
              {debt.open_approved_changes_count}
            </div>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400">Unreviewed Impacts</div>
            <div className="text-xl font-bold font-mono text-amber-400 mt-1">
              {debt.unreviewed_high_critical_count}
            </div>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400">Overdue Actions</div>
            <div className="text-xl font-bold font-mono text-rose-400 mt-1">
              {debt.overdue_actions_count}
            </div>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400">Pending Retests</div>
            <div className="text-xl font-bold font-mono text-blue-400 mt-1">
              {debt.pending_retests_count}
            </div>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400">Failed Tests</div>
            <div className="text-xl font-bold font-mono text-rose-500 mt-1">
              {debt.failed_tests_count}
            </div>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
            <div className="text-[11px] text-slate-400">Accepted Risks</div>
            <div className="text-xl font-bold font-mono text-purple-400 mt-1">
              {debt.accepted_risks_count}
            </div>
          </div>
        </div>
      </div>

      {/* Volatility Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <History className="w-4 h-4 text-brand-400" />
            <span>Requirement Volatility Ranking (Change Frequency)</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            High change frequency signals unstable scope or architectural churn
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase font-mono text-slate-400 border-b border-slate-800 bg-slate-950/40">
              <tr>
                <th className="py-3 px-4">Requirement</th>
                <th className="py-3 px-4">Title</th>
                <th className="py-3 px-4">Total Versions</th>
                <th className="py-3 px-4">Approved Changes</th>
                <th className="py-3 px-4">Stability Signal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {volatility.map((v) => (
                <tr key={v.requirement_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-mono font-bold text-brand-400 text-xs">
                    {v.display_id}
                  </td>
                  <td className="py-3 px-4 text-xs font-medium text-slate-200">
                    {v.title}
                  </td>
                  <td className="py-3 px-4 text-xs font-mono text-slate-300">
                    v{v.version_count}
                  </td>
                  <td className="py-3 px-4 text-xs font-mono font-bold text-slate-200">
                    {v.approved_changes_count}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        v.volatility_signal === 'HIGH'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800'
                          : v.volatility_signal === 'MEDIUM'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800'
                          : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      }`}
                    >
                      {v.volatility_signal}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
