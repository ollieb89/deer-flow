"use client";

import {
  CheckCircle2,
  Circle,
  Loader2,
} from "lucide-react";

import type { SubtaskInfo } from "@/core/dashboard";
import { cn } from "@/lib/utils";

export interface SubtaskProgressCardProps {
  subtask: SubtaskInfo;
  className?: string;
}

/**
 * SubtaskProgressCard - Displays a single subtask with its status
 * Shows: Description, parent thread, status indicator
 */
export function SubtaskProgressCard({
  subtask,
  className,
}: SubtaskProgressCardProps) {
  const statusConfig: Record<
    SubtaskInfo["status"],
    {
      icon: React.ComponentType<{ className?: string }>;
      label: string;
      className: string;
      iconClassName: string;
      animate?: string;
    }
  > = {
    pending: {
      icon: Circle,
      label: "Pending",
      className: "text-gray-400",
      iconClassName: "bg-gray-400/10",
    },
    in_progress: {
      icon: Loader2,
      label: "In Progress",
      className: "text-blue-500",
      iconClassName: "bg-blue-500/10",
      animate: "animate-spin",
    },
    completed: {
      icon: CheckCircle2,
      label: "Completed",
      className: "text-green-500",
      iconClassName: "bg-green-500/10",
    },
  };

  const config = statusConfig[subtask.status];
  const StatusIcon = config.icon;

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border bg-card/50 p-3",
        className,
      )}
    >
      {/* Status Icon */}
      <div
        className={cn(
          "flex size-8 shrink-0 items-center justify-center rounded-md",
          config.iconClassName,
        )}
      >
        <StatusIcon
          className={cn("size-4", config.className, config.animate ?? "")}
        />
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        {/* Description */}
        <p className="text-sm font-medium line-clamp-2">
          {subtask.description}
        </p>

        {/* Thread Reference */}
        <p className="text-muted-foreground mt-1 truncate text-xs">
          in "{subtask.threadTitle}"
        </p>

        {/* Status Badge */}
        <div className="mt-2">
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
              config.iconClassName,
              config.className,
            )}
          >
            {config.label}
          </span>
        </div>
      </div>
    </div>
  );
}
