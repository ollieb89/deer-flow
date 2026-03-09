"""Mock executor for deterministic evaluation testing."""
import time
from pathlib import Path
from typing import Any

from models import TaskDefinition, ExecutionContext, ExecutionResult, BaseBrowserExecutor


class MockBrowserExecutor(BaseBrowserExecutor):
    """Deterministic executor that simulates browser behavior based on task metadata."""
    name = "mock"

    def run(self, task: TaskDefinition, context: ExecutionContext) -> ExecutionResult:
        start_time = time.time()

        # Check for phase1 expected_trigger in metadata
        expected_trigger = task.metadata.get("phase1", {}).get("expected_trigger", False)

        # Determine invocation based on variant and expected_trigger
        if expected_trigger:
            # Phase 1 test: baseline should NOT invoke, skill SHOULD invoke
            should_invoke = (context.variant == "skill")
        else:
            # Standard behavior: follow task.requires_browser (default True) or should_succeed
            should_invoke = task.requires_browser if task.requires_browser is not None else True

        should_succeed = task.metadata.get("should_succeed", True)

        # Simulate actions based on expected behavior
        actions = []
        if should_invoke:
            actions.append({
                "type": "navigate",
                "url": task.start_url or "http://localhost:8000/",
                "success": True,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })

            # Simulate some interaction if task is expected to succeed
            if should_succeed:
                actions.append({
                    "type": "extract",
                    "selector": "body",
                    "value": "Sample content",
                    "success": True,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })

                # Set final_url to target if specified in metadata
                target_url = task.metadata.get("target_url")
                if target_url:
                    actions.append({
                        "type": "navigate",
                        "url": target_url,
                        "success": True,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    })
            else:
                actions.append({
                    "type": "error",
                    "message": "Simulated failure for testing",
                    "success": False,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })

        duration = time.time() - start_time

        # Build extracted_data based on metadata expectations
        extracted_data = {}
        if should_succeed and should_invoke:
            extracted_data = task.metadata.get("expected_extracted", {})
            # Add a default answer if target_url is set
            target_url = task.metadata.get("target_url")
            if target_url:
                extracted_data["answer"] = target_url

        # Determine status
        if should_invoke and should_succeed:
            status = "success"
        elif should_invoke and not should_succeed:
            status = "failed"
        else:
            status = "success"  # baseline didn't invoke, which is valid

        return ExecutionResult(
            task_id=task.id,
            status=status,
            execution_mode="mock",
            invoked_skill=should_invoke,
            final_url=task.metadata.get("target_url") if should_succeed and should_invoke else None,
            extracted_data=extracted_data,
            actions=actions,
            logs=[f"Mock execution for task {task.id}"],
            stdout=f"Mock executor: processed {task.id}",
            stderr="",
            error=None if status == "success" else "Simulated failure",
            duration_seconds=duration,
            metadata={
                "mock_mode": True,
                "expected_invoked": task.requires_browser,
                "phase1_expected_trigger": expected_trigger,
                "variant": context.variant,
            }
        )
