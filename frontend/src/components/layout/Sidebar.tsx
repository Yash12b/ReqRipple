import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Boxes,
  GitFork,
  GitPullRequest,
  CheckSquare,
  BarChart3,
  ShieldAlert,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/requirements', label: 'Requirements', icon: FileText },
  { to: '/artifacts', label: 'Artifacts', icon: Boxes },
  { to: '/graph', label: 'Traceability Graph', icon: GitFork },
  { to: '/change-requests', label: 'Change Requests', icon: GitPullRequest },
  { to: '/remediation', label: 'Remediation & Testing', icon: CheckSquare },
  { to: '/reports', label: 'Debt & Reports', icon: BarChart3 },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between shrink-0">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase font-mono">
          Workspace Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/80'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>

      <div className="p-3 rounded-xl bg-slate-900 border border-slate-800/80 text-xs text-slate-400 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-slate-200">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          <span>Decision Support</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Analysis derives from human-maintained traceability links. Always verify high-criticality items.
        </p>
      </div>
    </aside>
  );
};
