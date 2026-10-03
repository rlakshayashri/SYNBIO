"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Play, RefreshCw, AlertCircle, ShieldCheck, Calculator } from "lucide-react";
import { Dataset, DatasetPreviewResponse } from "../../../lib/types/dataset";
import { ValidationResult } from "../../../lib/types/validation";
import { DescriptiveStatisticsResult } from "../../../lib/types/statistics";
import { getDataset, getDatasetPreview } from "../../../lib/api/datasets";
import { validateDataset } from "../../../lib/api/validation";
import { calculateDescriptiveStatistics } from "../../../lib/api/statistics";
import { DatasetMetadataCard } from "../../../components/datasets/DatasetMetadataCard";
import { DataPreviewTable } from "../../../components/datasets/DataPreviewTable";
import { ValidationSummaryCard } from "../../../components/validation/ValidationSummaryCard";
import { ValidationDetailsTabs } from "../../../components/validation/ValidationDetailsTabs";
import { DescriptiveStatisticsCard } from "../../../components/statistics/DescriptiveStatisticsCard";
import { VisualizationPanel } from "../../../components/visualization/VisualizationPanel";
import { StatisticalAnalysisPanel } from "../../../components/statistics/StatisticalAnalysisPanel";
import { Button } from "../../../components/ui/Button";

export default function DatasetDetailPage() {
  const params = useParams();
  const datasetId = params?.id as string;

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DatasetPreviewResponse | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [statistics, setStatistics] = useState<DescriptiveStatisticsResult | null>(null);

  const [loadingDataset, setLoadingDataset] = useState(true);
  const [loadingPreview, setLoadingPreview] = useState(true);
  const [validating, setValidating] = useState(false);
  const [calculatingStats, setCalculatingStats] = useState(false);

  const [errorDataset, setErrorDataset] = useState<string | null>(null);
  const [errorPreview, setErrorPreview] = useState<string | null>(null);
  const [errorValidation, setErrorValidation] = useState<string | null>(null);
  const [errorStatistics, setErrorStatistics] = useState<string | null>(null);

  // Load Dataset Metadata & Preview
  const loadDatasetData = async () => {
    if (!datasetId) return;

    setLoadingDataset(true);
    setLoadingPreview(true);
    setErrorDataset(null);
    setErrorPreview(null);

    try {
      const data = await getDataset(datasetId);
      setDataset(data);
    } catch (err: any) {
      setErrorDataset(err.detail || "Unable to load dataset metadata.");
    } finally {
      setLoadingDataset(false);
    }

    try {
      const previewData = await getDatasetPreview(datasetId, 10);
      setPreview(previewData);
    } catch (err: any) {
      setErrorPreview(err.detail || "Unable to load dataset preview.");
    } finally {
      setLoadingPreview(false);
    }
  };

  useEffect(() => {
    loadDatasetData();
  }, [datasetId]);

  // Run Data Validation Action
  const handleRunValidation = async () => {
    if (!datasetId) return;

    setValidating(true);
    setErrorValidation(null);

    try {
      const result = await validateDataset(datasetId);
      setValidation(result);
    } catch (err: any) {
      setErrorValidation(err.detail || "Validation execution failed. Please try again.");
    } finally {
      setValidating(false);
    }
  };

  // Calculate Descriptive Statistics Action
  const handleCalculateStatistics = async () => {
    if (!datasetId) return;

    setCalculatingStats(true);
    setErrorStatistics(null);

    try {
      const result = await calculateDescriptiveStatistics(datasetId);
      setStatistics(result);
    } catch (err: any) {
      setErrorStatistics(err.detail || "Descriptive statistics calculation failed. Please try again.");
    } finally {
      setCalculatingStats(false);
    }
  };

  if (loadingDataset) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-32 bg-slate-900 rounded animate-pulse" />
        <div className="h-48 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (errorDataset || !dataset) {
    return (
      <div className="space-y-6">
        <Link href="/" className="inline-flex items-center text-xs text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Projects
        </Link>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center max-w-md mx-auto">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-100 mb-1">Dataset Not Found</h3>
          <p className="text-xs text-slate-400 mb-4">{errorDataset || "The requested dataset could not be found."}</p>
          <Button variant="outline" size="sm" onClick={loadDatasetData}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Navigation Topbar & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link href="/" className="inline-flex items-center text-xs text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Projects
        </Link>

        {/* Action Buttons: Run Validation & Calculate Statistics */}
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="md"
            onClick={handleRunValidation}
            isLoading={validating}
          >
            <Play className="w-4 h-4 mr-2" />
            {validation ? "Re-run Validation" : "Run Data Validation"}
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={handleCalculateStatistics}
            isLoading={calculatingStats}
          >
            <Calculator className="w-4 h-4 mr-2" />
            {statistics ? "Recalculate Statistics" : "Calculate Descriptive Statistics"}
          </Button>
        </div>
      </div>

      {/* Dataset Metadata Card */}
      <DatasetMetadataCard dataset={dataset} />

      {/* Action Error Alerts */}
      {errorValidation && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-xl text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>{errorValidation}</span>
          </div>
        </div>
      )}

      {errorStatistics && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-xl text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>{errorStatistics}</span>
          </div>
        </div>
      )}

      {/* Module 3 — Descriptive Statistics Section */}
      {statistics && (
        <div className="pt-2">
          <DescriptiveStatisticsCard report={statistics} />
        </div>
      )}

      {/* Module 4 — Scientific Visualization Section */}
      {preview && preview.columns && preview.columns.length > 0 && (
        <div className="pt-2">
          <VisualizationPanel datasetId={datasetId} columns={preview.columns} />
        </div>
      )}

      {/* Module 5 — Statistical Hypothesis Testing Section */}
      {preview && preview.columns && preview.columns.length > 0 && (
        <div className="pt-2">
          <StatisticalAnalysisPanel datasetId={datasetId} columns={preview.columns} />
        </div>
      )}

      {/* Module 2 — Data Quality Report (Validation Section) */}
      {validation ? (
        <div className="space-y-6 pt-2">
          <ValidationSummaryCard validation={validation} />
          <ValidationDetailsTabs validation={validation} />
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-800 border-dashed rounded-xl p-6 text-center">
          <ShieldCheck className="w-8 h-8 text-cyan-400/60 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-200">Data Validation Not Run</h4>
          <p className="text-xs text-slate-400 mt-1 mb-4 max-w-sm mx-auto">
            Click "Run Data Validation" to check for missing values, exact duplicate rows, data types, empty columns, and statistical IQR outliers.
          </p>
          <Button variant="outline" size="sm" onClick={handleRunValidation} isLoading={validating}>
            <Play className="w-3.5 h-3.5 mr-1" />
            Run Data Validation
          </Button>
        </div>
      )}

      {/* Data Preview Table */}
      <DataPreviewTable
        preview={preview}
        isLoading={loadingPreview}
        error={errorPreview}
      />
    </div>
  );
}
