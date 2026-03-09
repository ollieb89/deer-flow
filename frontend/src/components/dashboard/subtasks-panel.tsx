"use client";

import { ListTodo } from "lucide-react";

import type { SubtaskInfo } from "@/core/dashboard";
import { cn } from "@/lib/utils";

import { SubtaskProgressCard } from "./subtask-progress-card";

export interface SubtasksPanelProps {
  subtasks: SubtaskInfo[];
  isLoading?: boolean;
  className?: string;
}

/**
 * SubtasksPanel - Displays all subtasks across all threads
 * Groups by status: in_progress first, then pending, then completed
 */
export function SubtasksPanel({
  subtasks,
  isLoading,
  className,
}: SubtasksPanelProps) {
  // Sort subtasks: in_progress first, then pending, then completed
  const sortedSubtasks = [...subtasks].sort((a, b) => {
    const statusOrder = { in_progress: 0, pending: 1, completed: 2 };
    return statusOrder[a.status] - statusOrder[b.status];
  });

  // Count by status
  const inProgressCount = subtasks.filter(
    (s) => s.status === "in_progress",
  ).length;
  const pendingCount = subtasks.filter((s) => s.status === "pending").length;

  return (
    <div className={cn("bg-card flex flex-col rounded-lg border", className)}>
      {/* Header */}
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <ListTodo className="text-muted-foreground size-4" />
          <h3 className="font-semibold">Running Subtasks</h3>
        </div>
        <div className="text-muted-foreground flex items-center gap-2 text-xs">
          {inProgressCount > 0 && (
            <span className="text-blue-500">{inProgressCount} active</span>
          )}
          {pendingCount > 0 && (
            <>
              {inProgressCount > 0 && <span>•</span>}
              <span>{pendingCount} pending</span>
            </>
          )}
          {!isLoading && subtasks.length === 0 && <span>0 subtasks</span>}
        </div>
      </div>

      {/* Subtask List */}
      <div className="flex-1 overflow-auto p-3">
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="bg-muted h-24 animate-pulse rounded-lg"
              />
            ))}
          </div>
        ) : sortedSubtasks.length === 0 ? (
          // Empty state
          <div className="text-muted-foreground flex h-32 flex-col items-center justify-center text-center">
            <ListTodo className="mb-2 size-8 opacity-50" />
            <p className="text-sm">No subtasks</p>
            <p className="text-xs opacity-70">
              Subtasks appear when agents are working
            </p>
          </div>
        ) : (
          // Subtask list
          <div className="space-y-2">
            {sortedSubtasks.map((subtask) => (
              <SubtaskProgressCard key={subtask.id} subtask={subtask} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
