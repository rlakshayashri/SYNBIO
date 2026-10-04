"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertCircle, ArrowLeft, RefreshCw, FlaskConical } from "lucide-react";
import { ExperimentWorkspaceResponse } from "../../../lib/types/experiment";
import { getExperimentWorkspace } from "../../../lib/api/experiments";
import { ExperimentWorkspace } from "../../../components/experiments/ExperimentWorkspace";
import { Button } from "../../../components/ui/Button";

export default function ExperimentDetailPage() {
  const params = useParams();
  const experimentId = params?.id as string;

  const [workspace, setWorkspace] = useState<ExperimentWorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadWorkspace = async () => {
    if (!experimentId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await getExperimentWorkspace(experimentId);
      setWorkspace(data);
    } catch (err: any) {
      if (err.status === 404) {
        setError(`Experiment with ID '${experimentId}' was not found.`);
      } else {
        setError(err.detail || "Unable to load experiment workspace.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, [experimentId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-36 bg-slate-800 rounded animate-pulse" />
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 animate-pulse space-y-4">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-slate-800" />
            <div className="space-y-2 flex-1">
              <div className="h-5 bg-slate-800 rounded w-1/3" />
              <div className="h-3 bg-slate-800/60 rounded w-1/4" />
            </div>
          </div>
        </div>
        <div className="h-10 bg-slate-900/60 border border-slate-800 rounded-xl animate-pulse" />
        <div className="h-64 bg-slate-900/40 border border-slate-800 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (error || !workspace) {
    return (
      <div className="space-y-6">
        <Link
          href="/experiments"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-cyan-400 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Experiments Workbench</span>
        </Link>

        <div className="p-8 rounded-2xl bg-slate-900/60 border border-rose-500/30 text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">Unable to Load Workspace</h3>
            <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">{error || "Experiment not found."}</p>
          </div>
          <div className="pt-2 flex justify-center space-x-3">
            <Button variant="outline" size="sm" onClick={loadWorkspace}>
              <RefreshCw className="w-3.5 h-3.5 mr-2" />
              Try Again
            </Button>
            <Link href="/experiments">
              <Button variant="secondary" size="sm">
                Return to Workbench List
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <ExperimentWorkspace workspace={workspace} onRefreshWorkspace={loadWorkspace} />;
}
