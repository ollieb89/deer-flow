# Mission Control Dashboard - Design Document

**Date**: 2026-03-09  
**Status**: Brainstorming Phase  
**Author**: AI Assistant

---

## 1. Goal

Build a **Mission Control Dashboard** for DeerFlow that provides users with a comprehensive, real-time overview of their AI agent operations. This dashboard serves as the "mission control center" for the super agent harness, giving users visibility into:

- System health and active operations
- Running threads and their statuses
- Active subagents and subtasks
- Resource utilization (models, skills, tools)
- Recent activity and artifacts
- Task completion analytics

### Why Mission Control?

DeerFlow is a "super agent harness" capable of spawning multiple sub-agents for complex, multi-step tasks. Users currently navigate through individual chat threads but lack a **bird's-eye view** of:
- What's currently running
- How sub-tasks are progressing
- System resource usage
- Historical performance patterns

The NASA Mission Control metaphor aligns perfectly with DeerFlow's multi-agent orchestration paradigm.

---

## 2. Requirements

### 2.1 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| F1 | Display real-time system status (connected/disconnected) | P0 |
| F2 | Show active threads with status indicators | P0 |
| F3 | Show running/pending/completed subtasks | P0 |
| F4 | Display available models and their configurations | P1 |
| F5 | Display enabled skills and tool groups | P1 |
| F6 | Show recent artifacts generated | P1 |
| F7 | Display todo list summary (pending/in-progress/completed) | P1 |
| F8 | Show memory utilization (facts stored) | P2 |
| F9 | Activity timeline/recent events feed | P2 |
| F10 | Quick actions (new thread, new agent, install skill) | P2 |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| N1 | Dashboard loads within 2 seconds | < 2s |
| N2 | Real-time updates via polling or WebSocket | 5s refresh |
| N3 | Responsive design (desktop-first, tablet support) | 1280px+ |
| N4 | Dark theme matching DeerFlow aesthetic | Consistent |
| N5 | Accessible (keyboard nav, screen reader) | WCAG 2.1 AA |

### 2.3 User Stories

#### Monitoring & Visibility
**As a** research scientist running multiple parallel investigations  
**I want to** see a live percentage-based progress bar and status for every active thread  
**So that** I can accurately estimate completion times and prioritize my focus without switching contexts.

**As a** developer debugging a complex multi-agent workflow  
**I want to** see real-time status indicators for which models and skills are currently active  
**So that** I can identify bottlenecks or configuration errors in my orchestration logic.

**As a** system administrator  
**I want to** see a "System Health" indicator that monitors model provider connectivity and local system status  
**So that** I can ensure the super-agent harness is fully operational before launching mission-critical tasks.

#### Efficiency & Actions
**As a** power user managing a high volume of tasks  
**I want to** access a "Quick Actions" panel with shortcuts for creating new threads or spawning specialized agents  
**So that** I can reduce the number of clicks required to start common automated workflows.

**As a** project coordinator  
**I want to** see a "Global Todo Summary" that aggregates pending, in-progress, and completed items across all missions  
**So that** I can understand the total remaining workload at a glance.

#### Artifacts & Memory
**As a** content creator generating various assets  
**I want to** see a visual timeline of recent artifacts (images, documents, code snippets)  
**So that** I can quickly retrieve and reuse outputs without digging through individual chat histories.

**As a** knowledge worker  
**I want to** see a summary of "Memory Facts" that the system has recently extracted and stored  
**So that** I can verify the agent's evolving understanding of my project context and correct any misconceptions if necessary.

#### Troubleshooting
**As a** developer  
**I want to** see a clear error indicator on the dashboard when a subtask fails  
**So that** I can immediately jump to the specific thread and debug the issue before it cascades.

---

## 3. Proposed Architecture

### 3.1 Page Structure

```
/workspace/dashboard                 # New dashboard page
├── Header Section                  # Page title + last updated
├── Quick Stats Row                 # Key metrics cards
├── Main Content Grid
│   ├── Active Threads Panel        # List of threads with status
│   ├── Subtasks Panel              # Running subagents
│   ├── Activity Timeline           # Recent events
│   └── System Status Panel         # Models, skills, tools
└── Sidebar / Quick Actions         # Shortcuts to common actions
```

