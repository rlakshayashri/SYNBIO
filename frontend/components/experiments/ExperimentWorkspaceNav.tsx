import React from "react";
import { LayoutDashboard, Users, Database, ShieldCheck, Calculator, LineChart, GitCompare, FileCode } from "lucide-react";

export type WorkspaceTab =
  | "overview"
  | "groups"
  | "datasets"
  | "validation"
  | "statistics"
  | "visualizations"
  | "comparisons"
  | "results";

interface ExperimentWorkspaceNavProps {
  activeTab: WorkspaceTab;
  onTabChange: (tab: WorkspaceTab) => void;
  attachedDatasetsCount?: number;
  groupsCount?: number;
  comparisonsCount?: number;
  analysesCount?: number;
}

export const ExperimentWorkspaceNav: React.FC<ExperimentWorkspaceNavProps> = ({
  activeTab,
  onTabChange,
  attachedDatasetsCount = 0,
  groupsCount = 0,
  comparisonsCount = 0,
  analysesCount = 0,
}) => {
  const tabs: { id: WorkspaceTab; label: string; icon: React.FC<{ className?: string }>; count?: number }[] = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "groups", label: "Groups", icon: Users, count: groupsCount },
    { id: "datasets", label: "Datasets", icon: Database, count: attachedDatasetsCount },
    { id: "validation", label: "Validation", icon: ShieldCheck },
    { id: "statistics", label: "Statistics", icon: Calculator },
    { id: "visualizations", label: "Visualizations", icon: LineChart },
    { id: "comparisons", label: "Comparisons", icon: GitCompare, count: comparisonsCount },
    { id: "results", label: "Results", icon: FileCode, count: analysesCount },
  ];

  return (
    <div className="border-b border-slate-800 overflow-x-auto scrollbar-none">
      <nav className="flex space-x-1 p-1 bg-slate-900/40 rounded-xl">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
                isActive
                  ? "bg-cyan-600/20 text-cyan-400 border border-cyan-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.count !== undefined && tab.count > 0 && (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                    isActive ? "bg-cyan-500/20 text-cyan-300" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
};
