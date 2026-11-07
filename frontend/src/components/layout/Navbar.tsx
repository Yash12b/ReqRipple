import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Layers, ChevronDown, LogOut, User, Sparkles } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, projects, activeProject, selectProject, logout } = useAuth();

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight leading-none flex items-center gap-1.5">
              ReqRipple
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-brand-950 text-brand-400 border border-brand-800">
                v1.0
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 mt-0.5">Software Requirement Impact Analyser</p>
          </div>
        </div>

        {projects.length > 0 && (
          <div className="relative group">
            <select
              value={activeProject?.id || ''}
              onChange={(e) => selectProject(e.target.value)}
              className="appearance-none bg-slate-800/90 text-sm font-medium text-slate-200 border border-slate-700/80 rounded-lg pl-3 pr-8 py-1.5 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 cursor-pointer"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  📁 {p.name}
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-semibold text-slate-200">{user.name}</div>
              <div className="text-xs text-slate-400 font-mono">{user.email}</div>
            </div>
            <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
              <User className="w-4 h-4" />
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
