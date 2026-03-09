# Mission Control Dashboard - Implementation Plan

**Date**: 2026-03-09  
**Status**: Planning Phase  
**Design Doc**: `/docs/designs/2026-03-09-mission-control-dashboard.md`

---

## Overview

This plan implements the Mission Control Dashboard for DeerFlow using **Test-Driven Development (TDD)**:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 1. Write    │ ──▶ │ 2. Verify   │ ──▶ │ 3. Minimal  │ ──▶ │ 4. Verify   │
│    Test     │     │    Failure  │     │    Code     │     │    Pass     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   ▼
                                                            ┌─────────────┐
                                                            │ 5. Commit   │
                                                            └─────────────┘
```

---

## Phase 1: Foundation & Types (Tasks 1-5)

### Task 1: Create Dashboard Types
**File**: `frontend/src/core/dashboard/types.ts`  
**Estimated Time**: 3 minutes

**TDD Steps**:
1. **Write Test**: Create type definitions for `DashboardStats`, `ThreadWithStatus`, `ActivityItem`
2. **Verify**: Run `pnpm typecheck` - should pass (types only)
3. **Commit**: `git add . && git commit -m "feat(dashboard): add dashboard type definitions"`

**Code to Write**:
```typescript
export interface DashboardStats {
  activeThreads: number;
  pendingTasks: number;
  completedToday: number;
  artifactsGenerated: number;
}

export interface ThreadWithStatus {
  thread_id: string;
  title: string;
  updated_at: string;
  status: "active" | "idle" | "completed";
  progress: number;
  todoCount: number;
  completedTodos: number;
}

export interface ActivityItem {
  id: string;
  type: "thread_created" | "task_completed" | "artifact_generated" | "memory_updated";
  title: string;
  timestamp: string;
  threadId?: string;
}

export interface SubtaskInfo {
  id: string;
  description: string;
  status: "pending" | "in_progress" | "completed";
  threadId: string;
  threadTitle: string;
}
```

---

### Task 2: Create Dashboard Data Utils
**File**: `frontend/src/core/dashboard/utils.ts`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Create test file `frontend/src/core/dashboard/utils.test.ts` with test cases for `calculateThreadProgress`, `getThreadStatus`, `generateActivityItems`
2. **Verify Failure**: Run tests - should fail (functions don't exist yet)
3. **Implement**: Write the utility functions
4. **Verify Pass**: Run tests - should pass
5. **Commit**: `git add . && git commit -m "feat(dashboard): add dashboard data transformation utilities"`

**Functions to Implement**:
```typescript
export function calculateThreadProgress(todos?: Todo[]): number {
  if (!todos || todos.length === 0) return 0;
  const completed = todos.filter((t) => t.status === "completed").length;
  return Math.round((completed / todos.length) * 100);
}

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
```

---

### Task 3: Create Dashboard Hooks
**File**: `frontend/src/core/dashboard/hooks.ts`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Create mocks and test dashboard data aggregation
2. **Verify Failure**: Tests fail (hooks don't exist)
3. **Implement**: Write `useDashboardStats`, `useActiveThreads`, `useRecentActivity` hooks
4. **Verify Pass**: Tests pass
5. **Commit**: `git add . && git commit -m "feat(dashboard): add dashboard data hooks"`

**Hooks to Implement**:
```typescript
export function useDashboardStats() {
  const { threads } = useThreadsData(); // Uses existing useThreads
  // Calculate stats from threads
}

export function useActiveThreads(limit = 10) {
  const { threads } = useThreadsData();
  // Transform to ThreadWithStatus[]
}
```

---

### Task 4: Add Dashboard Index Export
**File**: `frontend/src/core/dashboard/index.ts`  
**Estimated Time**: 2 minutes

**TDD Steps**:
1. **Write**: Export all dashboard modules
2. **Verify**: `pnpm typecheck` passes
3. **Commit**: `git add . && git commit -m "feat(dashboard): add dashboard module exports"`

**Code**:
```typescript
export * from "./types";
export * from "./utils";
export * from "./hooks";
```

---

### Task 5: Create Dashboard Page Route
**File**: `frontend/src/app/workspace/dashboard/page.tsx`  
**Estimated Time**: 3 minutes

**TDD Steps**:
1. **Write**: Basic page component with placeholder content
2. **Verify**: Navigate to `/workspace/dashboard` - page loads
3. **Commit**: `git add . && git commit -m "feat(dashboard): create dashboard page route"`

**Code**:
```typescript
"use client";

export default function DashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Mission Control</h1>
      <p>Dashboard coming soon...</p>
    </div>
  );
}
```

**Checkpoint 1**: Foundation complete. Run `pnpm check` to verify no errors.

---

## Phase 2: UI Components (Tasks 6-12)

### Task 6: Create StatCard Component
**File**: `frontend/src/components/dashboard/stat-card.tsx`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Render component with props, verify display
2. **Verify Failure**: Test fails
3. **Implement**: Create StatCard with icon, label, value
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add StatCard component"`

**Props Interface**:
```typescript
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  trend?: { value: number; isPositive: boolean };
  className?: string;
}
```

