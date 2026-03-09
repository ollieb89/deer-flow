"use client";

import {
  Activity,
  CheckCircle2,
  Clock,
  FileOutput,
} from "lucide-react";

import type { DashboardStats } from "@/core/dashboard";
import { cn } from "@/lib/utils";

import { StatCard } from "./stat-card";

export interface StatsOverviewGridProps {
  stats: DashboardStats;
  isLoading?: boolean;
  className?: string;
}

/**
 * StatsOverviewGrid - Displays the 4 main dashboard statistics in a grid
 * Layout: 4 columns on desktop, 2 on tablet, 1 on mobile
 */
export function StatsOverviewGrid({
  stats,
  isLoading,
  className,
}: StatsOverviewGridProps) {
  const displayValue = (value: number) =>
    isLoading ? "-" : value.toString();

  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4",
        className,
      )}
    >
      <StatCard
        icon={<Activity className="size-5" />}
        label="Active Threads"
        value={displayValue(stats.activeThreads)}
        iconClassName="bg-blue-500/10 text-blue-500"
      />
      <StatCard
        icon={<Clock className="size-5" />}
        label="Pending Tasks"
        value={displayValue(stats.pendingTasks)}
        iconClassName="bg-amber-500/10 text-amber-500"
      />
      <StatCard
        icon={<CheckCircle2 className="size-5" />}
        label="Completed Today"
        value={displayValue(stats.completedToday)}
        iconClassName="bg-green-500/10 text-green-500"
      />
      <StatCard
        icon={<FileOutput className="size-5" />}
        label="Artifacts"
        value={displayValue(stats.artifactsGenerated)}
        iconClassName="bg-purple-500/10 text-purple-500"
      />
    </div>
  );
}
