#!/usr/bin/env python3
"""
Aggregate Benchmark: Iterates over test workspaces, runs grading, and generates reports.
Supports multi-iteration comparison between baseline and optimized skill descriptions.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
from collections import defaultdict

from grader import Grader


class TestResult:
    """Container for individual test results."""
    def __init__(self, test_id: str, difficulty: str, iteration: int, variant: str):
        self.test_id = test_id
        self.difficulty = difficulty
        self.iteration = iteration
        self.variant = variant  # 'baseline' or 'skill'
        self.passed = False
        self.assertion_count = 0
        self.passed_count = 0
        self.assertion_details: List[Dict[str, Any]] = []
        self.duration = 0.0
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "difficulty": self.difficulty,
            "iteration": self.iteration,
            "variant": self.variant,
            "passed": self.passed,
            "assertion_count": self.assertion_count,
            "passed_count": self.passed_count,
            "duration": self.duration,
            "error": self.error
        }


class BenchmarkAggregator:
    """Main aggregator for evaluation results."""
    
    def __init__(self, workspace_root: Path, output_dir: Path = None):
        self.workspace_root = Path(workspace_root)
        self.output_dir = output_dir or (self.workspace_root / ".." / "outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TestResult] = []
        self.test_metadata: Dict[str, Dict[str, Any]] = {}
    
    def discover_workspaces(self) -> List[Tuple[Path, int, str, str]]:
        """
        Discover all test workspace directories.
        Expected pattern: workspace/iteration-{n}/{variant}/{test_id}/
        Returns list of (workspace_path, iteration, variant, test_id)
        """
        workspaces = []
        
        if not self.workspace_root.exists():
            raise FileNotFoundError(f"Workspace root not found: {self.workspace_root}")
        
        for iter_dir in sorted(self.workspace_root.iterdir()):
            if not iter_dir.is_dir() or not iter_dir.name.startswith("iteration-"):
                continue
            try:
                iteration = int(iter_dir.name.split("-")[1])
            except (IndexError, ValueError):
                continue
            
            for variant_dir in sorted(iter_dir.iterdir()):
                if not variant_dir.is_dir() or variant_dir.name not in ["baseline", "skill"]:
                    continue
                variant = variant_dir.name
                
                for test_dir in sorted(variant_dir.iterdir()):
                    if not test_dir.is_dir():
                        continue
                    test_id = test_dir.name
                    workspaces.append((test_dir, iteration, variant, test_id))
        
        return workspaces
    
    def load_eval_suite_metadata(self, evals_json_path: Path):
        """Load test case metadata from evals.json."""
        if not evals_json_path.exists():
            return
        
        with open(evals_json_path) as f:
            data = json.load(f)
            for test in data.get("test_cases", []):
                self.test_metadata[test["id"]] = {
                    "difficulty": test.get("difficulty", "unknown"),
                    "description": test.get("expected_behavior", ""),
                    "tags": test.get("tags", [])
                }
    
    def run_grading(self, workspace_path: Path) -> TestResult:
        """Run grader on a single workspace and return TestResult."""
        test_id = workspace_path.name
        variant = workspace_path.parent.name
        iteration = workspace_path.parent.parent.name.split("-")[1]
        
        result = TestResult(test_id, "unknown", iteration, variant)
        
        try:
            grader = Grader(workspace_path)
            grader.load_data()
            passed, assertion_results, summary = grader.evaluate()
            
            result.passed = passed
            result.assertion_count = len(assertion_results)
            result.passed_count = sum(1 for ar in assertion_results if ar["passed"])
            result.assertion_details = assertion_results
            
            # Add difficulty from metadata
            if test_id in self.test_metadata:
                result.difficulty = self.test_metadata[test_id]["difficulty"]
            
            # Log summary
            print(f"[{variant}] iteration-{iteration}/{test_id}: {summary}")
            
        except Exception as e:
            result.error = str(e)
            print(f"[ERROR] {variant}/{test_id}: {e}")
        
        return result
    
    def aggregate_all(self) -> Dict[str, Any]:
        """Run grading on all discovered workspaces and aggregate results."""
        workspaces = self.discover_workspaces()
        
        if not workspaces:
            print("No workspaces found to evaluate.")
            return {}
        
        print(f"Found {len(workspaces)} workspaces to evaluate.")
        
        # Clear previous results
        self.results = []
        
        for ws_path, iteration, variant, test_id in workspaces:
            result = self.run_grading(ws_path)
            self.results.append(result)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        if not self.results:
            return {"error": "No results to report"}
        
        # Group by iteration and variant
        grouped: Dict[int, Dict[str, List[TestResult]]] = defaultdict(lambda: defaultdict(list))
        for r in self.results:
            grouped[r.iteration][r.variant].append(r)
        
        # Compute metrics
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "iterations": {},
            "summary": {}
        }
        
        overall_summary = {
            "total_tests": len(self.results),
            "overall_pass_rate": 0,
            "by_difficulty": defaultdict(lambda: {"total": 0, "passed": 0}),
            "by_variant": defaultdict(lambda: {"total": 0, "passed": 0})
        }
        
        for iter_num, variants in grouped.items():
            iter_report = {"baseline": None, "skill": None}
            
            for variant, results in variants.items():
                metrics = self._compute_metrics(results)
                iter_report[variant] = metrics
                
                # Accumulate into overall
                overall_summary["by_variant"][variant]["total"] += metrics["total_tests"]
                overall_summary["by_variant"][variant]["passed"] += metrics["passed_tests"]
                
                for diff, diff_metrics in metrics["by_difficulty"].items():
                    overall_summary["by_difficulty"][diff]["total"] += diff_metrics["total"]
                    overall_summary["by_difficulty"][diff]["passed"] += diff_metrics["passed"]
            
            report["iterations"][iter_num] = iter_report
        
        # Compute overall pass rate
        total_tests = overall_summary["total_tests"] = len(self.results)
        total_passed = sum(
            sum(1 for r in self.results if r.passed)
        )
        overall_summary["overall_pass_rate"] = total_passed / total_tests if total_tests > 0 else 0
        
        # Convert difficulty defaultdict to regular dict
        overall_summary["by_difficulty"] = dict(overall_summary["by_difficulty"])
        for diff in overall_summary["by_difficulty"]:
            data = overall_summary["by_difficulty"][diff]
            data["pass_rate"] = data["passed"] / data["total"] if data["total"] > 0 else 0
        
        report["summary"] = overall_summary
        
        # Save JSON report
        json_path = self.output_dir / "benchmark_report.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nJSON report saved to: {json_path}")
        
        # Generate Markdown summary
        md_report = self._generate_markdown(report)
        md_path = self.output_dir / "benchmark_report.md"
        with open(md_path, "w") as f:
            f.write(md_report)
        print(f"Markdown report saved to: {md_path}")
        
        return report
    
    def _compute_metrics(self, results: List[TestResult]) -> Dict[str, Any]:
        """Compute metrics for a set of results."""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        
        by_difficulty = defaultdict(lambda: {"total": 0, "passed": 0})
        for r in results:
            by_difficulty[r.difficulty]["total"] += 1
            if r.passed:
                by_difficulty[r.difficulty]["passed"] += 1
        
        # Convert to regular dicts with pass rates
        by_diff_dict = {}
        for diff, data in by_difficulty.items():
            by_diff_dict[diff] = {
                "total": data["total"],
                "passed": data["passed"],
                "pass_rate": data["passed"] / data["total"] if data["total"] > 0 else 0
            }
        
        avg_duration = sum(r.duration for r in results) / total if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "fail_tests": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "by_difficulty": by_diff_dict,
            "avg_duration": avg_duration,
            "results": [r.to_dict() for r in results]
        }
    
    def _generate_markdown(self, report: Dict[str, Any]) -> str:
        """Generate human-readable markdown report."""
        lines = [
            "# Agent-Browser Skill Benchmark Report",
            f"Generated: {report['timestamp']}",
            "",
            "## Overall Summary",
            f"- **Total Tests:** {report['summary']['total_tests']}",
            f"- **Overall Pass Rate:** {report['summary']['overall_pass_rate']:.1%}",
            "",
            "### By Difficulty",
        ]
        
        for diff, data in sorted(report['summary']['by_difficulty'].items()):
            lines.append(f"- **{diff}**: {data['passed']}/{data['total']} ({data['pass_rate']:.1%})")
        
        lines.extend([
            "",
            "### By Variant",
        ])
        for variant, data in sorted(report['summary']['by_variant'].items()):
            lines.append(f"- **{variant}**: {data['passed']}/{data['total']} ({data['passed']/data['total'] if data['total'] > 0 else 0:.1%})")
        
        lines.append("")
        lines.append("## Iteration Breakdown")
        
        for iter_num in sorted(report['iterations'].keys()):
            iter_data = report['iterations'][iter_num]
            lines.append(f"### Iteration {iter_num}")
            
            for variant in ['baseline', 'skill']:
                if variant not in iter_data or iter_data[variant] is None:
                    continue
                vdata = iter_data[variant]
                lines.append(f"- **{variant}**: {vdata['passed_tests']}/{vdata['total_tests']} ({vdata['pass_rate']:.1%})")
            lines.append("")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Aggregate agent-browser evaluation results.")
    parser.add_argument(
        "--workspace",
        type=str,
        default="/mnt/skills/public/agent-browser/workspace",
        help="Root workspace directory containing iteration-{n}/{variant}/{test_id}/"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for reports (default: workspace/../outputs)"
    )
    parser.add_argument(
        "--evals",
        type=str,
        default="/mnt/skills/public/agent-browser/evals/evals.json",
        help="Path to evals.json for test metadata"
    )
    
    args = parser.parse_args()
    
    workspace_path = Path(args.workspace)
    output_dir = Path(args.output) if args.output else None
    evals_path = Path(args.evals)
    
    aggregator = BenchmarkAggregator(workspace_path, output_dir)
    aggregator.load_eval_suite_metadata(evals_path)
    
    report = aggregator.aggregate_all()
    
    if report and "error" not in report:
        print("\n=== Benchmark Complete ===")
        print(f"Overall Pass Rate: {report['summary']['overall_pass_rate']:.1%}")
    else:
        print("\n=== Benchmark Failed ===")
        print(report.get("error", "Unknown error"))


if __name__ == "__main__":
    main()
