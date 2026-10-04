"use client";

import React from "react";
import { Dna, FlaskConical, Layers, ListChecks } from "lucide-react";
import { Experiment } from "../../lib/types/experiment";

interface ExperimentCardProps {
  experiment: Experiment;
  onSelect?: (experiment: Experiment) => void;
  isSelected?: boolean;
}

export const ExperimentCard: React.FC<ExperimentCardProps> = ({
  experiment,
  onSelect,
  isSelected,
}) => {
  return (
    <div
      onClick={() => onSelect && onSelect(experiment)}
      className={`p-4 rounded-xl border transition-all cursor-pointer ${
        isSelected
          ? "bg-slate-900 border-cyan-500/80 shadow-lg shadow-cyan-950/40"
          : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <FlaskConical className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-100">{experiment.name}</h4>
            <div className="flex items-center space-x-3 text-xs text-slate-400 mt-0.5">
              {experiment.organism && (
                <span className="flex items-center space-x-1">
                  <Dna className="w-3 h-3 text-emerald-400" />
                  <span>{experiment.organism}</span>
                </span>
              )}
              {experiment.condition_type && (
                <span className="flex items-center space-x-1">
                  <Layers className="w-3 h-3 text-cyan-400" />
                  <span>{experiment.condition_type}</span>
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
            {experiment.groups?.length || 0} Groups
          </span>
          <span className="px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/60 text-cyan-400 font-medium">
            {experiment.comparisons?.length || 0} Comparisons
          </span>
        </div>
      </div>

      {experiment.description && (
        <p className="text-xs text-slate-400 mt-3 line-clamp-2">{experiment.description}</p>
      )}
    </div>
  );
};