---

### Task 7: Create StatsOverviewGrid Component
**File**: `frontend/src/components/dashboard/stats-overview-grid.tsx`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Verify grid renders 4 StatCards with correct data
2. **Verify Failure**: Test fails
3. **Implement**: Grid layout using CSS Grid
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add StatsOverviewGrid component"`

**Design**: 4-column grid on desktop, 2-column on tablet, 1-column on mobile

---

### Task 8: Create ThreadStatusCard Component
**File**: `frontend/src/components/dashboard/thread-status-card.tsx`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Render thread with progress bar
2. **Verify Failure**: Test fails
3. **Implement**: Card with status badge, progress bar, todo count
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add ThreadStatusCard component"`

**Features**:
- Status indicator (dot color)
- Progress bar (0-100%)
- Click to navigate to thread

---

### Task 9: Create ActiveThreadsPanel Component
**File**: `frontend/src/components/dashboard/active-threads-panel.tsx`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Verify list renders ThreadStatusCards
2. **Verify Failure**: Test fails
3. **Implement**: Panel with header and scrollable list
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add ActiveThreadsPanel component"`

---

### Task 10: Create SubtaskProgressCard Component
**File**: `frontend/src/components/dashboard/subtask-progress-card.tsx`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Render subtask with status
2. **Verify Failure**: Test fails
3. **Implement**: Card with subagent type, description, elapsed time
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add SubtaskProgressCard component"`

---

### Task 11: Create SubtasksPanel Component
**File**: `frontend/src/components/dashboard/subtasks-panel.tsx`  
**Estimated Time**: 4 minutes

**TDD Steps**:
1. **Write Test**: Verify running subtasks display
2. **Verify Failure**: Test fails
3. **Implement**: Panel aggregating todos from all threads
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add SubtasksPanel component"`

---

### Task 12: Create SystemStatusPanel Component
**File**: `frontend/src/components/dashboard/system-status-panel.tsx`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Verify models, skills, tools display
2. **Verify Failure**: Test fails
3. **Implement**: Panel with sections for each system component
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add SystemStatusPanel component"`

**Sections**:
- Models: List of available models
- Skills: Enabled skills count + list
- Tools: Tool groups
- Memory: Fact count

**Checkpoint 2**: UI components complete. Run `pnpm check` to verify.

---

## Phase 3: Dashboard Assembly (Tasks 13-16)

### Task 13: Create ActivityTimeline Component
**File**: `frontend/src/components/dashboard/activity-timeline.tsx`  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Verify timeline renders items chronologically
2. **Verify Failure**: Test fails
3. **Implement**: Vertical timeline with icons and timestamps
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add ActivityTimeline component"`

---

### Task 14: Create QuickActionsBar Component
**File**: `frontend/src/components/dashboard/quick-actions-bar.tsx`  
**Estimated Time**: 4 minutes

**TDD Steps**:
1. **Write Test**: Verify buttons render and trigger actions
2. **Verify Failure**: Test fails
3. **Implement**: Button group with +New Thread, +New Agent, etc.
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add QuickActionsBar component"`

---

### Task 15: Create DashboardHeader Component
**File**: `frontend/src/components/dashboard/dashboard-header.tsx`  
**Estimated Time**: 4 minutes

**TDD Steps**:
1. **Write Test**: Verify header renders with title and refresh indicator
2. **Verify Failure**: Test fails
3. **Implement**: Header with title, last-updated timestamp, refresh button
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add DashboardHeader component"`

---

### Task 16: Assemble DashboardPage
**File**: `frontend/src/app/workspace/dashboard/page.tsx` (update)  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Verify all sections render correctly
2. **Verify Failure**: Test fails (page still has placeholder)
3. **Implement**: Full page layout with all components
4. **Verify Pass**: Tests pass, visual inspection
5. **Commit**: `git add . && git commit -m "feat(dashboard): assemble full dashboard page"`

**Layout Structure**:
```
┌─────────────────────────────────────┐
│ DashboardHeader                     │
├─────────────────────────────────────┤
│ StatsOverviewGrid                   │
├──────────────────┬──────────────────┤
│ ActiveThreads    │ Subtasks         │
│ Panel            │ Panel            │
├──────────────────┴──────────────────┤
│ ActivityTimeline  │ SystemStatus    │
├──────────────────┴──────────────────┤
│ QuickActionsBar                     │
└─────────────────────────────────────┘
```

**Checkpoint 3**: Dashboard functional. Manual testing in browser.

---

## Phase 4: Navigation & Integration (Tasks 17-20)

### Task 17: Add Dashboard to Sidebar Navigation
**File**: `frontend/src/components/workspace/workspace-nav-chat-list.tsx` (update)  
**Estimated Time**: 3 minutes

**TDD Steps**:
1. **Write**: Add Dashboard nav item with LayoutDashboard icon
2. **Verify**: Dashboard appears in sidebar, navigation works
3. **Commit**: `git add . && git commit -m "feat(dashboard): add dashboard to sidebar navigation"`

---

### Task 18: Add i18n Translations
**File**: `frontend/src/core/i18n/locales/en-US.ts` (update)  
**Estimated Time**: 4 minutes

