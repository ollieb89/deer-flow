#!/usr/bin/env python3
"""Benchmark aggregation tool for two-phase evaluation results.

Aggregates grade.json files across iterations and computes:
- Success rates per variant (baseline vs skill)
- Task completion metrics
- Phase 1 metrics (precision, recall, F1) if applicable
- Score distributions
- Comparative deltas
"""
import argparse
import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from grader import Grade


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a variant or comparison."""
    variant: str
    total_tasks: int = 0
    success_count: int = 0
    failed_count: int = 0
    timeout_count: int = 0
    error_count: int = 0

    # Overall metrics
    success_rate: float = 0.0
    average_score: float = 0.0
    score_stdev: float = 0.0
    average_duration: float = 0.0

    # Phase 1 metrics (trigger precision/recall/F1) - computed if metadata provides expectations
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None

    # Iteration breakdown
    iterations: dict[int, dict[str, Any]] = field(default_factory=dict)

    # Per-task breakdown
    task_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "variant": self.variant,
            "total_tasks": self.total_tasks,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "timeout_count": self.timeout_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate, 4),
            "average_score": round(self.average_score, 4),
            "score_stdev": round(self.score_stdev, 4),
            "average_duration": round(self.average_duration, 4),
            "iterations": self.iterations,
            "task_breakdown": self.task_breakdown,
            "metadata": self.metadata,
        }
        if self.precision is not None:
            d["precision"] = round(self.precision, 4)
        if self.recall is not None:
            d["recall"] = round(self.recall, 4)
        if self.f1 is not None:
            d["f1"] = round(self.f1, 4)
        return d


def load_all_grades(workspace_dir: Path, iteration: int | None = None) -> dict[str, list[dict[str, Any]]]:
    """
    Load all grade.json files from the workspace.

    Returns:
        Dict mapping variant -> list of grade data dicts
    """
    grades_by_variant = defaultdict(list)

    iterations = [workspace_dir / f"iteration-{iteration}"] if iteration is not None \
        else sorted([d for d in workspace_dir.iterdir() if d.is_dir() and d.name.startswith("iteration-")])

    for iter_dir in iterations:
        if not iter_dir.exists():
            continue
        iter_num = int(iter_dir.name.split("-")[1])
        for variant_dir in iter_dir.iterdir():
            if not variant_dir.is_dir():
                continue
            variant = variant_dir.name
            for test_dir in variant_dir.iterdir():
                grade_file = test_dir / "grade.json"
                if grade_file.exists():
                    with open(grade_file) as f:
                        grade_data = json.load(f)
                    grade_data["_workspace_path"] = str(grade_file)
                    grade_data["_variant"] = variant
                    grade_data["_iteration"] = iter_num
                    grades_by_variant[variant].append(grade_data)

    return grades_by_variant


def load_all_results(workspace_dir: Path, iteration: int | None = None) -> dict[str, list[dict[str, Any]]]:
    """Load all result.json files for detailed analysis."""
    results_by_variant = defaultdict(list)

    iterations = [workspace_dir / f"iteration-{iteration}"] if iteration is not None \
        else sorted([d for d in workspace_dir.iterdir() if d.is_dir() and d.name.startswith("iteration-")])

    for iter_dir in iterations:
        if not iter_dir.exists():
            continue
        iter_num = int(iter_dir.name.split("-")[1])
        for variant_dir in iter_dir.iterdir():
            if not variant_dir.is_dir():
                continue
            variant = variant_dir.name
            for test_dir in variant_dir.iterdir():
                result_file = test_dir / "result.json"
                if result_file.exists():
                    with open(result_file) as f:
                        result_data = json.load(f)
                    result_data["_variant"] = variant
                    result_data["_iteration"] = iter_num
                    results_by_variant[variant].append(result_data)

    return results_by_variant


def aggregate_variant(variant: str, grades: list[dict[str, Any]]) -> AggregatedMetrics:
    """Compute aggregated metrics for a single variant."""
    metrics = AggregatedMetrics(variant=variant)

    total = len(grades)
    metrics.total_tasks = total

    if total == 0:
        return metrics

    # Count outcomes
    for g in grades:
        status = g.get("status", "error")
        if status == "success":
            metrics.success_count += 1
        elif status == "failed":
            metrics.failed_count += 1
        elif status == "timeout":
            metrics.timeout_count += 1
        else:
            metrics.error_count += 1

    metrics.success_rate = metrics.success_count / total

    # Average score
    scores = [g.get("score", 0.0) for g in grades]
    metrics.average_score = statistics.mean(scores) if scores else 0.0
    metrics.score_stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0

    # Average duration
    durations = [g.get("metadata", {}).get("duration_seconds", 0) for g in grades]
    metrics.average_duration = statistics.mean(durations) if durations else 0.0

    # Iteration grouping
    iter_groups = defaultdict(list)
    for g in grades:
        iter_num = g.get("_iteration", 0)
        iter_groups[iter_num].append(g)

    for iter_num, iter_grades in iter_groups.items():
        iter_scores = [g.get("score", 0.0) for g in iter_grades]
        iter_success = sum(1 for g in iter_grades if g.get("status") == "success")
        metrics.iterations[iter_num] = {
            "count": len(iter_grades),
            "success_count": iter_success,
            "success_rate": iter_success / len(iter_grades) if iter_grades else 0.0,
            "average_score": statistics.mean(iter_scores) if iter_scores else 0.0,
        }

    # Per-task breakdown
    task_groups = defaultdict(list)
    for g in grades:
        task_id = g.get("task_id", "unknown")
        task_groups[task_id].append(g)

    for task_id, task_grades in task_groups.items():
        latest = max(task_grades, key=lambda g: (g.get("_iteration", 0), g.get("_variant", "")))
        metrics.task_breakdown[task_id] = {
            "status": latest.get("status"),
            "score": latest.get("score", 0.0),
            "iterations_test_count": len(task_grades),
            "best_score": max(g.get("score", 0.0) for g in task_grades),
        }

    return metrics


def compute_phase1_metrics(
    workspace_dir: Path,
    iteration: int | None,
    grades_by_variant: dict[str, list[dict[str, Any]]],
    metrics_by_variant: dict[str, AggregatedMetrics]
) -> dict[str, AggregatedMetrics]:
    """
    Compute Phase 1 precision/recall/F1 based on invoked_skill expectations from metadata.
    Loads result.json files to get actual invoked_skill for each task.

    Args:
        workspace_dir: Root workspace path
        iteration: Optional specific iteration
        grades_by_variant: Dict of variant -> list of grade dicts (each may have metadata.phase1.expected_trigger)
        metrics_by_variant: Dict of variant -> AggregatedMetrics (will be augmented in-place)

    Returns:
        Updated metrics_by_variant (with Phase 1 metrics on the 'skill' variant).
    """
    # Load all result.json files to access invoked_skill flags
    results_by_variant = load_all_results(workspace_dir, iteration)

    # Need both skill and baseline results
    if "skill" not in results_by_variant or "baseline" not in results_by_variant:
        print("Skipping Phase 1 metrics: both 'baseline' and 'skill' variant results are required.")
        return metrics_by_variant

    # Build expected_trigger map from grades (same across variants for a given task)
    expected_trigger_by_task: dict[str, bool] = {}
    for grades in grades_by_variant.values():
        for g in grades:
            tid = g.get("task_id")
            if not tid:
                continue
            if tid in expected_trigger_by_task:
                continue
            phase1 = g.get("metadata", {}).get("phase1", {})
            if "expected_trigger" in phase1:
                expected_trigger_by_task[tid] = phase1["expected_trigger"]

    if not expected_trigger_by_task:
        print("Skipping Phase 1 metrics: no metadata.phase1.expected_trigger found in grades.")
        return metrics_by_variant

    # Map by task_id
    skill_results = {r["task_id"]: r for r in results_by_variant["skill"] if "task_id" in r}
    baseline_results = {r["task_id"]: r for r in results_by_variant["baseline"] if "task_id" in r}

    # Common tasks: have expected trigger, skill result, and baseline result
    common_tasks = set(expected_trigger_by_task.keys()) & set(skill_results.keys()) & set(baseline_results.keys())

    # Compute confusion matrix for skill variant (true positives, false positives, false negatives, true negatives)
    tp = fp = tn = fn = 0
    for task_id in common_tasks:
        expected = expected_trigger_by_task[task_id]
        skill_invoked = skill_results[task_id].get("invoked_skill", False)

        if expected and skill_invoked:
            tp += 1
        elif expected and not skill_invoked:
            fn += 1
        elif not expected and skill_invoked:
            fp += 1
        else:
            tn += 1

    # Compute precision, recall, F1
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = (2 * precision * recall) / (precision + recall)
    else:
        f1 = None

    # Augment the 'skill' AggregatedMetrics
    if "skill" in metrics_by_variant:
        metrics_by_variant["skill"].precision = precision
        metrics_by_variant["skill"].recall = recall
        metrics_by_variant["skill"].f1 = f1

    return metrics_by_variant


def generate_comparison(metrics_by_variant: dict[str, AggregatedMetrics]) -> dict[str, Any]:
    """Generate comparison delta between baseline and skill."""
    if "baseline" not in metrics_by_variant or "skill" not in metrics_by_variant:
        return {"error": "Comparison requires both baseline and skill variants"}

    baseline = metrics_by_variant["baseline"]
    skill = metrics_by_variant["skill"]

    comparison = {
        "success_rate_delta": round(skill.success_rate - baseline.success_rate, 4),
        "average_score_delta": round(skill.average_score - baseline.average_score, 4),
        "average_duration_delta": round(skill.average_duration - baseline.average_duration, 4),
        "baseline_success_rate": baseline.success_rate,
        "skill_success_rate": skill.success_rate,
        "baseline_average_score": baseline.average_score,
        "skill_average_score": skill.average_score,
        "relative_improvement_score": (
            round((skill.average_score - baseline.average_score) / baseline.average_score, 4)
            if baseline.average_score > 0 else None
        ),
    }

    # Task-level improvement
    improved_tasks = 0
    degraded_tasks = 0
    for task_id in baseline.task_breakdown:
        if task_id in skill.task_breakdown:
            b_delta = baseline.task_breakdown[task_id].get("score", 0)
            s_delta = skill.task_breakdown[task_id].get("score", 0)
            if s_delta > b_delta + 0.01:
                improved_tasks += 1
            elif s_delta < b_delta - 0.01:
                degraded_tasks += 1

    comparison["improved_tasks_count"] = improved_tasks
    comparison["degraded_tasks_count"] = degraded_tasks
    comparison["unchanged_tasks_count"] = (
        len(set(baseline.task_breakdown.keys()) & set(skill.task_breakdown.keys())) - improved_tasks - degraded_tasks
    )

    return comparison


def generate_summary_text(metrics_by_variant: dict[str, AggregatedMetrics], comparison: dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("BENCHMARK SUMMARY")
    lines.append("=" * 60)

    for variant_name in ["baseline", "skill"]:
        if variant_name not in metrics_by_variant:
            continue
        m = metrics_by_variant[variant_name]
        lines.append(f"\n{variant_name.upper()}:")
        lines.append(f"  Total tasks: {m.total_tasks}")
        lines.append(f"  Success rate: {m.success_rate:.2%} ({m.success_count}/{m.total_tasks})")
        lines.append(f"  Average score: {m.average_score:.3f} ± {m.score_stdev:.3f}")
        lines.append(f"  Average duration: {m.average_duration:.1f}s")
        lines.append(f"  Score range: min={min(task['score'] for task in m.task_breakdown.values()):.3f}, "
                     f"max={max(task['score'] for task in m.task_breakdown.values()):.3f}")

    if comparison:
        lines.append("\nCOMPARISON (skill vs baseline):")
        lines.append(f"  Success rate delta: {comparison['success_rate_delta']:+.2%}")
        lines.append(f"  Average score delta: {comparison['average_score_delta']:+.4f}")
        lines.append(f"  Relative improvement: {comparison['relative_improvement_score']:+.2%}" if comparison.get('relative_improvement_score') else "  Relative improvement: N/A")
        lines.append(f"  Tasks improved: {comparison['improved_tasks_count']}")
        lines.append(f"  Tasks degraded: {comparison['degraded_tasks_count']}")
        lines.append(f"  Tasks unchanged: {comparison['unchanged_tasks_count']}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Aggregate benchmark results from evaluation runs")
    parser.add_argument(
        "workspace_dir",
        type=Path,
        help="Workspace directory containing iteration-* subdirectories"
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=None,
        help="Specific iteration to aggregate (default: all)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("aggregated_metrics.json"),
        help="Output JSON file for aggregated metrics"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print human-readable summary to stdout"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load all grades
    grades_by_variant = load_all_grades(args.workspace_dir, args.iteration)

    if not any(grades_by_variant.values()):
        print("No grade.json files found in workspace. Check workspace structure.")
        return

    print(f"Loaded {sum(len(g) for g in grades_by_variant.values())} grade files.")

    # Aggregate per-variant metrics
    metrics_by_variant: dict[str, AggregatedMetrics] = {}
    for variant, grades in grades_by_variant.items():
        print(f"Aggregating {variant}...")
        metrics = aggregate_variant(variant, grades)
        metrics_by_variant[variant] = metrics

    # Add Phase 1 metrics if applicable
    metrics_by_variant = compute_phase1_metrics(args.workspace_dir, args.iteration, grades_by_variant, metrics_by_variant)

    # Generate comparison if both variants exist
    comparison = {}
    if "baseline" in metrics_by_variant and "skill" in metrics_by_variant:
        comparison = generate_comparison(metrics_by_variant)
        print("Comparison (skill vs baseline):")
        for k, v in comparison.items():
            print(f"  {k}: {v}")

    # Build final aggregate
    aggregated = {
        "by_variant": {v: metrics.to_dict() for v, metrics in metrics_by_variant.items()},
        "comparison": comparison,
        "timestamp": datetime.now().isoformat() + "Z",
        "workspace": str(args.workspace_dir),
        "iteration_filter": args.iteration,
    }

    # Write to output
    with open(args.output, "w") as f:
        json.dump(aggregated, f, indent=2)
    print(f"\nAggregated metrics written to: {args.output}")

    # Print summary if requested
    if args.summary:
        print(generate_summary_text(metrics_by_variant, comparison))


if __name__ == "__main__":
    main()
