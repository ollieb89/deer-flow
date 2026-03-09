# Design: python-fastapi-pro Subagent

**Date:** 2026-03-09  
**Status:** Approved

## Goal

Create a specialized subagent for FastAPI/backend development that inherits all capabilities from `python-agent` while adding FastAPI-specific expertise.

## Requirements

### Functional Requirements

1. Subagent can be invoked via `task` tool with `subagent_type="python-fastapi-pro"`
2. Inherits all 14 python-agent skills without duplication
3. Adds 3 new FastAPI-specific skills
4. System prompt emphasizes FastAPI/backend patterns
5. Prevents recursive task nesting (disallowed_tools includes "task")

### Non-Functional Requirements

- Follow existing subagent patterns (same structure as general-purpose, bash)
- Minimal changes to existing codebase
- Skills are modular and reusable
- Configuration is declarative via config.yaml

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         python-fastapi-pro Subagent                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Core System (from python-agent):                                       │
│  ├── python-code-style, python-type-safety                              │
│  ├── python-error-handling, python-testing-patterns                     │
│  ├── python-design-patterns, python-project-structure                   │
│  ├── python-async-patterns, python-performance-optimization             │
│  ├── python-packaging, uv-package-manager                               │
│  └── python-configuration, python-observability, python-resilience      │
│                                                                         │
│  FastAPI Extensions:                                                    │
│  ├── fastapi-patterns (dependencies, middleware, routing)               │
│  ├── async-sqlalchemy (SQLAlchemy 2.0 + FastAPI integration)            │
│  └── api-testing (pytest + httpx + TestClient patterns)                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Subagent Configuration

**Location:** `backend/src/subagents/builtins/python_fastapi_pro.py`

| Attribute | Value |
|-----------|-------|
| name | `python-fastapi-pro` |
| description | "A specialized agent for FastAPI and backend API development. Use when building FastAPI applications, designing REST APIs, implementing async database layers with SQLAlchemy 2.0, or writing API tests." |
| system_prompt | FastAPI-focused identity with API/backend best practices |
| skills | All `python-agent` skills + 3 new FastAPI skills |
| max_turns | 50 |
| timeout_seconds | 900 |
| disallowed_tools | `["task", "ask_clarification", "present_files"]` |

### 2. New Skills

Created in `.deer-flow/agents/python-fastapi-pro/skills/`:

| Skill | Description |
|-------|-------------|
| `fastapi-patterns` | Dependency injection, middleware patterns, routing best practices |
| `async-sqlalchemy` | Async ORM patterns, transaction management, connection pooling with FastAPI |
| `api-testing` | FastAPI TestClient, async test patterns, httpx mocking |

### 3. Registry Integration

- **Add to:** `backend/src/subagents/builtins/__init__.py` → `BUILTIN_SUBAGENTS`
- **Add to:** `backend/src/tools/builtins/task_tool.py` → `subagent_type` Literal

### 4. Agent Config Update

**Location:** `.deer-flow/agents/python-fastapi-pro/config.yaml`

Update to reference all inherited skills plus new FastAPI skills.

## Data Flow

```
User Request → Lead Agent → task_tool(subagent_type="python-fastapi-pro") 
    → SubagentExecutor → FastAPI-specialized subagent with full Python skills
```

## Files to Create/Modify

### Create

1. `backend/src/subagents/builtins/python_fastapi_pro.py` - Subagent configuration
2. `.deer-flow/agents/python-fastapi-pro/skills/fastapi-patterns/SKILL.md`
3. `.deer-flow/agents/python-fastapi-pro/skills/async-sqlalchemy/SKILL.md`
4. `.deer-flow/agents/python-fastapi-pro/skills/api-testing/SKILL.md`

### Modify

1. `backend/src/subagents/builtins/__init__.py` - Add to BUILTIN_SUBAGENTS
2. `backend/src/tools/builtins/task_tool.py` - Add to subagent_type Literal
3. `.deer-flow/agents/python-fastapi-pro/config.yaml` - Update skills list

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Skill name conflicts | Use prefixed names (`fastapi-*`) for new skills |
| Skills drift from python-agent | Reference skills by name in config, don't copy |
| Subagent nesting | Explicitly disallow `task` tool |
| Over-complication | Keep skills focused, follow Rule of Three |

## Success Criteria

1. ✅ Subagent can be invoked via `task` tool with `subagent_type="python-fastapi-pro"`
2. ✅ Inherits all 14 python-agent skills without duplication
3. ✅ Adds 3 new FastAPI-specific skills
4. ✅ System prompt emphasizes FastAPI/backend patterns
5. ✅ Prevents recursive task nesting
