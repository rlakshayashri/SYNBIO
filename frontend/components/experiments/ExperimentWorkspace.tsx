import React, { useState } from "react";
import { ExperimentWorkspaceResponse } from "../../lib/types/experiment";
import { ExperimentHeader } from "./ExperimentHeader";
import { ExperimentWorkspaceNav, WorkspaceTab } from "./ExperimentWorkspaceNav";
import { ExperimentOverviewTab } from "./ExperimentOverviewTab";
import { ExperimentGroupsTab } from "./tabs/ExperimentGroupsTab";
import { ExperimentDatasetsTab } from "./tabs/ExperimentDatasetsTab";
import { ExperimentValidationTab } from "./tabs/ExperimentValidationTab";
import { ExperimentStatisticsTab } from "./tabs/ExperimentStatisticsTab";
import { ExperimentVisualizationsTab } from "./tabs/ExperimentVisualizationsTab";
import { ExperimentComparisonsTab } from "./tabs/ExperimentComparisonsTab";
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
          <ExperimentValidationTab workspace={workspace} />
        )}
        {activeTab === "statistics" && (
          <ExperimentStatisticsTab workspace={workspace} />
        )}
        {activeTab === "visualizations" && (
          <ExperimentVisualizationsTab workspace={workspace} />
        )}
        {activeTab === "comparisons" && (
          <ExperimentComparisonsTab
            workspace={workspace}
            onRefreshWorkspace={onRefreshWorkspace}
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
