"use client";

import { MessageSquare } from "lucide-react";

import type { ThreadWithStatus } from "@/core/dashboard";
import { cn } from "@/lib/utils";

import { ThreadStatusCard } from "./thread-status-card";

export interface ActiveThreadsPanelProps {
  threads: ThreadWithStatus[];
  isLoading?: boolean;
  className?: string;
}

/**
 * ActiveThreadsPanel - Displays a scrollable list of active threads
 * Shows up to 10 most recently updated threads
 */
export function ActiveThreadsPanel({
  threads,
  isLoading,
  className,
}: ActiveThreadsPanelProps) {
  return (
    <div
      className={cn(
        "bg-card flex flex-col rounded-lg border",
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="text-muted-foreground size-4" />
          <h3 className="font-semibold">Active Threads</h3>
        </div>
        <span className="text-muted-foreground text-xs">
          {isLoading ? "-" : threads.length} threads
        </span>
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-auto p-3">
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="bg-muted h-20 animate-pulse rounded-lg"
              />
            ))}
          </div>
        ) : threads.length === 0 ? (
          // Empty state
          <div className="text-muted-foreground flex h-32 flex-col items-center justify-center text-center">
            <MessageSquare className="mb-2 size-8 opacity-50" />
            <p className="text-sm">No active threads</p>
            <p className="text-xs opacity-70">
              Start a new chat to see it here
            </p>
          </div>
        ) : (
          // Thread list
          <div className="space-y-2">
            {threads.map((thread) => (
              <ThreadStatusCard key={thread.thread_id} thread={thread} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
