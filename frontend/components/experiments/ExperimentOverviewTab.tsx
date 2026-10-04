import React from "react";
import { Dna, Layers, Target, FileText, Database, FlaskConical, BarChart2, ShieldCheck, Clock } from "lucide-react";
import { ExperimentWorkspaceResponse } from "../../lib/types/experiment";
import { Card } from "../ui/Card";
import { ExperimentStatusBadge } from "./ExperimentStatusBadge";

interface ExperimentOverviewTabProps {
  workspace: ExperimentWorkspaceResponse;
}

export const ExperimentOverviewTab: React.FC<ExperimentOverviewTabProps> = ({ workspace }) => {
  const { experiment, attached_datasets, groups, comparisons, analyses } = workspace;

  return (
    <div className="space-y-6">
      {/* Quick Summary Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900/60 border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <FlaskConical className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Experimental Groups</p>
              <p className="text-lg font-bold text-slate-100">{groups.length}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/60 border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Attached Datasets</p>
              <p className="text-lg font-bold text-slate-100">{attached_datasets.length}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/60 border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <BarChart2 className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Group Comparisons</p>
              <p className="text-lg font-bold text-slate-100">{comparisons.length}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/60 border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Analyses Executed</p>
              <p className="text-lg font-bold text-slate-100">{analyses.length}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Details Card */}
      <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-6">
        <div className="flex items-start justify-between border-b border-slate-800/80 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <span>{experiment.name}</span>
            </h2>
            {experiment.description && (
              <p className="text-sm text-slate-400 mt-1">{experiment.description}</p>
            )}
          </div>
          <ExperimentStatusBadge status={experiment.status} />
        </div>

        {/* Biological & Experimental Parameters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              <Dna className="w-3.5 h-3.5 text-emerald-400" />
              <span>Model Organism</span>
            </div>
            <p className="text-slate-200 font-medium">{experiment.organism || "Not specified"}</p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Condition / Perturbation</span>
            </div>
            <p className="text-slate-200 font-medium">{experiment.condition_type || "Not specified"}</p>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>Created Date</span>
            </div>
            <p className="text-slate-200 font-medium">
              {new Date(experiment.created_at).toLocaleDateString(undefined, {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            </p>
          </div>
        </div>

        {/* Objective & Hypothesis */}
        {experiment.objective && (
          <div className="p-4 rounded-lg bg-cyan-950/20 border border-cyan-800/40">
            <div className="flex items-center space-x-2 text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-1">
              <Target className="w-3.5 h-3.5" />
              <span>Hypothesis & Objective</span>
            </div>
            <p className="text-sm text-slate-200">{experiment.objective}</p>
          </div>
        )}

        {/* Scientific Notes */}
        {experiment.notes && (
          <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              <span>Scientist Notes</span>
            </div>
            <p className="text-sm text-slate-300 whitespace-pre-line">{experiment.notes}</p>
          </div>
        )}
      </Card>
    </div>
  );
};