### 3.2 Component Hierarchy

```
DashboardPage (app/workspace/dashboard/page.tsx)
├── DashboardHeader
├── StatsOverviewGrid
│   ├── StatCard (active threads)
│   ├── StatCard (pending tasks)
│   ├── StatCard (completed today)
│   └── StatCard (artifacts generated)
├── DashboardGrid
│   ├── ActiveThreadsPanel
│   │   └── ThreadStatusCard[]
│   ├── SubtasksPanel
│   │   └── SubtaskProgressCard[]
│   ├── ActivityTimeline
│   │   └── TimelineItem[]
│   └── SystemStatusPanel
│       ├── ModelsStatus
│       ├── SkillsStatus
│       └── ToolsStatus
└── QuickActionsBar
```

### 3.3 Data Flow (Verified)

Based on actual project APIs:

```
Dashboard Components
        │
        ├──▶ useThreads() ─────────▶ LangGraph SDK threads.search()
        │                             Returns: AgentThread[] (with values: title, messages, artifacts, todos)
        ├──▶ useAgents() ──────────▶ GET /api/agents
        │                             Returns: Agent[] (name, description, model, tool_groups)
        ├──▶ useSkills() ──────────▶ GET /api/skills
        │                             Returns: Skill[] (name, description, category, enabled)
        ├──▶ useModels() ──────────▶ GET /api/models
        │                             Returns: Model[] (id, name, display_name, supports_thinking)
        ├──▶ useMemory() ──────────▶ GET /api/memory
        │                             Returns: UserMemory (facts[], user context, history)
        └──▶ useSubtasks() ────────▶ Derived from thread state (via useStream or useThreads)
                                      Returns: Subtask[] from thread.values.todos

Polling Strategy:
- Threads: 30s refresh (useQuery with staleTime)
- Agents/Skills/Models: On mount + cache
- Memory: On mount + manual refresh
- Real-time subtasks: Via thread streaming (not polling)
```

### 3.4 Tech Stack Alignment

| Layer | Technology | Notes |
|-------|------------|-------|
| Framework | Next.js 16 App Router | Follow existing patterns |
| Styling | Tailwind CSS 4 | Use existing CSS variables |
| Components | Radix UI + Shadcn | Reuse existing ui/ components |
| State | TanStack Query | Consistent with core/ pattern |
| Icons | Lucide React | Already in dependencies |
| Charts | Custom CSS-based | Avoid heavy chart libraries |

---

## 4. Detailed Design

### 4.1 Layout Design

```
┌─────────────────────────────────────────────────────────────────────┐
│  🦌 Mission Control                              Last updated: 2s ago│
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ Active   │ │ Pending  │ │Completed │ │ Artifacts│  Stats Cards   │
│  │ Threads  │ │ Tasks    │ │  Today   │ │  12      │               │
│  │   8      │ │   3      │ │   24     │ │          │               │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │
├──────────────────────────────┬──────────────────────────────────────┤
│  ACTIVE THREADS              │  RUNNING SUBTASKS                    │
│  ┌────────────────────────┐  │  ┌────────────────────────────────┐  │
│  │ 🔵 Research Assistant  │  │  │ ▶️ Web Search...        2m 30s │  │
│  │    3 subtasks running  │  │  │ 🟡 Code Generation...   1m 15s │  │
│  │ ━━━━━━━━░░░░ 67%       │  │  │ ⏸️ File Analysis        45s    │  │
│  ├────────────────────────┤  │  └────────────────────────────────┘  │
│  │ 🟢 Code Generator      │  │                                      │
│  │    0 subtasks          │  │  SYSTEM STATUS                       │
│  │ ✓ Idle                 │  │  ┌────────────────────────────────┐  │
│  └────────────────────────┘  │  │ Models    GPT-4, Claude 3.5    │  │
│                              │  │ Skills    12 enabled           │  │
│  RECENT ACTIVITY             │  │ Tools     web, bash, file:rw   │  │
│  ┌────────────────────────┐  │  │ Memory    47 facts stored      │  │
│  │ 2m ago  📄 Report gen  │  │  └────────────────────────────────┘  │
│  │ 5m ago  🔧 Tool: bash  │  │                                      │
│  │ 12m ago ✅ Task done   │  │  QUICK ACTIONS                       │
│  │ 1h ago  🧠 Memory upd  │  │  [+ New Thread] [+ New Agent] [...]  │
│  └────────────────────────┘  │                                      │
└──────────────────────────────┴──────────────────────────────────────┘
```

