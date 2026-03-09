from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class TaskDefinition:
    """Structured task definition loaded from task.json"""
    id: str
    prompt: str
    start_url: str | None = None
    requires_browser: bool | None = None
    environment: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context for a single execution run"""
    variant: str  # "baseline" | "skill"
    iteration: int
    workspace_dir: Path
    timeout_seconds: int = 120
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Normalized execution record returned by executors and persisted as result.json"""
    task_id: str
    status: str  # "success" | "failed" | "timeout" | "error"
    execution_mode: str  # "mock" | "agent_browser_cli"
    invoked_skill: bool | None = None
    final_url: str | None = None
    extracted_data: dict[str, Any] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    stdout: str | None = None
    stderr: str | None = None
    error: str | None = None
    duration_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON storage"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "execution_mode": self.execution_mode,
            "invoked_skill": self.invoked_skill,
            "final_url": self.final_url,
            "extracted_data": self.extracted_data,
            "actions": self.actions,
            "logs": self.logs,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


class BrowserExecutor(Protocol):
    """Interface contract for all executors"""
    def run(self, task: TaskDefinition, context: ExecutionContext) -> ExecutionResult:
        ...


class BaseBrowserExecutor(ABC):
    """Optional base class with shared utilities"""
    name: str = "base"

    @abstractmethod
    def run(self, task: TaskDefinition, context: ExecutionContext) -> ExecutionResult:
        raise NotImplementedError

    def _base_result(self, task: TaskDefinition, status: str = "error", **kwargs) -> ExecutionResult:
        """Helper to create a result with task_id and execution_mode pre-filled"""
        return ExecutionResult(
            task_id=task.id,
            status=status,
            execution_mode=self.name,
            **kwargs,
        )
