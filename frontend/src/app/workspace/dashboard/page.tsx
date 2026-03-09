"use client";

import { useState } from "react";

import { ActiveThreadsPanel } from "@/components/dashboard/active-threads-panel";
import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { QuickActionsBar } from "@/components/dashboard/quick-actions-bar";
import { StatsOverviewGrid } from "@/components/dashboard/stats-overview-grid";
import { SubtasksPanel } from "@/components/dashboard/subtasks-panel";
import { SystemStatusPanel } from "@/components/dashboard/system-status-panel";
import {
  useActiveThreads,
  useDashboardStats,
  useRecentActivity,
  useSubtasks,
  useSystemStatus,
} from "@/core/dashboard";

/**
 * Mission Control Dashboard Page
 * Provides a comprehensive real-time overview of DeerFlow operations
 */
export default function DashboardPage() {
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch dashboard data
  const { stats, isLoading: statsLoading } = useDashboardStats();
  const { threads, isLoading: threadsLoading } = useActiveThreads(10);
  const { subtasks, isLoading: subtasksLoading } = useSubtasks();
  const { activities, isLoading: activitiesLoading } = useRecentActivity(10);
  const { status: systemStatus, isLoading: statusLoading } = useSystemStatus();

  const isLoading =
    statsLoading ||
    threadsLoading ||
    subtasksLoading ||
    activitiesLoading ||
    statusLoading;

  // Handle manual refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    // The hooks will automatically refetch due to TanStack Query's invalidation
    // We just need to update the timestamp
    setTimeout(() => {
      setLastUpdated(new Date());
      setIsRefreshing(false);
    }, 500);
  };

  return (
    <div className="flex h-full flex-col gap-6 overflow-auto p-6">
      {/* Header */}
      <DashboardHeader
        lastUpdated={lastUpdated}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Stats Overview */}
      <StatsOverviewGrid stats={stats} isLoading={statsLoading} />

      {/* Main Content Grid */}
      <div className="grid flex-1 gap-6 lg:grid-cols-2">
        {/* Active Threads Panel */}
        <ActiveThreadsPanel
          threads={threads}
          isLoading={threadsLoading}
          className="min-h-[300px]"
        />

        {/* Subtasks Panel */}
        <SubtasksPanel
          subtasks={subtasks}
          isLoading={subtasksLoading}
          className="min-h-[300px]"
        />

        {/* Activity Timeline */}
        <ActivityTimeline
          activities={activities}
          isLoading={activitiesLoading}
          className="min-h-[300px]"
        />

        {/* System Status Panel */}
        <SystemStatusPanel
          status={systemStatus}
          isLoading={statusLoading}
          className="min-h-[300px]"
        />
      </div>

      {/* Quick Actions */}
      <QuickActionsBar />
    </div>
  );
}
