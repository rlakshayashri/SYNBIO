"use client";

import React, { useState } from "react";
import {
  Layers,
  Plus,
  Trash2,
  AlertCircle,
  Tag,
  CheckCircle2,
  X,
} from "lucide-react";
import { ExperimentalFactor, ExperimentalFactorCreate, FactorLevelCreate } from "../../../lib/types/factorial";
import { createExperimentalFactor, deleteExperimentalFactor } from "../../../lib/api/experiments";
import { Card } from "../../ui/Card";
import { Button } from "../../ui/Button";
import { Badge } from "../../ui/Badge";

interface FactorManagementPanelProps {
  experimentId: string;
  factors: ExperimentalFactor[];
  onRefreshFactors: () => void;
}

export const FactorManagementPanel: React.FC<FactorManagementPanelProps> = ({
  experimentId,
  factors,
  onRefreshFactors,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [factorType, setFactorType] = useState("treatment");
  const [levelNames, setLevelNames] = useState<string[]>(["Level 1", "Level 2"]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleAddLevel = () => {
    setLevelNames((prev) => [...prev, `Level ${prev.length + 1}`]);
  };

  const handleRemoveLevel = (idx: number) => {
    setLevelNames((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleLevelChange = (idx: number, val: string) => {
    setLevelNames((prev) => {
      const copy = [...prev];
      copy[idx] = val;
      return copy;
    });
  };

  const handleCreateFactor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Factor name is required.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const levelsPayload: FactorLevelCreate[] = levelNames
        .map((lvlName, i) => ({
          name: lvlName.trim(),
          order_index: i,
        }))
        .filter((lvl) => Boolean(lvl.name));

      const payload: ExperimentalFactorCreate = {
        name: name.trim(),
        description: description.trim() || undefined,
        factor_type: factorType,
        levels: levelsPayload,
      };

      await createExperimentalFactor(experimentId, payload);
      setName("");
      setDescription("");
      setLevelNames(["Level 1", "Level 2"]);
      setIsAdding(false);
      onRefreshFactors();
    } catch (err: any) {
      setError(err.detail || "Failed to create factor. Please verify name is unique in this experiment.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFactor = async (factorId: string) => {
    setDeletingId(factorId);
    setError(null);
    try {
      await deleteExperimentalFactor(experimentId, factorId);
      onRefreshFactors();
    } catch (err: any) {
      setError(err.detail || "Failed to delete factor.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <Card className="p-5 bg-slate-900/60 border-slate-800 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-xs font-bold text-slate-200 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Registered Conceptual Factors ({factors.length})</span>
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Conceptual factors represent biological or experimental variables (e.g. Genotype, Inducer) independent of specific dataset column names.
          </p>
        </div>

        {!isAdding && (
          <Button size="sm" onClick={() => setIsAdding(true)}>
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            Register Factor
          </Button>
        )}
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Factor Creation Form */}
      {isAdding && (
        <form onSubmit={handleCreateFactor} className="p-4 rounded-xl bg-slate-950 border border-cyan-500/40 space-y-4 text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-bold text-cyan-400 flex items-center space-x-1.5">
              <Tag className="w-3.5 h-3.5" />
              <span>New Experimental Factor</span>
            </span>
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="text-slate-500 hover:text-slate-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-300 mb-1">Factor Name *</label>
              <input
                type="text"
                placeholder="e.g. Genotype, Temperature, IPTG"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                required
              />
            </div>

            <div>
              <label className="block font-medium text-slate-300 mb-1">Factor Type</label>
              <select
                value={factorType}
                onChange={(e) => setFactorType(e.target.value)}
                className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="treatment">Treatment / Compound</option>
                <option value="genetic">Genetic / Strain / Strain Variant</option>
                <option value="environmental">Environmental (Temp, pH, Light)</option>
                <option value="time">Timepoint</option>
                <option value="other">Other Categorical</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-medium text-slate-300 mb-1">Description (Optional)</label>
            <input
              type="text"
              placeholder="Biological purpose or experimental definition"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Initial Levels */}
          <div className="space-y-2 pt-1 border-t border-slate-800/80">
            <div className="flex items-center justify-between">
              <label className="font-medium text-slate-300">Factor Levels ({levelNames.length})</label>
              <button
                type="button"
                onClick={handleAddLevel}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold flex items-center space-x-1"
              >
                <Plus className="w-3 h-3" />
                <span>Add Level</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {levelNames.map((lvl, idx) => (
                <div key={idx} className="flex items-center space-x-1">
                  <input
                    type="text"
                    value={lvl}
                    onChange={(e) => handleLevelChange(idx, e.target.value)}
                    placeholder={`Level ${idx + 1}`}
                    className="flex-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-cyan-500 font-mono"
                  />
                  {levelNames.length > 2 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveLevel(idx)}
                      className="text-slate-500 hover:text-rose-400 p-1"
                      title="Remove level"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
            <Button type="button" variant="secondary" size="sm" onClick={() => setIsAdding(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={loading}>
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
              {loading ? "Registering..." : "Save Factor"}
            </Button>
          </div>
        </form>
      )}

      {/* Factors List */}
      {factors.length === 0 ? (
        <div className="p-6 text-center text-xs text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800/80">
          No conceptual experimental factors registered yet. Register factors (e.g. Strain, Temperature) to associate them with factorial analyses.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {factors.map((f) => (
            <div
              key={f.id}
              className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-all space-y-2 text-xs"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-bold text-slate-100 flex items-center space-x-1.5">
                    <Tag className="w-3 h-3 text-cyan-400" />
                    <span>{f.name}</span>
                    {f.factor_type && (
                      <Badge variant="neutral" className="text-[9px] text-slate-400 ml-1">
                        {f.factor_type}
                      </Badge>
                    )}
                  </div>
                  {f.description && (
                    <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{f.description}</p>
                  )}
                </div>

                <button
                  onClick={() => handleDeleteFactor(f.id)}
                  disabled={deletingId === f.id}
                  className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                  title="Delete factor"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Levels pills */}
              {f.levels && f.levels.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800/60">
                  {f.levels.map((lvl) => (
                    <span
                      key={lvl.id}
                      className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-300 font-mono"
                    >
                      {lvl.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
