"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Database, FileSpreadsheet, ArrowRight, RefreshCw, AlertCircle } from "lucide-react";
import { Project } from "../lib/types/project";
import { Dataset } from "../lib/types/dataset";
import { getProjects } from "../lib/api/projects";
import { getDatasets } from "../lib/api/datasets";
import { ProjectList } from "../components/projects/ProjectList";
import { CreateProjectModal } from "../components/projects/CreateProjectModal";
import { DatasetUpload } from "../components/datasets/DatasetUpload";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Fetch Projects on Mount
  const fetchProjectsList = async () => {
    setLoadingProjects(true);
    setError(null);
    try {
      const data = await getProjects();
      setProjects(data);
      if (data.length > 0 && !selectedProjectId) {
        setSelectedProjectId(data[0].id);
      }
    } catch (err: any) {
      setError(err.detail || "Unable to connect to SynDataX backend server. Ensure FastAPI is running on http://localhost:8000.");
    } finally {
      setLoadingProjects(false);
    }
  };

  useEffect(() => {
    fetchProjectsList();
  }, []);

  // Fetch Datasets when selectedProjectId changes
  const fetchDatasetsList = async (projectId: string) => {
    setLoadingDatasets(true);
    try {
      const data = await getDatasets(projectId);
      setDatasets(data);
    } catch (err: any) {
      // Failed to load datasets
    } finally {
      setLoadingDatasets(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      fetchDatasetsList(selectedProjectId);
    } else {
      setDatasets([]);
    }
  }, [selectedProjectId]);

  const handleProjectCreated = (newProject: Project) => {
    setProjects((prev) => [newProject, ...prev]);
    setSelectedProjectId(newProject.id);
  };

  const handleUploadSuccess = (newDataset: Dataset) => {
    setDatasets((prev) => [newDataset, ...prev]);
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId);

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800 rounded-2xl p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 text-xs font-semibold text-cyan-400 bg-cyan-950/80 border border-cyan-800/50 px-3 py-1 rounded-full mb-3">
              <Database className="w-3.5 h-3.5" />
              <span>Scientific Data Platform • Milestone 1</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Dataset Ingestion & Validation
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm mt-1 max-w-2xl">
              Connect raw experimental tabular datasets (.csv, .xlsx), preview schema structure, and execute automated scientific data quality validation.
            </p>
          </div>

          <Button
            variant="primary"
            onClick={() => setIsCreateModalOpen(true)}
            className="flex-shrink-0"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>

      {/* Backend Disconnected Alert */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-xl text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <Button variant="outline" size="sm" onClick={fetchProjectsList}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            Retry Connection
          </Button>
        </div>
      )}

      {/* Projects Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100">Scientific Projects</h2>
          <span className="text-xs text-slate-400">{projects.length} project(s)</span>
        </div>

        {loadingProjects ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-28 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <ProjectList
            projects={projects}
            selectedProjectId={selectedProjectId}
            onSelectProject={setSelectedProjectId}
            onOpenCreateModal={() => setIsCreateModalOpen(true)}
          />
        )}
      </section>

      {/* Active Project Workspace */}
      {selectedProject && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-4">
          {/* Upload Ingestion Column */}
          <div className="lg:col-span-5 space-y-6">
            <DatasetUpload
              projectId={selectedProject.id}
              onUploadSuccess={handleUploadSuccess}
            />
          </div>

          {/* Datasets List Column */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
                Project Datasets ({datasets.length})
              </h3>
            </div>

            {loadingDatasets ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <div key={i} className="h-20 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : datasets.length === 0 ? (
              <Card className="text-center py-10">
                <p className="text-xs text-slate-400">
                  No datasets uploaded to <span className="font-semibold text-slate-200">{selectedProject.name}</span> yet.
                </p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Upload a CSV or XLSX file on the left to begin analysis.
                </p>
              </Card>
            ) : (
              <div className="space-y-3">
                {datasets.map((dataset) => (
                  <Link key={dataset.id} href={`/datasets/${dataset.id}`}>
                    <div className="p-4 bg-slate-900 border border-slate-800 hover:border-cyan-500/50 rounded-xl transition-all hover:bg-slate-900/80 group flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors">
                            {dataset.name}
                          </h4>
                          <Badge variant="info">{dataset.file_type.toUpperCase()}</Badge>
                        </div>
                        <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-1">
                          <span>{dataset.file_name}</span>
                          <span>•</span>
                          <span>{dataset.row_count} rows</span>
                          <span>•</span>
                          <span>{dataset.column_count} cols</span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 text-xs text-slate-400 group-hover:text-cyan-400">
                        <span>View Details</span>
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onProjectCreated={handleProjectCreated}
      />
    </div>
  );
}
