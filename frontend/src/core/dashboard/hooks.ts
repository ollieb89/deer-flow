"use client";

import { useMemo } from "react";

import { useAgents } from "@/core/agents/hooks";
import { useMemory } from "@/core/memory/hooks";
import { useModels } from "@/core/models/hooks";
import { useSkills } from "@/core/skills/hooks";
import { useThreads } from "@/core/threads/hooks";

import type {
  ActivityItem,
  DashboardStats,
  SubtaskInfo,
  SystemStatus,
  ThreadWithStatus,
} from "./types";
import {
  countCompletedToday,
  countTotalArtifacts,
  extractSubtasksFromThreads,
  generateActivityItems,
  transformThreadWithStatus,
} from "./utils";

/**
 * Hook to fetch and compute dashboard statistics
 * Uses existing useThreads hook with a 30s refresh interval
 */
export function useDashboardStats(): {
  stats: DashboardStats;
  isLoading: boolean;
} {
  const { data: threads = [], isLoading } = useThreads({
    limit: 100,
    sortBy: "updated_at",
    sortOrder: "desc",
  });

  const stats = useMemo((): DashboardStats => {
    const activeThreads = threads.filter((t) => {
      const todos = t.values?.todos ?? [];
      return todos.some((todo) => todo.status === "in_progress");
    }).length;

    const pendingTasks = threads.reduce((sum, t) => {
      const todos = t.values?.todos ?? [];
      return sum + todos.filter((todo) => todo.status === "pending").length;
    }, 0);

    const completedToday = countCompletedToday(threads);
    const artifactsGenerated = countTotalArtifacts(threads);

    return {
      activeThreads,
      pendingTasks,
      completedToday,
      artifactsGenerated,
    };
  }, [threads]);

  return { stats, isLoading };
}

/**
 * Hook to get active threads with computed status
 * Returns threads sorted by most recently updated
 */
export function useActiveThreads(limit = 10): {
  threads: ThreadWithStatus[];
  isLoading: boolean;
} {
  const { data: threads = [], isLoading } = useThreads({
    limit,
    sortBy: "updated_at",
    sortOrder: "desc",
  });

  const activeThreads = useMemo((): ThreadWithStatus[] => {
    return threads.map(transformThreadWithStatus);
  }, [threads]);

  return { threads: activeThreads, isLoading };
}

/**
 * Hook to get all subtasks from all threads
 * Returns pending and in-progress subtasks
 */
export function useSubtasks(): {
  subtasks: SubtaskInfo[];
  isLoading: boolean;
} {
  const { data: threads = [], isLoading } = useThreads({
    limit: 100,
    sortBy: "updated_at",
    sortOrder: "desc",
  });

  const subtasks = useMemo((): SubtaskInfo[] => {
    return extractSubtasksFromThreads(threads);
  }, [threads]);

  return { subtasks, isLoading };
}

/**
 * Hook to get recent activity across all threads
 */
export function useRecentActivity(limit = 10): {
  activities: ActivityItem[];
  isLoading: boolean;
} {
  const { data: threads = [], isLoading } = useThreads({
    limit: 50,
    sortBy: "updated_at",
    sortOrder: "desc",
  });

  const activities = useMemo((): ActivityItem[] => {
    const allActivities = generateActivityItems(threads);
    return allActivities.slice(0, limit);
  }, [threads, limit]);

  return { activities, isLoading };
}

/**
 * Hook to get system status (models, skills, tools, memory)
 * Aggregates data from multiple existing hooks
 */
export function useSystemStatus(): {
  status: SystemStatus | null;
  isLoading: boolean;
} {
  const { models, isLoading: modelsLoading } = useModels();
  const { skills, isLoading: skillsLoading } = useSkills();
  const { memory, isLoading: memoryLoading } = useMemory();

  const status = useMemo((): SystemStatus | null => {
    if (modelsLoading || skillsLoading || memoryLoading) {
      return null;
    }

    return {
      models: models.map((m) => ({
        id: m.id,
        display_name: m.display_name,
        enabled: true,
      })),
      skills: skills.map((s) => ({
        name: s.name,
        description: s.description,
        enabled: s.enabled,
      })),
      toolGroups: ["web", "file:read", "file:write", "bash"],
      memoryFacts: memory?.facts?.length ?? 0,
    };
  }, [models, skills, memory, modelsLoading, skillsLoading, memoryLoading]);

  const isLoading = modelsLoading || skillsLoading || memoryLoading;

  return { status, isLoading };
}

/**
 * Hook to get all dashboard data in one call
 * Useful for the main dashboard page
 */
export function useDashboardData(): {
  stats: DashboardStats;
  threads: ThreadWithStatus[];
  subtasks: SubtaskInfo[];
  activities: ActivityItem[];
  systemStatus: SystemStatus | null;
  isLoading: boolean;
} {
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

  return {
    stats,
    threads,
    subtasks,
    activities,
    systemStatus,
    isLoading,
  };
}
