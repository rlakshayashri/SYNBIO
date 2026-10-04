import React from "react";
import { FlaskConical, Clock } from "lucide-react";
import { Card } from "../ui/Card";

interface WorkspacePlaceholderTabProps {
  title: string;
  description: string;
}

export const WorkspacePlaceholderTab: React.FC<WorkspacePlaceholderTabProps> = ({
  title,
  description,
}) => {
  return (
    <Card className="p-8 text-center bg-slate-900/40 border-slate-800">
      <div className="w-12 h-12 rounded-xl bg-cyan-600/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mx-auto mb-4">
        <FlaskConical className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-slate-200 mb-2">{title}</h3>
      <p className="text-sm text-slate-400 max-w-md mx-auto mb-4">{description}</p>
      <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-400">
        <Clock className="w-3.5 h-3.5 text-cyan-400" />
        <span>Planned for Module 7 sub-phase integration</span>
      </div>
    </Card>
  );
};