**TDD Steps**:
1. **Write**: Add dashboard translation keys
2. **Verify**: `pnpm typecheck` passes
3. **Commit**: `git add . && git commit -m "feat(dashboard): add i18n translations"`

**Keys to Add**:
```typescript
dashboard: {
  title: "Mission Control",
  stats: {
    activeThreads: "Active Threads",
    pendingTasks: "Pending Tasks",
    completedToday: "Completed Today",
    artifactsGenerated: "Artifacts Generated",
  },
  panels: {
    activeThreads: "Active Threads",
    runningSubtasks: "Running Subtasks",
    recentActivity: "Recent Activity",
    systemStatus: "System Status",
  },
  actions: {
    newThread: "New Thread",
    newAgent: "New Agent",
    installSkill: "Install Skill",
  },
}
```

---

### Task 19: Add zh-CN Translations
**File**: `frontend/src/core/i18n/locales/zh-CN.ts` (update)  
**Estimated Time**: 3 minutes

**TDD Steps**:
1. **Write**: Add Chinese translations for dashboard keys
2. **Verify**: `pnpm typecheck` passes
3. **Commit**: `git add . && git commit -m "feat(dashboard): add Chinese i18n translations"`

---

### Task 20: Create Dashboard Loading State
**File**: `frontend/src/components/dashboard/dashboard-skeleton.tsx`  
**Estimated Time**: 4 minutes

**TDD Steps**:
1. **Write Test**: Verify skeleton renders
2. **Verify Failure**: Test fails
3. **Implement**: Skeleton placeholder matching dashboard layout
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add loading skeleton"`

---

## Phase 5: Polish & Optimization (Tasks 21-25)

### Task 21: Implement Polling Strategy
**File**: `frontend/src/core/dashboard/hooks.ts` (update)  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Verify refetch intervals work correctly
2. **Verify Failure**: Test fails
3. **Implement**: Add refetchInterval to hooks (30s for threads)
4. **Verify Pass**: Tests pass
5. **Commit**: `git add . && git commit -m "feat(dashboard): implement data polling"`

**Polling Config**:
```typescript
// useActiveThreads
refetchInterval: 30000, // 30 seconds

// useDashboardStats (derived from threads)
staleTime: 30000,
```

---

### Task 22: Add Empty States
**Files**: Various component updates  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Write Test**: Verify empty states render when no data
2. **Verify Failure**: Tests fail
3. **Implement**: Empty state components for each panel
4. **Verify Pass**: Tests pass
5. **Commit**: `git add . && git commit -m "feat(dashboard): add empty states"`

---

### Task 23: Add Error Handling
**File**: `frontend/src/components/dashboard/dashboard-error.tsx`  
**Estimated Time**: 4 minutes

**TDD Steps**:
1. **Write Test**: Verify error state renders
2. **Verify Failure**: Test fails
3. **Implement**: Error boundary component with retry action
4. **Verify Pass**: Test passes
5. **Commit**: `git add . && git commit -m "feat(dashboard): add error handling"`

---

### Task 24: Responsive Layout Adjustments
**File**: `frontend/src/app/workspace/dashboard/page.tsx` (update)  
**Estimated Time**: 4 minutes

**TDD Steps**:
1. **Visual Test**: Check layout on different screen sizes
2. **Adjust**: Update grid classes for responsiveness
3. **Verify**: Layout works on 1280px+, 1024px, 768px
4. **Commit**: `git add . && git commit -m "feat(dashboard): responsive layout adjustments"`

---

### Task 25: Final Code Quality Check
**Files**: All dashboard files  
**Estimated Time**: 5 minutes

**TDD Steps**:
1. **Run**: `pnpm check` (lint + typecheck)
2. **Fix**: Any errors or warnings
3. **Verify**: All checks pass
4. **Commit**: `git add . && git commit -m "chore(dashboard): final code quality fixes"`

**Final Checkpoint**: Run full verification:
```bash
cd frontend
pnpm check
pnpm build  # Verify build succeeds
```

---

## Summary

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Foundation | 1-5 | ~18 minutes |
| Phase 2: UI Components | 6-12 | ~34 minutes |
| Phase 3: Assembly | 13-16 | ~18 minutes |
| Phase 4: Navigation | 17-20 | ~14 minutes |
| Phase 5: Polish | 21-25 | ~23 minutes |
| **Total** | **25 tasks** | **~107 minutes** |

---

## Verification Checklist

After each task:
- [ ] Test passes (if applicable)
- [ ] `pnpm typecheck` passes
- [ ] `pnpm lint` passes
- [ ] Commit with descriptive message

After each phase:
- [ ] `pnpm check` passes
- [ ] Visual inspection in browser
- [ ] Commit phase checkpoint

Final verification:
- [ ] All 25 tasks complete
- [ ] Full `pnpm check` passes
- [ ] `pnpm build` succeeds
- [ ] Dashboard accessible at `/workspace/dashboard`
- [ ] Navigation works from sidebar
- [ ] Data displays correctly

---

**Ready to Execute**: Start with Task 1 when ready! 🚀
