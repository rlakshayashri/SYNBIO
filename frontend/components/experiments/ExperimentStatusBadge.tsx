import React from "react";
import { Badge } from "../ui/Badge";

interface ExperimentStatusBadgeProps {
  status?: string | null;
  className?: string;
}

export const ExperimentStatusBadge: React.FC<ExperimentStatusBadgeProps> = ({
  status = "draft",
  className = "",
}) => {
  const normalizedStatus = (status || "draft").toLowerCase();

  switch (normalizedStatus) {
    case "in_progress":
    case "in progress":
      return <Badge variant="info" className={className}>In Progress</Badge>;
    case "completed":
      return <Badge variant="pass" className={className}>Completed</Badge>;
    case "archived":
      return <Badge variant="neutral" className={className}>Archived</Badge>;
    case "draft":
    default:
      return <Badge variant="warning" className={className}>Draft</Badge>;
  }
};
