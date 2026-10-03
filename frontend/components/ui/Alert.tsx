import React from "react";
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from "lucide-react";

interface AlertProps {
  type?: "success" | "warning" | "error" | "info";
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  type = "info",
  title,
  children,
  className = "",
}) => {
  const styles = {
    success: {
      bg: "bg-emerald-950/40 border-emerald-800/50 text-emerald-300",
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />,
    },
    warning: {
      bg: "bg-amber-950/40 border-amber-800/50 text-amber-300",
      icon: <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />,
    },
    error: {
      bg: "bg-rose-950/40 border-rose-800/50 text-rose-300",
      icon: <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />,
    },
    info: {
      bg: "bg-cyan-950/40 border-cyan-800/50 text-cyan-300",
      icon: <Info className="w-5 h-5 text-cyan-400 flex-shrink-0" />,
    },
  };

  const current = styles[type];

  return (
    <div className={`flex gap-3 p-4 rounded-lg border ${current.bg} ${className}`}>
      {current.icon}
      <div className="text-sm">
        {title && <h4 className="font-semibold mb-1">{title}</h4>}
        <div>{children}</div>
      </div>
    </div>
  );
};
