import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "pass" | "warning" | "error" | "neutral" | "info";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "neutral",
  className = "",
}) => {
  const variants = {
    pass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    error: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    neutral: "bg-slate-800 text-slate-300 border-slate-700",
    info: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
};
