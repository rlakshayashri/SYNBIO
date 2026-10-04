import React, { useState } from "react";
import Link from "next/link";
import { FlaskConical, Dna, Layers, Search, Filter, ArrowRight, Plus } from "lucide-react";
import { Experiment } from "../../lib/types/experiment";
import { Project } from "../../lib/types/project";
import { Card } from "../ui/Card";
import { ExperimentStatusBadge } from "./ExperimentStatusBadge";

interface ExperimentListProps {
  experiments: Experiment[];
  projects?: Project[];
  selectedProjectId?: string | null;
  onSelectProject?: (projectId: string | null) => void;
  onCreateExperiment?: () => void;
}

export const ExperimentList: React.FC<ExperimentListProps> = ({
  experiments,
  projects = [],
  selectedProjectId = null,
  onSelectProject,
  onCreateExperiment,
}) => {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredExperiments = experiments.filter((exp) => {
    const matchesProject = selectedProjectId ? exp.project_id === selectedProjectId : true;
    const matchesSearch =
      exp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (exp.organism && exp.organism.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (exp.condition_type && exp.condition_type.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (exp.description && exp.description.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesProject && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3 flex-1">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search experiments by name, organism, or condition..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs rounded-xl bg-slate-900 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>

          {/* Project Filter Select */}
          {projects.length > 0 && onSelectProject && (
            <div className="flex items-center space-x-2">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedProjectId || ""}
                onChange={(e) => onSelectProject(e.target.value || null)}
                className="py-2 px-3 text-xs rounded-xl bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors"
              >
                <option value="">All Projects</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {onCreateExperiment && (
          <button
            onClick={onCreateExperiment}
            className="inline-flex items-center justify-center space-x-2 px-4 py-2 text-xs font-semibold rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white transition-colors shadow-lg shadow-cyan-950/30"
          >
            <Plus className="w-4 h-4" />
            <span>New Experiment</span>
          </button>
        )}
      </div>

      {/* Experiments Grid */}
      {filteredExperiments.length === 0 ? (
        <Card className="p-12 text-center bg-slate-900/40 border-slate-800">
          <FlaskConical className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-slate-300">No experiments found</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {searchQuery || selectedProjectId
              ? "No experiments match your search criteria. Try clearing filters."
              : "Create an experiment to start structuring your biological groups, datasets, and comparisons."}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredExperiments.map((exp) => (
            <Link
              key={exp.id}
              href={`/experiments/${exp.id}`}
              className="block group"
            >
              <Card className="p-5 bg-slate-900/60 border-slate-800 hover:border-slate-700 transition-all hover:shadow-xl group-hover:bg-slate-900/90 h-full flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-9 h-9 rounded-lg bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 group-hover:border-cyan-500/50 transition-colors">
                        <FlaskConical className="w-4 h-4" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-400 transition-colors">
                          {exp.name}
                        </h3>
                        <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-0.5">
                          {exp.organism && (
                            <span className="flex items-center space-x-1">
                              <Dna className="w-3 h-3 text-emerald-400" />
                              <span>{exp.organism}</span>
                            </span>
                          )}
                          {exp.condition_type && (
                            <span className="flex items-center space-x-1">
                              <Layers className="w-3 h-3 text-cyan-400" />
                              <span>{exp.condition_type}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <ExperimentStatusBadge status={exp.status} />
                  </div>

                  {exp.description && (
                    <p className="text-xs text-slate-400 line-clamp-2">{exp.description}</p>
                  )}
                </div>

                <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-800/60 text-xs">
                  <span className="text-slate-500 text-[11px]">
                    {new Date(exp.created_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                  <span className="flex items-center space-x-1 text-cyan-400 group-hover:translate-x-0.5 transition-transform font-medium">
                    <span>Open Workbench</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
