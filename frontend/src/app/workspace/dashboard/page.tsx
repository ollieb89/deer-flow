"use client";

import { Activity, CheckCircle, Clock, FileOutput } from "lucide-react";

import { useDashboardStats } from "@/core/dashboard";

/**
 * Mission Control Dashboard Page
 * Provides an overview of system status, active threads, and recent activity
 */
export default function DashboardPage() {
  const { stats, isLoading } = useDashboardStats();

  return (
    <div className="flex h-full flex-col overflow-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Mission Control</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Real-time overview of your DeerFlow operations
        </p>
      </div>

      {/* Stats Grid */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Active Threads */}
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500/10 rounded-md p-2">
              <Activity className="text-blue-500 size-5" />
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Active Threads</p>
              <p className="text-2xl font-semibold">
                {isLoading ? "-" : stats.activeThreads}
              </p>
            </div>
          </div>
        </div>

        {/* Pending Tasks */}
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="bg-amber-500/10 rounded-md p-2">
              <Clock className="text-amber-500 size-5" />
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Pending Tasks</p>
              <p className="text-2xl font-semibold">
                {isLoading ? "-" : stats.pendingTasks}
              </p>
            </div>
          </div>
        </div>

        {/* Completed Today */}
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="bg-green-500/10 rounded-md p-2">
              <CheckCircle className="text-green-500 size-5" />
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Completed Today</p>
              <p className="text-2xl font-semibold">
                {isLoading ? "-" : stats.completedToday}
              </p>
            </div>
          </div>
        </div>

        {/* Artifacts Generated */}
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="bg-purple-500/10 rounded-md p-2">
              <FileOutput className="text-purple-500 size-5" />
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Artifacts</p>
              <p className="text-2xl font-semibold">
                {isLoading ? "-" : stats.artifactsGenerated}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Placeholder for more content */}
      <div className="bg-card flex flex-1 items-center justify-center rounded-lg border">
        <div className="text-muted-foreground text-center">
          <p className="mb-2 text-lg font-medium">Dashboard Coming Soon</p>
          <p className="text-sm">
            More panels and features are being implemented
          </p>
        </div>
      </div>
    </div>
  );
}
