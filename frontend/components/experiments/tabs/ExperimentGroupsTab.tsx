"use client";

import React, { useState } from "react";
import { Plus, Users, Shield, Tag, FileText, AlertCircle, RefreshCw, Layers } from "lucide-react";
import { ExperimentalGroup, ExperimentWorkspaceResponse } from "../../../lib/types/experiment";
import { addExperimentalGroup, addReplicate } from "../../../lib/api/experiments";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";
import { Badge } from "../../ui/Badge";

interface ExperimentGroupsTabProps {
  workspace: ExperimentWorkspaceResponse;
  onRefreshWorkspace: () => void;
}

export const ExperimentGroupsTab: React.FC<ExperimentGroupsTabProps> = ({
  workspace,
  onRefreshWorkspace,
}) => {
  const { experiment, groups } = workspace;

  const [isAddGroupOpen, setIsAddGroupOpen] = useState(false);
  const [addingGroup, setAddingGroup] = useState(false);
  const [groupError, setGroupError] = useState<string | null>(null);

  const [groupName, setGroupName] = useState("");
  const [groupCode, setGroupCode] = useState("");
  const [isControl, setIsControl] = useState(false);
  const [groupDescription, setGroupDescription] = useState("");

  const [activeReplicateGroupId, setActiveReplicateGroupId] = useState<string | null>(null);
  const [replicateName, setReplicateName] = useState("");
  const [sampleIdentifier, setSampleIdentifier] = useState("");
  const [replicateType, setReplicateType] = useState<string>("biological");
  const [addingReplicate, setAddingReplicate] = useState(false);
  const [replicateError, setReplicateError] = useState<string | null>(null);

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupName.trim() || !groupCode.trim()) {
      setGroupError("Group name and group code are required.");
      return;
    }

    setAddingGroup(true);
    setGroupError(null);

    try {
      await addExperimentalGroup(experiment.id, {
        name: groupName.trim(),
        group_code: groupCode.trim().toUpperCase(),
        is_control: isControl,
        description: groupDescription.trim() || undefined,
      });

      // Reset form & close
      setGroupName("");
      setGroupCode("");
      setIsControl(false);
      setGroupDescription("");
      setIsAddGroupOpen(false);

      // Refresh workspace
      onRefreshWorkspace();
    } catch (err: any) {
      setGroupError(err.detail || "Failed to create experimental group.");
    } finally {
      setAddingGroup(false);
    }
  };

  const handleCreateReplicate = async (groupId: string, e: React.FormEvent) => {
    e.preventDefault();
    if (!replicateName.trim()) {
      setReplicateError("Replicate name is required.");
      return;
    }

    setAddingReplicate(true);
    setReplicateError(null);

    try {
      await addReplicate(groupId, {
        replicate_name: replicateName.trim(),
        sample_identifier: sampleIdentifier.trim() || undefined,
        replicate_type: replicateType,
      });

      // Reset form
      setReplicateName("");
      setSampleIdentifier("");
      setReplicateType("biological");
      setActiveReplicateGroupId(null);

      // Refresh workspace
      onRefreshWorkspace();
    } catch (err: any) {
      setReplicateError(err.detail || "Failed to add replicate sample.");
    } finally {
      setAddingReplicate(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
            <Users className="w-4 h-4 text-cyan-400" />
            <span>Experimental Groups & Replicates</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Define study arms/conditions (e.g. WT-Control, Knockout) and register sample replicates.
          </p>
        </div>

        <Button
          size="sm"
          onClick={() => {
            setIsAddGroupOpen(true);
            setGroupError(null);
          }}
        >
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          Add Group
        </Button>
      </div>

      {/* Add Group Modal / Inline Form */}
      {isAddGroupOpen && (
        <Card className="p-5 bg-slate-900 border-cyan-500/40 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="text-sm font-bold text-cyan-400 flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Create Experimental Group</span>
            </h4>
            <button
              onClick={() => setIsAddGroupOpen(false)}
              className="text-xs text-slate-500 hover:text-slate-300"
            >
              Cancel
            </button>
          </div>

          {groupError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{groupError}</span>
            </div>
          )}

          <form onSubmit={handleCreateGroup} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block font-medium text-slate-300 mb-1">Group Name *</label>
                <input
                  type="text"
                  placeholder="e.g. WT Control 37C"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="block font-medium text-slate-300 mb-1">Group Code *</label>
                <input
                  type="text"
                  placeholder="e.g. CTRL (used in dataset group_column)"
                  value={groupCode}
                  onChange={(e) => setGroupCode(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 uppercase"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block font-medium text-slate-300 mb-1">Description (Optional)</label>
              <input
                type="text"
                placeholder="Brief description of this experimental arm"
                value={groupDescription}
                onChange={(e) => setGroupDescription(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center space-x-2 pt-1">
              <input
                type="checkbox"
                id="isControl"
                checked={isControl}
                onChange={(e) => setIsControl(e.target.checked)}
                className="rounded border-slate-800 bg-slate-950 text-cyan-500 focus:ring-0"
              />
              <label htmlFor="isControl" className="text-slate-300 font-medium cursor-pointer">
                Designate as Baseline / Control Group
              </label>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setIsAddGroupOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={addingGroup}>
                {addingGroup ? "Saving..." : "Save Group"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Groups List */}
      {groups.length === 0 ? (
        <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
          <Users className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h4 className="text-sm font-semibold text-slate-300">No Experimental Groups</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Define at least two experimental groups (e.g. CTRL and TRT) to enable scientific group comparisons.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {groups.map((group) => (
            <Card key={group.id} className="p-5 bg-slate-900/60 border-slate-800 space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <h4 className="text-sm font-bold text-slate-100">{group.name}</h4>
                    <span className="px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/60 text-cyan-400 text-xs font-mono font-medium">
                      CODE: {group.group_code}
                    </span>
                    {group.is_control && (
                      <Badge variant="pass">Control Group</Badge>
                    )}
                  </div>
                  {group.description && (
                    <p className="text-xs text-slate-400">{group.description}</p>
                  )}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setActiveReplicateGroupId(
                      activeReplicateGroupId === group.id ? null : group.id
                    );
                    setReplicateError(null);
                  }}
                >
                  <Plus className="w-3.5 h-3.5 mr-1" />
                  Add Replicate
                </Button>
              </div>

              {/* Add Replicate Form */}
              {activeReplicateGroupId === group.id && (
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-cyan-400">
                      Add Sample Replicate to {group.name}
                    </span>
                    <button
                      onClick={() => setActiveReplicateGroupId(null)}
                      className="text-xs text-slate-500 hover:text-slate-300"
                    >
                      Close
                    </button>
                  </div>

                  {replicateError && (
                    <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                      {replicateError}
                    </div>
                  )}

                  <form
                    onSubmit={(e) => handleCreateReplicate(group.id, e)}
                    className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs"
                  >
                    <div>
                      <input
                        type="text"
                        placeholder="Replicate Name (e.g. Rep_1)"
                        value={replicateName}
                        onChange={(e) => setReplicateName(e.target.value)}
                        className="w-full px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                        required
                      />
                    </div>

                    <div>
                      <input
                        type="text"
                        placeholder="Sample Identifier (Optional)"
                        value={sampleIdentifier}
                        onChange={(e) => setSampleIdentifier(e.target.value)}
                        className="w-full px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="flex items-center space-x-2">
                      <select
                        value={replicateType}
                        onChange={(e) => setReplicateType(e.target.value)}
                        className="flex-1 px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                      >
                        <option value="biological">Biological</option>
                        <option value="technical">Technical</option>
                      </select>

                      <Button type="submit" size="sm" disabled={addingReplicate}>
                        {addingReplicate ? "Saving..." : "Save"}
                      </Button>
                    </div>
                  </form>
                </div>
              )}

              {/* Replicates Table */}
              <div className="pt-2">
                <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center justify-between">
                  <span>Registered Replicates ({group.replicates?.length || 0})</span>
                </div>

                {group.replicates && group.replicates.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                    {group.replicates.map((rep) => (
                      <div
                        key={rep.id}
                        className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80 flex items-center justify-between text-xs"
                      >
                        <div>
                          <p className="font-semibold text-slate-200">{rep.replicate_name}</p>
                          {rep.sample_identifier && (
                            <p className="text-[11px] text-slate-400">{rep.sample_identifier}</p>
                          )}
                        </div>
                        <span className="px-2 py-0.5 rounded text-[10px] uppercase font-medium bg-slate-800 text-slate-400">
                          {rep.replicate_type}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No replicate samples registered yet.</p>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
