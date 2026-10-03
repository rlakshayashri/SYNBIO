import React from "react";
import Link from "next/link";
import { Database, FlaskConical, Layers } from "lucide-react";

export const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-lg bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-600/30 transition-colors">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <span className="text-lg font-bold text-white tracking-tight">SynDataX</span>
            <span className="ml-2 text-xs font-medium text-cyan-400 px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/50">
              v0.1.0
            </span>
          </div>
        </Link>

        <nav className="flex items-center space-x-6 text-sm font-medium">
          <Link
            href="/"
            className="flex items-center space-x-2 text-slate-300 hover:text-white transition-colors"
          >
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Projects</span>
          </Link>
          <div className="h-4 w-px bg-slate-800" />
          <div className="flex items-center space-x-2 text-slate-400 text-xs">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span>PostgreSQL Ready</span>
          </div>
        </nav>
      </div>
    </header>
  );
};
