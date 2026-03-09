// Note: Todo type is imported in utils.ts where it's used

/**
 * Dashboard statistics overview
 */
export interface DashboardStats {
  activeThreads: number;
  pendingTasks: number;
  completedToday: number;
  artifactsGenerated: number;
}

/**
 * Thread with computed status information for dashboard display
 */
export interface ThreadWithStatus {
  thread_id: string;
  title: string;
  updated_at: string;
  status: "active" | "idle" | "completed";
  progress: number;
  todoCount: number;
  completedTodos: number;
}

/**
 * Activity item types for the timeline
 */
export type ActivityType =
  | "thread_created"
  | "task_completed"
  | "task_in_progress"
  | "artifact_generated"
  | "memory_updated"
  | "message_sent";

/**
 * Activity item for the dashboard timeline
 */
export interface ActivityItem {
  id: string;
  type: ActivityType;
  title: string;
  timestamp: string;
  threadId?: string;
  threadTitle?: string;
}

/**
 * Subtask information aggregated from thread todos
 */
export interface SubtaskInfo {
  id: string;
  description: string;
  status: "pending" | "in_progress" | "completed";
  threadId: string;
  threadTitle: string;
}

/**
 * System status information
 */
export interface SystemStatus {
  models: {
    id: string;
    display_name: string;
    enabled: boolean;
  }[];
  skills: {
    name: string;
    description: string;
    enabled: boolean;
  }[];
  toolGroups: string[];
  memoryFacts: number;
}
