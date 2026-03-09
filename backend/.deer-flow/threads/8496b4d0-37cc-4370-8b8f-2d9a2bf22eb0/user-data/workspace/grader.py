"""Assertion-based grader for evaluation tasks."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from models import ExecutionResult, TaskDefinition


@dataclass
class AssertionResult:
    """Result of a single assertion evaluation"""
    assertion_type: str
    passed: bool
    message: str
    expected: Any = None
    actual: Any = None


@dataclass
class Grade:
    """Final structured grade for a task"""
    task_id: str
    overall_passed: bool
    assertion_results: list[AssertionResult] = field(default_factory=list)
    assertion_pass_count: int = 0
    assertion_total_count: int = 0
    score: float = 0.0  # normalized score 0-1
    rubric_scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "overall_passed": self.overall_passed,
            "assertion_results": [
                {
                    "assertion_type": ar.assertion_type,
                    "passed": ar.passed,
                    "message": ar.message,
                    "expected": ar.expected,
                    "actual": ar.actual,
                }
                for ar in self.assertion_results
            ],
            "assertion_pass_count": self.assertion_pass_count,
            "assertion_total_count": self.assertion_total_count,
            "score": self.score,
            "rubric_scores": self.rubric_scores,
            "metadata": self.metadata,
        }


class AssertionEvaluator:
    """Evaluates individual assertion types against execution results."""

    def evaluate(self, assertion: dict[str, Any], result: ExecutionResult) -> AssertionResult:
        """Evaluate a single assertion."""
        assertion_type = assertion.get("type")
        expected = assertion.get("expected")
        field_name = assertion.get("field")

        evaluators = {
            "final_url_equals": self._check_final_url_equals,
            "result_field_equals": self._check_result_field_equals,
            "final_url_contains": self._check_final_url_contains,
            "text_contains": self._check_text_contains,
            "status_equals": self._check_status_equals,
            "invoked_skill_equals": self._check_invoked_skill_equals,
        }

        if assertion_type not in evaluators:
            return AssertionResult(
                assertion_type=assertion_type,
                passed=False,
                message=f"Unknown assertion type: {assertion_type}",
                expected=expected,
                actual=None
            )

        return evaluators[assertion_type](expected, result, field_name)

    def _check_final_url_equals(self, expected: str, result: ExecutionResult, _: Any) -> AssertionResult:
        actual = result.final_url
        passed = actual == expected
        return AssertionResult(
            assertion_type="final_url_equals",
            passed=passed,
            message=f"Final URL {'matches' if passed else 'does not match'} expected value",
            expected=expected,
            actual=actual
        )

    def _check_result_field_equals(self, expected: Any, result: ExecutionResult, field_name: str) -> AssertionResult:
        actual = self._get_nested_field(result.extracted_data, field_name)
        passed = actual == expected
        return AssertionResult(
            assertion_type="result_field_equals",
            passed=passed,
            message=f"Field '{field_name}' {'matches' if passed else 'does not match'} expected value",
            expected=expected,
            actual=actual
        )

    def _get_nested_field(self, data: dict[str, Any], field_path: str) -> Any:
        """Get nested field using dot notation, e.g., 'extracted_data.heading'."""
        if not data:
            return None
        parts = field_path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value

    def _check_final_url_contains(self, expected_substring: str, result: ExecutionResult, _: Any) -> AssertionResult:
        actual = result.final_url or ""
        passed = expected_substring in actual
        return AssertionResult(
            assertion_type="final_url_contains",
            passed=passed,
            message=f"Final URL {'contains' if passed else 'does not contain'} '{expected_substring}'",
            expected=expected_substring,
            actual=actual
        )

    def _check_text_contains(self, expected_substring: str, result: ExecutionResult, _: Any) -> AssertionResult:
        # Search through logs and extracted_data for the text
        searchable = " ".join(result.logs) + " " + json.dumps(result.extracted_data)
        passed = expected_substring in searchable
        return AssertionResult(
            assertion_type="text_contains",
            passed=passed,
            message=f"Output {'contains' if passed else 'does not contain'} '{expected_substring}'",
            expected=expected_substring,
            actual="(text content)" if passed else "(text not found)"
        )

    def _check_status_equals(self, expected: str, result: ExecutionResult, _: Any) -> AssertionResult:
        actual = result.status
        passed = actual == expected
        return AssertionResult(
            assertion_type="status_equals",
            passed=passed,
            message=f"Status {'matches' if passed else 'does not match'} expected value",
            expected=expected,
            actual=actual
        )

    def _check_invoked_skill_equals(self, expected: bool, result: ExecutionResult, _: Any) -> AssertionResult:
        actual = result.invoked_skill
        passed = actual == expected
        return AssertionResult(
            assertion_type="invoked_skill_equals",
            passed=passed,
            message=f"Invoked skill {'matches' if passed else 'does not match'} expected value",
            expected=expected,
            actual=actual
        )


class Grader:
    """Main grader that evaluates execution results against task assertions."""

    def __init__(self):
        self.evaluator = AssertionEvaluator()

    def grade(
        self,
        result: ExecutionResult,
        assertions: list[dict[str, Any]],
        task_metadata: dict[str, Any] | None = None
    ) -> Grade:
        """
        Grade an execution result against assertions.

        Args:
            result: Execution result from executor
            assertions: List of assertion objects from assertions.json
            task_metadata: Optional metadata from metadata.json

        Returns:
            Grade object with evaluation results
        """
        assertion_results = []
        for assertion in assertions:
            ar = self.evaluator.evaluate(assertion, result)
            assertion_results.append(ar)

        pass_count = sum(1 for ar in assertion_results if ar.passed)
        total_count = len(assertion_results)
        score = pass_count / total_count if total_count > 0 else 0.0
        overall_passed = pass_count == total_count  # all must pass

        # Check phase1 expectations if present in metadata
        phase1_meta = (task_metadata or {}).get("phase1", {})
        expected_trigger = phase1_meta.get("expected_trigger")
        if expected_trigger is not None:
            # Add an implicit assertion about trigger correctness
            trigger_ar = self.evaluator._check_invoked_skill_equals(
                expected_trigger, result, None
            )
            assertion_results.append(trigger_ar)
            # Recompute totals
            pass_count = sum(1 for ar in assertion_results if ar.passed)
            total_count = len(assertion_results)
            score = pass_count / total_count if total_count > 0 else 0.0
            overall_passed = pass_count == total_count

        # Optional rubric evaluation (structured only)
        rubric_scores = self._evaluate_rubric(result, task_metadata or {})

        grade = Grade(
            task_id=result.task_id,
            overall_passed=overall_passed,
            assertion_results=assertion_results,
            assertion_pass_count=pass_count,
            assertion_total_count=total_count,
            score=score,
            rubric_scores=rubric_scores,
            metadata={
                "variant": result.metadata.get("variant"),
                "execution_mode": result.execution_mode,
                "duration_seconds": result.duration_seconds,
            }
        )

        return grade

    def _evaluate_rubric(self, result: ExecutionResult, task_metadata: dict[str, Any]) -> dict[str, float]:
        """Evaluate optional structured rubric fields."""
        rubric_scores = {}
        rubric = task_metadata.get("rubric", {})

        # Task completion: did status indicate success?
        if "task_completion" in rubric:
            completion_score = 1.0 if result.status == "success" else 0.0
            rubric_scores["task_completion"] = completion_score

        # Efficiency: time-based scoring if threshold defined
        if "efficiency" in rubric and result.duration_seconds:
            threshold = rubric["efficiency"].get("threshold_seconds", 30)
            efficiency_score = max(0.0, 1.0 - (result.duration_seconds / threshold))
            rubric_scores["efficiency"] = efficiency_score

        # Add more structured rubric fields as needed
        return rubric_scores


def load_task_fixture(fixture_dir: Path) -> tuple[TaskDefinition, dict[str, Any], list[dict[str, Any]]]:
    """
    Load task definition, metadata, and assertions from a fixture directory.

    Expected files:
    - task.json
    - assertions.json (optional if assertions in task.json)
    - metadata.json
    """
    task_file = fixture_dir / "task.json"
    assertions_file = fixture_dir / "assertions.json"
    metadata_file = fixture_dir / "metadata.json"

    if not task_file.exists():
        raise FileNotFoundError(f"task.json not found in {fixture_dir}")

    with open(task_file) as f:
        task_data = json.load(f)

    task = TaskDefinition(
        id=task_data["id"],
        prompt=task_data["prompt"],
        start_url=task_data.get("start_url"),
        requires_browser=task_data.get("requires_browser"),
        environment=task_data.get("environment", {}),
        metadata=task_data.get("metadata", {})
    )

    # Load assertions (can be in separate file or in task.metadata.assertions)
    if assertions_file.exists():
        with open(assertions_file) as f:
            assertions = json.load(f).get("assertions", [])
    elif "assertions" in task.metadata:
        assertions = task.metadata["assertions"]
    else:
        assertions = []

    # Load metadata
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
    else:
        metadata = {}

    return task, metadata, assertions


def write_grade(grade: Grade, output_path: Path) -> None:
    """Write grade.json to disk."""
    with open(output_path, "w") as f:
        json.dump(grade.to_dict(), f, indent=2)
