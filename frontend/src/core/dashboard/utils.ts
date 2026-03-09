import type { AgentThread } from "@/core/threads";
import type { Todo } from "@/core/todos";

import type {
  ActivityItem,
  SubtaskInfo,
  ThreadWithStatus,
} from "./types";

/**
 * Calculate thread progress based on todo completion
 * @param todos - Array of todos from thread state
 * @returns Progress percentage (0-100)
 */
export function calculateThreadProgress(todos?: Todo[]): number {
  if (!todos || todos.length === 0) return 0;
  const completed = todos.filter((t) => t.status === "completed").length;
  return Math.round((completed / todos.length) * 100);
}

/**
 * Get the status of a thread based on its todos
 * @param thread - AgentThread with values containing todos
 * @returns Status: 'active' | 'idle' | 'completed'
 */
export function getThreadStatus(
  thread: AgentThread,
): "active" | "idle" | "completed" {
  const todos = thread.values?.todos ?? [];
  if (todos.length === 0) return "idle";
  const hasInProgress = todos.some((t) => t.status === "in_progress");
  const allCompleted = todos.every((t) => t.status === "completed");
  if (hasInProgress) return "active";
  if (allCompleted) return "completed";
  return "idle";
}

/**
 * Transform AgentThread to ThreadWithStatus for dashboard display
 * @param thread - AgentThread from API
 * @returns ThreadWithStatus with computed fields
 */
export function transformThreadWithStatus(
  thread: AgentThread,
): ThreadWithStatus {
  const todos = thread.values?.todos ?? [];
  const completedTodos = todos.filter((t) => t.status === "completed").length;

  return {
    thread_id: thread.thread_id,
    title: thread.values?.title ?? "Untitled",
    updated_at: thread.updated_at,
    status: getThreadStatus(thread),
    progress: calculateThreadProgress(todos),
    todoCount: todos.length,
    completedTodos,
  };
}

/**
 * Extract subtasks from all threads
 * @param threads - Array of AgentThreads
 * @returns Array of SubtaskInfo
 */
export function extractSubtasksFromThreads(
  threads: AgentThread[],
): SubtaskInfo[] {
  const subtasks: SubtaskInfo[] = [];

  for (const thread of threads) {
    const todos = thread.values?.todos ?? [];
    const title = thread.values?.title ?? "Untitled";

    for (const todo of todos) {
      if (!todo.content) continue;

      subtasks.push({
        id: `${thread.thread_id}-${todo.content}`,
        description: todo.content,
        status: todo.status ?? "pending",
        threadId: thread.thread_id,
        threadTitle: title,
      });
    }
  }

  return subtasks;
}

/**
 * Generate activity items from threads
 * This creates a timeline of recent thread activity
 * @param threads - Array of AgentThreads
 * @returns Array of ActivityItem sorted by timestamp (newest first)
 */
export function generateActivityItems(
  threads: AgentThread[],
): ActivityItem[] {
  const activities: ActivityItem[] = [];

  for (const thread of threads) {
    const title = thread.values?.title ?? "Untitled";
    const todos = thread.values?.todos ?? [];

    // Add thread creation activity
    activities.push({
      id: `thread-created-${thread.thread_id}`,
      type: "thread_created",
      title: `Thread created: ${title}`,
      timestamp: thread.created_at ?? thread.updated_at,
      threadId: thread.thread_id,
      threadTitle: title,
    });

    // Add activities for in-progress and completed todos
    for (const todo of todos) {
      if (!todo.content) continue;

      if (todo.status === "in_progress") {
        activities.push({
          id: `task-progress-${thread.thread_id}-${todo.content}`,
          type: "task_in_progress",
          title: `Task started: ${todo.content}`,
          timestamp: thread.updated_at,
          threadId: thread.thread_id,
          threadTitle: title,
        });
      } else if (todo.status === "completed") {
        activities.push({
          id: `task-completed-${thread.thread_id}-${todo.content}`,
          type: "task_completed",
          title: `Task completed: ${todo.content}`,
          timestamp: thread.updated_at,
          threadId: thread.thread_id,
          threadTitle: title,
        });
      }
    }

    // Add artifact generation activity if artifacts exist
    const artifacts = thread.values?.artifacts ?? [];
    if (artifacts.length > 0) {
      activities.push({
        id: `artifacts-${thread.thread_id}`,
        type: "artifact_generated",
        title: `${artifacts.length} artifact${artifacts.length > 1 ? "s" : ""} generated in "${title}"`,
        timestamp: thread.updated_at,
        threadId: thread.thread_id,
        threadTitle: title,
      });
    }
  }

  // Sort by timestamp (newest first) and limit to most recent
  return activities
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    )
    .slice(0, 20);
}

/**
 * Check if a date is from today
 * @param dateString - ISO date string
 * @returns boolean
 */
export function isToday(dateString: string): boolean {
  const date = new Date(dateString);
  const today = new Date();
  return (
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  );
}

/**
 * Count completed todos from today across all threads
 * @param threads - Array of AgentThreads
 * @returns Number of completed todos today
 */
export function countCompletedToday(threads: AgentThread[]): number {
  let count = 0;
  for (const thread of threads) {
    if (!isToday(thread.updated_at)) continue;
    const todos = thread.values?.todos ?? [];
    count += todos.filter((t) => t.status === "completed").length;
  }
  return count;
}

/**
 * Count total artifacts across all threads
 * @param threads - Array of AgentThreads
 * @returns Total number of artifacts
 */
export function countTotalArtifacts(threads: AgentThread[]): number {
  return threads.reduce(
    (sum, thread) => sum + (thread.values?.artifacts?.length ?? 0),
    0,
  );
}
