import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = "",
  title,
  description,
  action,
}) => {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm ${className}`}>
      {(title || description || action) && (
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
          <div>
            {title && <h3 className="text-base font-semibold text-slate-100">{title}</h3>}
            {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
