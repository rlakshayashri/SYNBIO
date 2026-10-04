import React from "react";
import Link from "next/link";
import { ArrowLeft, Dna, FlaskConical, Layers } from "lucide-react";
import { Experiment } from "../../lib/types/experiment";
import { ExperimentStatusBadge } from "./ExperimentStatusBadge";

interface ExperimentHeaderProps {
  experiment: Experiment;
}

export const ExperimentHeader: React.FC<ExperimentHeaderProps> = ({ experiment }) => {
  return (
    <div className="space-y-4">
      {/* Back Link */}
      <Link
        href="/experiments"
        className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-cyan-400 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Experiments Workbench</span>
      </Link>

      {/* Main Title & Attributes Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
        <div className="flex items-start space-x-4">
          <div className="w-12 h-12 rounded-xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 flex-shrink-0">
            <FlaskConical className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl font-bold text-white tracking-tight">{experiment.name}</h1>
              <ExperimentStatusBadge status={experiment.status} />
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-1.5">
              {experiment.organism && (
                <span className="flex items-center space-x-1">
                  <Dna className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{experiment.organism}</span>
                </span>
              )}
              {experiment.condition_type && (
                <span className="flex items-center space-x-1">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{experiment.condition_type}</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
