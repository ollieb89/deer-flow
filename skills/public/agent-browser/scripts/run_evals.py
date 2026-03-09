#!/usr/bin/env python3
"""
Eval runner for agent-browser skill.
Uses executor abstraction to run tests and generates result.json for grading.
"""

import json
import time
import argparse
import traceback
from datetime import datetime
from pathlib import Path

from executor import Executor, MockExecutor, RealExecutor
from grader import Grader

BASE_DIR = Path(__file__).parent.parent
EVALS_FILE = BASE_DIR / "evals" / "evals.json"
WORKSPACE_ROOT = BASE_DIR / "workspace"
SKILL_FILE = BASE_DIR / "SKILL.md"

def load_evals():
    with open(EVALS_FILE, 'r') as f:
        data = json.load(f)
    return data["test_cases"]

def load_skill_description() -> str:
    """Read the current skill description from SKILL.md."""
    if SKILL_FILE.exists():
        return SKILL_FILE.read_text()
    return ""

def ensure_dirs(iteration):
    iteration_dir = WORKSPACE_ROOT / f"iteration-{iteration}"
    for tc_dir in ["baseline", "skill"]:
        (iteration_dir / tc_dir).mkdir(parents=True, exist_ok=True)
    return iteration_dir

def run_with_executor(prompt: str, output_dir: Path, executor: Executor):
    """Execute test case using the provided executor."""
    start = time.time()
    
    try:
        # Execute the prompt through the executor
        # For MockExecutor: will use local fixtures
        # For RealExecutor: will spawn real agent-browser CLI
        result = executor.execute(prompt, output_dir)
        
        # Convert ExecutionResult to dict if needed
        if hasattr(result, 'to_dict'):
            result = result.to_dict()
        
        # Ensure result has the expected structure for grader
        # Should contain:
        # - success (bool)
        # - commands (list of CLI commands executed)
        # - output (stdout/stderr combined)
        # - error (error message if any)
        # - duration (optional, if not provided we'll compute here)
        
        duration = time.time() - start
        if "duration" not in result:
            result["duration"] = duration
            
    except Exception as e:
        duration = time.time() - start
        result = {
            "success": False,
            "commands": [],
            "output": "",
            "error": str(e),
            "duration": duration
        }
    
    # Write result.json for grading
    result_file = output_dir / "result.json"
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    
    return result

def run_eval_for_test_case(test_case, with_skill=True, iteration=1, skill_executor: Executor = None, mock_executor: Executor = None):
    test_id = test_case["id"]
    prompt = test_case["prompt"]
    mode = "skill" if with_skill else "baseline"
    output_dir = WORKSPACE_ROOT / f"iteration-{iteration}" / mode / test_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the test prompt and expected assertions
    with open(output_dir / "prompt.txt", "w") as f:
        f.write(prompt)
    with open(output_dir / "assertions.json", "w") as f:
        json.dump({"assertions": test_case["assertions"]}, f, indent=2)

    if with_skill:
        if not skill_executor:
            raise ValueError("skill_executor required when with_skill=True")
        exec_result = run_with_executor(prompt, output_dir, skill_executor)
    else:
        if not mock_executor:
            raise ValueError("mock_executor required when with_skill=False")
        exec_result = run_with_executor(prompt, output_dir, mock_executor)

    # Run grader to evaluate result.json against assertions.json
    grader_passed = False
    assertion_count = 0
    passed_count = 0
    grader_summary = ""
    assertion_details = []
    grader_error = None
    
    try:
        grader = Grader(output_dir)
        grader.load_data()
        grader_passed, assertion_details, grader_summary = grader.evaluate()
        assertion_count = len(assertion_details)
        passed_count = sum(1 for ar in assertion_details if ar["passed"])
        
        # Save grader results
        grader_results_path = output_dir / "grader_results.json"
        with open(grader_results_path, "w") as f:
            json.dump({
                "passed": grader_passed,
                "assertion_count": assertion_count,
                "passed_count": passed_count,
                "summary": grader_summary,
                "assertions": assertion_details
            }, f, indent=2)
            
    except Exception as e:
        grader_error = str(e) + "\n" + traceback.format_exc()
        grader_summary = f"Grader failed: {e}"

    # Save detailed log
    with open(output_dir / "log.txt", "w") as f:
        f.write(f"Test ID: {test_id}\n")
        f.write(f"Difficulty: {test_case['difficulty']}\n")
        f.write(f"Mode: {mode}\n")
        f.write(f"Start: {datetime.now().isoformat()}\n")
        f.write(f"Executor Success: {exec_result['success']}\n")
        f.write(f"Grader Passed: {grader_passed}\n")
        f.write(f"Assertions: {passed_count}/{assertion_count}\n")
        f.write(f"Duration: {exec_result.get('duration', 0):.2f}s\n")
        f.write(f"Executor Error: {exec_result.get('error', '')}\n")
        if grader_error:
            f.write(f"Grader Error: {grader_error}\n")
        f.write("\n--- Commands ---\n")
        for c in exec_result.get("commands", []):
            f.write(c + "\n")
        f.write("\n--- Output ---\n")
        f.write(exec_result.get("output", ""))
        if grader_summary:
            f.write("\n\n--- Grader Summary ---\n")
            f.write(grader_summary)

    return {
        "test_id": test_id,
        "success": exec_result["success"],  # executor success
        "grader_passed": grader_passed,  # grader evaluation
        "assertion_count": assertion_count,
        "passed_count": passed_count,
        "duration": exec_result.get("duration", 0),
        "commands": exec_result.get("commands", []),
        "error": exec_result.get("error", ""),
        "grader_error": grader_error,
        "grader_summary": grader_summary,
        "assertion_details": assertion_details,
        "output_dir": str(output_dir)
    }

