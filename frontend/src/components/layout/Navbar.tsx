import React from 'react';
import { Layers, Activity, ShieldCheck } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600 text-white p-2 rounded-lg shadow-sm">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 tracking-tight leading-none">
              SkillBridge AI
            </h1>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Career Intelligence Platform
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-2 text-xs font-medium text-slate-600 bg-slate-100 px-3 py-1.5 rounded-full">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Phase 5: Semantic Matching & Scoring</span>
          </div>
          <div className="flex items-center space-x-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-md">
            <Activity className="w-3.5 h-3.5 animate-pulse text-emerald-600" />
            <span>Ready</span>
          </div>
        </div>
      </div>
    </header>
  );
};
