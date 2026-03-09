"use client";

import Link from "next/link";
import {
  CheckCircle2,
  Circle,
  Loader2,
  MinusCircle,
} from "lucide-react";

import type { ThreadWithStatus } from "@/core/dashboard";
import { cn } from "@/lib/utils";

export interface ThreadStatusCardProps {
  thread: ThreadWithStatus;
  className?: string;
}

/**
 * ThreadStatusCard - Displays a single thread with status and progress
 * Shows: Title, status badge, progress bar, todo count
 */
export function ThreadStatusCard({
  thread,
  className,
}: ThreadStatusCardProps) {
  const statusConfig = {
    active: {
      icon: Loader2,
      label: "Active",
      className: "text-blue-500",
      iconClassName: "bg-blue-500/10",
      animate: "animate-spin",
    },
    idle: {
      icon: MinusCircle,
      label: "Idle",
      className: "text-gray-500",
      iconClassName: "bg-gray-500/10",
      animate: "",
    },
    completed: {
      icon: CheckCircle2,
      label: "Completed",
      className: "text-green-500",
      iconClassName: "bg-green-500/10",
      animate: "",
    },
  };

  const config = statusConfig[thread.status];
  const StatusIcon = config.icon;

  return (
    <Link
      href={`/workspace/chats/${thread.thread_id}`}
      className={cn(
        "bg-card hover:bg-accent/50 group block rounded-lg border p-3 transition-colors",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        {/* Status Icon */}
        <div
          className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-md",
            config.iconClassName,
          )}
        >
          <StatusIcon className={cn("size-4", config.className, config.animate)} />
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Title */}
          <h4 className="truncate text-sm font-medium">{thread.title}</h4>

          {/* Status Badge & Todo Count */}
          <div className="mt-1 flex items-center gap-2">
            <span className={cn("text-xs", config.className)}>
              {config.label}
            </span>
            {thread.todoCount > 0 && (
              <>
                <span className="text-muted-foreground">•</span>
                <span className="text-muted-foreground text-xs">
                  {thread.completedTodos}/{thread.todoCount} tasks
                </span>
              </>
            )}
          </div>

          {/* Progress Bar */}
          {thread.todoCount > 0 && (
            <div className="mt-2">
              <div className="bg-secondary h-1.5 w-full rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    thread.status === "completed"
                      ? "bg-green-500"
                      : thread.status === "active"
                        ? "bg-blue-500"
                        : "bg-gray-400",
                  )}
                  style={{ width: `${thread.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