def main():
    parser = argparse.ArgumentParser(description="Run eval suite for agent-browser skill")
    parser.add_argument("--iteration", type=int, default=1, help="Iteration number (for workspace folder)")
    parser.add_argument("--mode", choices=["skill", "baseline", "both"], default="both", help="Which runs to execute")
    parser.add_argument("--limit", type=int, help="Limit number of tests to run")
    parser.add_argument("--dry-run", action="store_true", help="Create workspaces only, skip execution")
    args = parser.parse_args()

    tests = load_evals()
    if args.limit:
        tests = tests[:args.limit]
    
    ensure_dirs(args.iteration)
    
    # Initialize executors
    real_executor = RealExecutor(timeout=60)
    mock_executor = MockExecutor()

    results = {"skill": [], "baseline": []}

    for test in tests:
        print(f"\n[{args.iteration}] Test: {test['id']} ({test['difficulty']})")
        
        if args.dry_run:
            # Just create directories
            if args.mode in ["skill", "both"]:
                (WORKSPACE_ROOT / f"iteration-{args.iteration}" / "skill" / test['id']).mkdir(parents=True, exist_ok=True)
            if args.mode in ["baseline", "both"]:
                (WORKSPACE_ROOT / f"iteration-{args.iteration}" / "baseline" / test['id']).mkdir(parents=True, exist_ok=True)
            print("  [DRY RUN] Skipped")
            continue
            
        if args.mode in ["skill", "both"]:
            res = run_eval_for_test_case(
                test, with_skill=True, iteration=args.iteration,
                skill_executor=real_executor, mock_executor=mock_executor
            )
            results["skill"].append(res)
            print(f"  skill: {'PASS' if res['success'] else 'FAIL'}")
            
        if args.mode in ["baseline", "both"]:
            res = run_eval_for_test_case(
                test, with_skill=False, iteration=args.iteration,
                skill_executor=real_executor, mock_executor=mock_executor
            )
            results["baseline"].append(res)
            print(f"  baseline: {'PASS' if res['success'] else 'FAIL'}")

    # Summary report - include grader pass rates
    def calculate_metrics(result_list):
        total = len(result_list)
        exec_passed = sum(1 for r in result_list if r["success"])
        grader_passed = sum(1 for r in result_list if r.get("grader_passed", False))
        assertions_total = sum(r.get("assertion_count", 0) for r in result_list)
        assertions_passed = sum(r.get("passed_count", 0) for r in result_list)
        return {
            "executor_passed": exec_passed,
            "executor_failed": total - exec_passed,
            "grader_passed": grader_passed,
            "grader_failed": total - grader_passed,
            "assertion_count": assertions_total,
            "assertion_passed": assertions_passed
        }

    summary = {
        "iteration": args.iteration,
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(tests),
        "skill": calculate_metrics(results["skill"]),
        "baseline": calculate_metrics(results["baseline"])
    }

    summary_file = WORKSPACE_ROOT / f"iteration-{args.iteration}" / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== Summary ===")
    skill_metrics = summary['skill']
    baseline_metrics = summary['baseline']
    print(f"Skill Executor: {skill_metrics['executor_passed']}/{summary['total_tests']} passed")
    print(f"Skill Grader: {skill_metrics['grader_passed']}/{summary['total_tests']} passed")
    print(f"Baseline Executor: {baseline_metrics['executor_passed']}/{summary['total_tests']} passed")
    print(f"Baseline Grader: {baseline_metrics['grader_passed']}/{summary['total_tests']} passed")
    print(f"Total Assertions: {skill_metrics['assertion_passed']}/{skill_metrics['assertion_count']}")
    print(f"Workspace: {WORKSPACE_ROOT / f'iteration-{args.iteration}'}")

if __name__ == "__main__":
    main()
