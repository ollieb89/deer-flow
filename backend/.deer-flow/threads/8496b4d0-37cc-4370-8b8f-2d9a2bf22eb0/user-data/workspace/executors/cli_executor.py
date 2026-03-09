"""AgentBrowser CLI executor for real integration with agent-browser skill."""
import subprocess
import time
from pathlib import Path
from typing import Any

from models import TaskDefinition, ExecutionContext, ExecutionResult, BaseBrowserExecutor


class AgentBrowserCLIExecutor(BaseBrowserExecutor):
    """Executor that runs the actual agent-browser CLI."""
    name = "agent_browser_cli"

    def __init__(self, cli_path: str = "agent-browser", cli_timeout: int = 120):
        """
        Initialize the CLI executor.

        Args:
            cli_path: Path to the agent-browser CLI executable
            cli_timeout: Default timeout for CLI execution in seconds
        """
        self.cli_path = cli_path
        self.cli_timeout = cli_timeout

    def run(self, task: TaskDefinition, context: ExecutionContext) -> ExecutionResult:
        """Execute the task using the agent-browser CLI."""
        start_time = time.time()

        # Construct the CLI command
        # Example: agent-browser --prompt "task prompt" --start-url "http://..." --output result.json
        cmd = [
            self.cli_path,
            "--prompt", task.prompt,
            "--output", str(context.workspace_dir / "cli_result.json")
        ]

        if task.start_url:
            cmd.extend(["--start-url", task.start_url])

        # Add any environment-specific flags
        if task.environment.get("type") == "local_fixture_site":
            cmd.append("--local-fixture")

        # Set timeout (use context timeout if provided, otherwise default)
        timeout = context.timeout_seconds or self.cli_timeout

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**context.env} if context.env else None,
                cwd=context.workspace_dir
            )

            duration = time.time() - start_time

            # Parse the CLI output JSON if it exists
            result_data = {}
            result_file = context.workspace_dir / "cli_result.json"
            if result_file.exists():
                import json
                with open(result_file) as f:
                    result_data = json.load(f)

            # Map CLI output to ExecutionResult
            # The real implementation will depend on the actual agent-browser CLI format
            return ExecutionResult(
                task_id=task.id,
                status="success" if proc.returncode == 0 else "failed",
                execution_mode="agent_browser_cli",
                invoked_skill=result_data.get("invoked_skill"),
                final_url=result_data.get("final_url"),
                extracted_data=result_data.get("extracted_data", {}),
                actions=result_data.get("actions", []),
                logs=result_data.get("logs", proc.stdout.splitlines()),
                stdout=proc.stdout,
                stderr=proc.stderr,
                error=None if proc.returncode == 0 else f"CLI exit code {proc.returncode}",
                duration_seconds=duration,
                metadata={
                    "cli_returncode": proc.returncode,
                    "cli_args": cmd,
                }
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                task_id=task.id,
                status="timeout",
                execution_mode="agent_browser_cli",
                invoked_skill=None,
                final_url=None,
                extracted_data={},
                actions=[],
                logs=["Execution timed out"],
                stdout="",
                stderr="",
                error=f"Timeout after {timeout} seconds",
                duration_seconds=duration,
                metadata={"timeout": timeout}
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                task_id=task.id,
                status="error",
                execution_mode="agent_browser_cli",
                invoked_skill=None,
                final_url=None,
                extracted_data={},
                actions=[],
                logs=[f"Executor exception: {str(e)}"],
                stdout="",
                stderr="",
                error=str(e),
                duration_seconds=duration,
                metadata={"exception": str(e)}
            )
