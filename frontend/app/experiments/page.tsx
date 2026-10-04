"use client";

import React, { useEffect, useState } from "react";
import { FlaskConical, AlertCircle, RefreshCw } from "lucide-react";
import { Experiment } from "../../lib/types/experiment";
import { Project } from "../../lib/types/project";
import { getExperiments } from "../../lib/api/experiments";
import { getProjects } from "../../lib/api/projects";
import { ExperimentList } from "../../components/experiments/ExperimentList";
import { Button } from "../../components/ui/Button";

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [expList, projList] = await Promise.all([
        getExperiments(selectedProjectId || undefined),
        getProjects(),
      ]);
      setExperiments(expList);
      setProjects(projList);
    } catch (err: any) {
      setError(err.detail || "Unable to load experiments list.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedProjectId]);

  return (
    <div className="space-y-8">
      {/* Page Heading */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-3">
            <FlaskConical className="w-7 h-7 text-cyan-400" />
            <span>Experiments Workbench</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Experiment-centric workspace for biological group design, datasets, and scientific statistical analysis.
          </p>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-between text-rose-400 text-sm">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={loadData}>
            <RefreshCw className="w-3.5 h-3.5 mr-2" />
            Retry
          </Button>
        </div>
      )}

      {/* Loading Skeleton State */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="p-5 rounded-xl bg-slate-900/40 border border-slate-800 animate-pulse space-y-4"
            >
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-slate-800" />
                <div className="space-y-2 flex-1">
                  <div className="h-4 bg-slate-800 rounded w-3/4" />
                  <div className="h-3 bg-slate-800/60 rounded w-1/2" />
                </div>
              </div>
              <div className="h-12 bg-slate-800/40 rounded" />
            </div>
          ))}
        </div>
      ) : (
        <ExperimentList
          experiments={experiments}
          projects={projects}
          selectedProjectId={selectedProjectId}
          onSelectProject={setSelectedProjectId}
        />
      )}
    </div>
  );
}