### 4.2 Color Scheme & Status Indicators

| Status | Color | Icon | Usage |
|--------|-------|------|-------|
| Active/Running | Blue (`blue-500`) | Circle play | Threads, subtasks |
| Completed/Success | Green (`green-500`) | Check circle | Finished tasks |
| Pending/Queued | Amber (`amber-500`) | Clock | Waiting subtasks |
| Error/Failed | Red (`red-500`) | X circle | Failed operations |
| Idle | Gray (`gray-400`) | Minus circle | Inactive threads |

### 4.3 Component Specifications

#### StatCard
- Size: ~200px width, auto height
- Contains: Icon, label, value, optional trend indicator
- Hover: Subtle elevation change

#### ThreadStatusCard
- Shows: Thread title, agent name, status, progress bar
- Progress: Based on todos completion percentage
- Click: Navigate to thread
- Status badge: Color-coded dot

#### SubtaskProgressCard
- Shows: Subagent type, description, elapsed time, status
- Progress: Animated bar for running tasks
- Status: Icon + text

#### ActivityTimeline
- Vertical list with connecting line
- Each item: Icon, description, timestamp
- Grouped by date (Today, Yesterday, Earlier)

---

## 5. API Requirements

### 5.1 Existing APIs to Use (Verified)

| Endpoint | Purpose | Hook | Location |
|----------|---------|------|----------|
| `threads.search()` | List all threads | `useThreads()` | `core/threads/hooks.ts:312` |
| `GET /api/agents` | List all agents | `useAgents()` | `core/agents/hooks.ts:12` |
| `GET /api/skills` | List skills | `useSkills()` | `core/skills/hooks.ts:7` |
| `GET /api/models` | List models | `useModels()` | `core/models/hooks.ts:6` |
| `GET /api/memory` | Memory data | `useMemory()` | `core/memory/hooks.ts:5` |

**Thread Data Structure:**
```typescript
interface AgentThread {
  thread_id: string;
  updated_at: string;
  values: {
    title: string;
    messages: Message[];
    artifacts: string[];
    todos?: Todo[];  // <-- Use for subtask tracking
  };
}

interface Todo {
  content?: string;
  status?: "pending" | "in_progress" | "completed";
}
```

### 5.2 New Data Transformations Needed

```typescript
// Derived stats from thread data
interface DashboardStats {
  activeThreads: number;
  totalSubtasks: number;
  pendingSubtasks: number;
  completedSubtasks: number;
  completedToday: number;
  artifactsGenerated: number;
}

// Enriched thread with derived status
interface ThreadWithStatus extends AgentThread {
  status: 'active' | 'idle' | 'completed' | 'error';
  progress: number; // 0-100 based on todos
  runningSubtasks: Subtask[];
}
```

---

## 6. File Structure

```
frontend/src/
├── app/workspace/dashboard/
│   ├── page.tsx                    # Main dashboard page
│   └── layout.tsx                  # Dashboard layout (optional)
├── components/dashboard/
│   ├── dashboard-header.tsx        # Page header with refresh
│   ├── stats-overview-grid.tsx     # Stats cards container
│   ├── stat-card.tsx               # Individual stat card
│   ├── dashboard-grid.tsx          # Main grid layout
│   ├── active-threads-panel.tsx    # Threads list panel
│   ├── thread-status-card.tsx      # Individual thread card
│   ├── subtasks-panel.tsx          # Subtasks list panel
│   ├── subtask-progress-card.tsx   # Individual subtask card
│   ├── activity-timeline.tsx       # Activity feed panel
│   ├── timeline-item.tsx           # Individual activity item
│   ├── system-status-panel.tsx     # System info panel
│   ├── models-status.tsx           # Models sub-panel
│   ├── skills-status.tsx           # Skills sub-panel
│   ├── tools-status.tsx            # Tools sub-panel
│   └── quick-actions-bar.tsx       # Action buttons
├── core/dashboard/
│   ├── hooks.ts                    # Dashboard-specific hooks
│   ├── utils.ts                    # Data transformation utils
│   └── types.ts                    # Dashboard-specific types
└── lib/
    └── dashboard-utils.ts          # Shared utilities
```

