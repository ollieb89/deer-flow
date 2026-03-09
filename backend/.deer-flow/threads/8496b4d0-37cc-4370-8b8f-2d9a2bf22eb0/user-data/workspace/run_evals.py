#!/usr/bin/env python3
"""Unified two-phase evaluation runner for browser skill evaluation.

Runs a task through an executor, persists result.json, and invokes grader to produce grade.json.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from models import TaskDefinition, ExecutionContext, ExecutionResult
from executors.mock_executor import MockBrowserExecutor
from executors.cli_executor import AgentBrowserCLIExecutor
from grader import Grader, load_task_fixture, write_grade


def setup_workspace(base_workspace: Path, iteration: int, variant: str, test_id: str) -> Path:
    """Create workspace directory for this execution."""
    iteration_dir = base_workspace / f"iteration-{iteration}"
    variant_dir = iteration_dir / variant
    test_dir = variant_dir / test_id
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def run_single_evaluation(
    fixture_dir: Path,
    workspace_dir: Path,
    variant: str,
    iteration: int,
    executor_name: str,
    cli_path: str | None = None,
    timeout: int = 120
) -> tuple[ExecutionResult, Path]:
    """
    Run a single evaluation for a task fixture.

    Returns:
        (ExecutionResult, grade_json_path)
    """
    # Load fixture
    task, metadata, assertions = load_task_fixture(fixture_dir)
    test_id = task.id

    # Create workspace
    test_workspace = setup_workspace(workspace_dir, iteration, variant, test_id)

    # Select executor
    if executor_name == "mock":
        executor = MockBrowserExecutor()
    elif executor_name == "agent_browser_cli":
        executor = AgentBrowserCLIExecutor(cli_path=cli_path or "agent-browser")
    else:
        raise ValueError(f"Unknown executor: {executor_name}")

    # Build execution context
    env_vars = metadata.get("environment", {}).get("env_vars", {})
    context = ExecutionContext(
        variant=variant,
        iteration=iteration,
        workspace_dir=test_workspace,
        timeout_seconds=timeout,
        env=env_vars
    )

    # Execute
    result = executor.run(task, context)

    # Add variant and fixture metadata to result.metadata
    result.metadata["variant"] = variant
    result.metadata["iteration"] = iteration
    result.metadata["fixture_dir"] = str(fixture_dir)

    # Persist result.json
    result_path = test_workspace / "result.json"
    with open(result_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    # Grade
    grader = Grader()
    grade = grader.grade(result, assertions, metadata)

    # Append grade metadata
    grade.metadata["variant"] = variant
    grade.metadata["iteration"] = iteration
    grade.metadata["fixture_dir"] = str(fixture_dir)
    grade.metadata["executor"] = executor_name
    grade.metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Persist grade.json
    grade_path = test_workspace / "grade.json"
    write_grade(grade, grade_path)

    return result, grade_path


def run_benchmark(
    fixtures_dir: Path,
    workspace_dir: Path,
    variant: str,
    iteration: int,
    executor_name: str,
    cli_path: str | None = None,
    timeout: int = 120,
) -> list[Path]:
    """
    Run all task fixtures in a directory.

    Args:
        fixtures_dir: Directory containing test fixture subdirectories
        workspace_dir: Root workspace path
        variant: "baseline" or "skill"
        iteration: Iteration number
        executor_name: "mock" or "agent_browser_cli"
        cli_path: Path to agent-browser CLI (if using cli executor)
        timeout: Timeout in seconds

    Returns:
        List of grade.json paths for later aggregation
    """
    grade_files = []

    # Iterate over subdirectories (each should be a test with task.json)
    for fixture_subdir in sorted(fixtures_dir.iterdir()):
        if not fixture_subdir.is_dir():
            continue
        if not (fixture_subdir / "task.json").exists():
            continue

        print(f"Running {variant} iteration {iteration} on {fixture_subdir.name}...")
        try:
            _, grade_path = run_single_evaluation(
                fixture_subdir,
                workspace_dir,
                variant,
                iteration,
                executor_name,
                cli_path=cli_path,
                timeout=timeout
            )
            grade_files.append(grade_path)
        except Exception as e:
            print(f"Error running {fixture_subdir.name}: {e}", file=sys.stderr)
            # Still create an empty grade file or log error
            test_workspace = setup_workspace(workspace_dir, iteration, variant, fixture_subdir.name)
            error_grade = {
                "task_id": fixture_subdir.name,
                "overall_passed": False,
                "error": str(e),
                "metadata": {"variant": variant, "iteration": iteration}
            }
            grade_path = test_workspace / "grade.json"
            with open(grade_path, "w") as f:
                json.dump(error_grade, f, indent=2)
            grade_files.append(grade_path)

    return grade_files


def parse_args():
    parser = argparse.ArgumentParser(description="Run unified browser skill evaluation")
    parser.add_argument(
        "fixtures_dir",
        type=Path,
        help="Directory containing task fixture subdirectories"
    )
    parser.add_argument(
        "workspace_dir",
        type=Path,
        help="Root workspace directory"
    )
    parser.add_argument(
        "--variant",
        type=str,
        required=True,
        choices=["baseline", "skill"],
        help="Evaluation variant: baseline (without skill) or skill (with skill)"
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=0,
        help="Iteration number (default 0)"
    )
    parser.add_argument(
        "--executor",
        type=str,
        default="mock",
        choices=["mock", "agent_browser_cli"],
        help="Executor to use (default: mock)"
    )
    parser.add_argument(
        "--cli-path",
        type=str,
        default=None,
        help="Path to agent-browser CLI (required if executor is agent_browser_cli)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Execution timeout in seconds (default 120)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.executor == "agent_browser_cli" and not args.cli_path:
        print("Error: --cli-path is required when using agent_browser_cli executor", file=sys.stderr)
        sys.exit(1)

    grade_files = run_benchmark(
        fixtures_dir=args.fixtures_dir,
        workspace_dir=args.workspace_dir,
        variant=args.variant,
        iteration=args.iteration,
        executor_name=args.executor,
        cli_path=args.cli_path,
        timeout=args.timeout
    )

    print(f"\nCompleted {len(grade_files)} evaluations.")
    print(f"Results in: {args.workspace_dir}/iteration-{args.iteration}/{args.variant}/")
    print("Grade files:", ", ".join(str(p) for p in grade_files[:5]))


if __name__ == "__main__":
    main()
