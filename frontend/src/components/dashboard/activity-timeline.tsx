"use client";

import Link from "next/link";
import {
  CheckCircle2,
  Clock,
  FileOutput,
  MessageSquare,
  Sparkles,
} from "lucide-react";

import type { ActivityItem } from "@/core/dashboard";
import { cn } from "@/lib/utils";

export interface ActivityTimelineProps {
  activities: ActivityItem[];
  isLoading?: boolean;
  className?: string;
}

/**
 * ActivityTimeline - Displays recent activity in a vertical timeline
 * Shows: Thread creation, task progress, artifact generation
 */
export function ActivityTimeline({
  activities,
  isLoading,
  className,
}: ActivityTimelineProps) {
  const getActivityIcon = (type: ActivityItem["type"]) => {
    switch (type) {
      case "thread_created":
        return <MessageSquare className="size-3.5" />;
      case "task_in_progress":
        return <Clock className="size-3.5" />;
      case "task_completed":
        return <CheckCircle2 className="size-3.5" />;
      case "artifact_generated":
        return <FileOutput className="size-3.5" />;
      case "memory_updated":
        return <Sparkles className="size-3.5" />;
      case "message_sent":
        return <MessageSquare className="size-3.5" />;
      default:
        return <MessageSquare className="size-3.5" />;
    }
  };

  const getActivityColor = (type: ActivityItem["type"]) => {
    switch (type) {
      case "thread_created":
        return "bg-blue-500 text-blue-500";
      case "task_in_progress":
        return "bg-amber-500 text-amber-500";
      case "task_completed":
        return "bg-green-500 text-green-500";
      case "artifact_generated":
        return "bg-purple-500 text-purple-500";
      case "memory_updated":
        return "bg-pink-500 text-pink-500";
      case "message_sent":
        return "bg-gray-500 text-gray-500";
      default:
        return "bg-gray-500 text-gray-500";
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={cn("bg-card flex flex-col rounded-lg border", className)}>
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Recent Activity</h3>
          <span className="text-muted-foreground text-xs">
            {isLoading ? "-" : `${activities.length} events`}
          </span>
        </div>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-auto p-4">
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <div className="bg-muted h-8 w-8 animate-pulse rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="bg-muted h-4 w-3/4 animate-pulse rounded" />
                  <div className="bg-muted h-3 w-1/4 animate-pulse rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : activities.length === 0 ? (
          // Empty state
          <div className="text-muted-foreground flex h-32 flex-col items-center justify-center text-center">
            <Clock className="mb-2 size-8 opacity-50" />
            <p className="text-sm">No recent activity</p>
            <p className="text-xs opacity-70">
              Activity will appear as you use DeerFlow
            </p>
          </div>
        ) : (
          // Timeline list
          <div className="relative space-y-4">
            {/* Timeline line */}
            <div className="absolute inset-y-0 left-4 w-px bg-border" />

            {activities.map((activity, index) => (
              <div key={activity.id} className="relative flex gap-3">
                {/* Icon */}
                <div
                  className={cn(
                    "relative z-10 flex size-8 shrink-0 items-center justify-center rounded-full border-2 bg-background",
                    getActivityColor(activity.type),
                  )}
                >
                  {getActivityIcon(activity.type)}
                </div>

                {/* Content */}
                <div className="flex-1 pt-1">
                  <p className="text-sm">{activity.title}</p>
                  <div className="mt-0.5 flex items-center gap-2 text-xs">
                    <span className="text-muted-foreground">
                      {formatTimeAgo(activity.timestamp)}
                    </span>
                    {activity.threadId && (
                      <>
                        <span className="text-muted-foreground">•</span>
                        <Link
                          href={`/workspace/chats/${activity.threadId}`}
                          className="text-primary hover:underline"
                        >
                          View thread
                        </Link>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
