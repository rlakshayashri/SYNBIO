"use client";

import React, { useState } from "react";
import { FlaskConical, Plus, Trash2, X } from "lucide-react";
import { Button } from "../ui/Button";
import { ExperimentCreate, ExperimentalGroupCreate } from "../../lib/types/experiment";

interface CreateExperimentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ExperimentCreate) => Promise<void>;
  projectId: string;
  datasetId?: string;
}

export const CreateExperimentModal: React.FC<CreateExperimentModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  projectId,
  datasetId,
}) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [organism, setOrganism] = useState("");
  const [conditionType, setConditionType] = useState("");
  const [notes, setNotes] = useState("");

  const [groups, setGroups] = useState<ExperimentalGroupCreate[]>([
    { name: "Control Group", group_code: "CTRL", is_control: true, replicates: [{ replicate_name: "Rep_1" }] },
    { name: "Treatment 1", group_code: "TRT_1", is_control: false, replicates: [{ replicate_name: "Rep_1" }] },
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAddGroup = () => {
    setGroups([
      ...groups,
      {
        name: `Group ${groups.length + 1}`,
        group_code: `GRP_${groups.length + 1}`,
        is_control: false,
        replicates: [{ replicate_name: "Rep_1" }],
      },
    ]);
  };

  const handleRemoveGroup = (index: number) => {
    if (groups.length <= 1) return;
    setGroups(groups.filter((_, i) => i !== index));
  };

  const handleGroupChange = (index: number, field: keyof ExperimentalGroupCreate, value: any) => {
    const updated = [...groups];
    updated[index] = { ...updated[index], [field]: value };
    setGroups(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Experiment name is required.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onSubmit({
        project_id: projectId,
        dataset_id: datasetId || null,
        name: name.trim(),
        description: description.trim() || undefined,
        organism: organism.trim() || undefined,
        condition_type: conditionType.trim() || undefined,
        notes: notes.trim() || undefined,
        groups,
      });
      onClose();
    } catch (err: any) {
      setError(err.detail || err.message || "Failed to create experiment.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-6 my-8">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <FlaskConical className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Create New Experiment</h3>
              <p className="text-xs text-slate-400">Define experimental context, conditions, and group parameters.</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-xl text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Experiment Name *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Temperature Sensitivity Assay"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Organism / System</label>
              <input
                type="text"
                value={organism}
                onChange={(e) => setOrganism(e.target.value)}
                placeholder="e.g. E. coli K-12, HeLa"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Condition Variable</label>
              <input
                type="text"
                value={conditionType}
                onChange={(e) => setConditionType(e.target.value)}
                placeholder="e.g. Temperature, Concentration"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Description</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of biological goals and parameters..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Initial Experimental Groups Section */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-200">Experimental Groups</label>
              <Button type="button" variant="outline" size="sm" onClick={handleAddGroup}>
                <Plus className="w-3.5 h-3.5 mr-1" /> Add Group
              </Button>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {groups.map((group, idx) => (
                <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center gap-3">
                  <input
                    type="text"
                    value={group.name}
                    onChange={(e) => handleGroupChange(idx, "name", e.target.value)}
                    placeholder="Group Name"
                    className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-100"
                  />
                  <input
                    type="text"
                    value={group.group_code}
                    onChange={(e) => handleGroupChange(idx, "group_code", e.target.value)}
                    placeholder="Code (CTRL)"
                    className="w-24 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-100"
                  />
                  <label className="flex items-center space-x-1 text-xs text-slate-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={group.is_control}
                      onChange={(e) => handleGroupChange(idx, "is_control", e.target.checked)}
                      className="rounded border-slate-800 bg-slate-900 text-cyan-600 focus:ring-0"
                    />
                    <span>Control</span>
                  </label>
                  {groups.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveGroup(idx)}
                      className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-3 border-t border-slate-800 pt-4 mt-6">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={loading}>
              Create Experiment
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
