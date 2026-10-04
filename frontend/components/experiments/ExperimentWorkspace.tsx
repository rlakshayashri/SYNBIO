import React, { useState } from "react";
import { ExperimentWorkspaceResponse } from "../../lib/types/experiment";
import { ExperimentHeader } from "./ExperimentHeader";
import { ExperimentWorkspaceNav, WorkspaceTab } from "./ExperimentWorkspaceNav";
import { ExperimentOverviewTab } from "./ExperimentOverviewTab";
import { ExperimentGroupsTab } from "./tabs/ExperimentGroupsTab";
import { ExperimentDatasetsTab } from "./tabs/ExperimentDatasetsTab";
import { WorkspacePlaceholderTab } from "./WorkspacePlaceholderTab";

interface ExperimentWorkspaceProps {
  workspace: ExperimentWorkspaceResponse;
  onRefreshWorkspace?: () => void;
}

export const ExperimentWorkspace: React.FC<ExperimentWorkspaceProps> = ({
  workspace,
  onRefreshWorkspace = () => {},
}) => {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("overview");
  const { experiment, attached_datasets, groups, comparisons, analyses } = workspace;

  return (
    <div className="space-y-6">
      {/* Header */}
      <ExperimentHeader experiment={experiment} />

      {/* Navigation */}
      <ExperimentWorkspaceNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        attachedDatasetsCount={attached_datasets.length}
        groupsCount={groups.length}
        comparisonsCount={comparisons.length}
        analysesCount={analyses.length}
      />

      {/* Tab Panels */}
      <div>
        {activeTab === "overview" && <ExperimentOverviewTab workspace={workspace} />}
        {activeTab === "groups" && (
          <ExperimentGroupsTab
            workspace={workspace}
            onRefreshWorkspace={onRefreshWorkspace}
          />
        )}
        {activeTab === "datasets" && (
          <ExperimentDatasetsTab
            workspace={workspace}
            onRefreshWorkspace={onRefreshWorkspace}
          />
        )}
        {activeTab === "validation" && (
          <WorkspacePlaceholderTab
            title="Data Validation & Quality Checks"
            description="Inspect data missingness, detected data types, empty columns, and IQR outliers."
          />
        )}
        {activeTab === "statistics" && (
          <WorkspacePlaceholderTab
            title="Descriptive Statistics"
            description="Review column-level summary metrics (mean, median, std error, min/max, IQR, CV)."
          />
        )}
        {activeTab === "visualizations" && (
          <WorkspacePlaceholderTab
            title="Scientific Visualizations"
            description="Generate interactive histograms, scatter plots, box plots, and bar charts."
          />
        )}
        {activeTab === "comparisons" && (
          <WorkspacePlaceholderTab
            title="Group Comparisons"
            description="Execute parametric and non-parametric hypothesis tests (Welch t-test, ANOVA, Mann-Whitney U, Kruskal-Wallis)."
          />
        )}
        {activeTab === "results" && (
          <WorkspacePlaceholderTab
            title="Unified Scientific Results Timeline"
            description="Chronological history of all validation, statistical, and group comparison outputs with full scientific provenance."
          />
        )}
      </div>
    </div>
  );
};
