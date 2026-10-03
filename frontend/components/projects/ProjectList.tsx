import React from "react";
import { Folder, Calendar, ArrowRight } from "lucide-react";
import { Project } from "../../lib/types/project";
import { Card } from "../ui/Card";

interface ProjectListProps {
  projects: Project[];
  selectedProjectId: string | null;
  onSelectProject: (id: string) => void;
  onOpenCreateModal: () => void;
}

export const ProjectList: React.FC<ProjectListProps> = ({
  projects,
  selectedProjectId,
  onSelectProject,
  onOpenCreateModal,
}) => {
  if (projects.length === 0) {
    return (
      <Card className="text-center py-12">
        <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-3 text-slate-400">
          <Folder className="w-6 h-6 text-cyan-400" />
        </div>
        <h3 className="text-base font-medium text-slate-200">No Projects Found</h3>
        <p className="text-xs text-slate-400 mt-1 mb-4 max-w-sm mx-auto">
          Create your first scientific project container to begin uploading datasets.
        </p>
        <button
          onClick={onOpenCreateModal}
          className="inline-flex items-center px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-medium rounded-lg transition-colors"
        >
          Create Project
        </button>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects.map((project) => {
        const isSelected = project.id === selectedProjectId;
        return (
          <div
            key={project.id}
            onClick={() => onSelectProject(project.id)}
            className={`p-4 rounded-xl border transition-all cursor-pointer relative ${
              isSelected
                ? "bg-cyan-950/30 border-cyan-500/80 ring-1 ring-cyan-500/50"
                : "bg-slate-900 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80"
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className={`p-2 rounded-lg ${isSelected ? "bg-cyan-600/20 text-cyan-400" : "bg-slate-800 text-slate-400"}`}>
                  <Folder className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-100 line-clamp-1">{project.name}</h4>
                  <div className="flex items-center text-[11px] text-slate-400 mt-0.5 space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>{new Date(project.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              <ArrowRight className={`w-4 h-4 transition-transform ${isSelected ? "text-cyan-400 translate-x-1" : "text-slate-600"}`} />
            </div>

            {project.description && (
              <p className="text-xs text-slate-400 mt-3 line-clamp-2 pl-0.5">
                {project.description}
              </p>
            )}

            {isSelected && (
              <div className="mt-3 pt-2 border-t border-cyan-900/50 text-[11px] text-cyan-400 font-medium flex items-center justify-between">
                <span>Active Project</span>
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