---

## 7. Implementation Phases

### Phase 1: Foundation (P0)
- [ ] Create dashboard page route
- [ ] Build dashboard layout structure
- [ ] Implement StatCard component
- [ ] Create ActiveThreadsPanel with real data

### Phase 2: Core Features (P0-P1)
- [ ] SubtasksPanel with progress indicators
- [ ] SystemStatusPanel (models, skills, tools)
- [ ] ActivityTimeline with mock data
- [ ] QuickActionsBar

### Phase 3: Polish (P1-P2)
- [ ] Real-time polling implementation
- [ ] Activity timeline with real events
- [ ] Responsive optimizations
- [ ] Empty states and loading skeletons

### Phase 4: Advanced (P2)
- [ ] Memory visualization
- [ ] Historical analytics
- [ ] Export/refresh controls
- [ ] Keyboard shortcuts

---

## 8. Unresolved Questions

1. **Q**: Should the dashboard auto-refresh or use WebSocket?  
   **A**: Start with polling (5s), evaluate WebSocket later.

2. **Q**: What constitutes "activity" for the timeline?  
   **A**: Thread creation, message sent, artifact generated, task completed.

3. **Q**: How to calculate thread "progress"?  
   **A**: Use todos: `(completed_todos / total_todos) * 100`.

4. **Q**: Should users be able to customize the dashboard layout?  
   **A**: Not for v1; consider for future enhancement.

---

## 9. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits from frequent polling | Medium | Implement exponential backoff, cache data |
| Performance with many threads | Medium | Virtualize lists, paginate data |
| Data inconsistency between dashboard and thread view | Low | Use shared TanStack Query cache |
| Mobile layout complexity | Low | Desktop-first, graceful degradation |

---

## 10. Success Criteria

- [ ] Dashboard loads in < 2 seconds
- [ ] All P0 requirements implemented
- [ ] Visual design matches DeerFlow aesthetic
- [ ] No console errors or warnings
- [ ] ESLint + TypeScript checks pass
- [ ] Manual testing confirms accurate data display

---

## 11. Future Enhancements (Post-MVP)

1. **Customizable widgets** - Drag-and-drop layout (use `@dnd-kit/core`)
2. **Advanced analytics** - Charts for usage patterns (consider `recharts` or lightweight canvas)
3. **Alerting** - Browser notifications for task completions (extend existing `core/notification`)
4. **Activity persistence** - Store dashboard activity in localStorage or backend
5. **Performance metrics** - Token usage, latency tracking (requires backend instrumentation)
6. **Workspace navigation integration** - Add Dashboard to sidebar alongside Chats/Agents
7. **Real-time via WebSocket** - Replace polling with LangGraph WebSocket streams

---

## Appendix: API Verification

### Verified Existing APIs

✅ **useThreads** (`core/threads/hooks.ts:312`)
```typescript
export function useThreads(params = { limit: 50, sortBy: "updated_at" })
// Returns AgentThread[] with todos in values
```

✅ **useAgents** (`core/agents/hooks.ts:12`)
```typescript
export function useAgents()
// Returns { agents: Agent[], isLoading, error }
```

✅ **useSkills** (`core/skills/hooks.ts:7`)
```typescript
export function useSkills()
// Returns { skills: Skill[], isLoading, error }
```

✅ **useModels** (`core/models/hooks.ts:6`)
```typescript
export function useModels()
// Returns { models: Model[], isLoading, error }
```

✅ **useMemory** (`core/memory/hooks.ts:5`)
```typescript
export function useMemory()
// Returns { memory: UserMemory, isLoading, error }
```

### Navigation Integration Points

The dashboard should be added to the sidebar navigation in `workspace-nav-chat-list.tsx`:

```typescript
// Current items:
// - /workspace/chats (MessagesSquare icon)
// - /workspace/agents (BotIcon icon)

// Add new item:
// - /workspace/dashboard (LayoutDashboard icon)
```

---

**Next Step**: Proceed to Phase 2 - Writing Plans (Task Breakdown)
