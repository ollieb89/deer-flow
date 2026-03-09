#!/usr/bin/env python3
"""
Grader: Evaluates execution results against test assertions.
Checks commands, output, file existence, and other criteria defined in assertions.json.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple


class AssertionResult:
    """Result of a single assertion check."""
    def __init__(self, assertion: str, passed: bool, details: str = ""):
        self.assertion = assertion
        self.passed = passed
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "assertion": self.assertion,
            "passed": self.passed,
            "details": self.details
        }


class Grader:
    """Evaluates execution result against a set of assertions."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.assertions_file = workspace_dir / "assertions.json"
        self.result_file = workspace_dir / "result.json"
        self.assertions: List[str] = []
        self.result_data: Dict[str, Any] = {}
        self.assertion_results: List[AssertionResult] = []
        self.passed: bool = False
    
    def load_data(self):
        """Load assertions and result data."""
        if not self.assertions_file.exists():
            raise FileNotFoundError(f"Assertions file not found: {self.assertions_file}")
        if not self.result_file.exists():
            raise FileNotFoundError(f"Result file not found: {self.result_file}")
        
        with open(self.assertions_file) as f:
            assertions_data = json.load(f)
            self.assertions = assertions_data.get("assertions", [])
        
        with open(self.result_file) as f:
            self.result_data = json.load(f)
    
    def evaluate(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Run all assertions and determine overall pass/fail.
        
        Returns:
            (passed, assertion_results, summary)
        """
        self.assertion_results = []
        
        for assertion_text in self.assertions:
            result = self._check_assertion(assertion_text)
            self.assertion_results.append(result)
        
        all_passed = all(ar.passed for ar in self.assertion_results)
        self.passed = all_passed
        
        summary = self._generate_summary()
        
        return all_passed, [ar.to_dict() for ar in self.assertion_results], summary
    
    def _check_assertion(self, assertion: str) -> AssertionResult:
        """Evaluate a single assertion string against result data."""
        assertion_lower = assertion.lower()
        
        # Check file existence assertions
        if "file exists" in assertion_lower or "file exists in workspace" in assertion_lower:
            return self._check_file_exists(assertion)
        
        # Check command execution
        if "command" in assertion_lower and "executed" in assertion_lower:
            return self._check_command_executed(assertion)
        
        # Check output is non-empty
        if "output is non-empty" in assertion_lower or "output is not empty" in assertion_lower:
            return self._check_output_non_empty()
        
        # Check navigation occurred
        if "navigation occurred" in assertion_lower:
            return self._check_navigation()
        
        # Check element located
        if "element" in assertion_lower and ("located" in assertion_lower or "found" in assertion_lower):
            return self._check_element_located()
        
        # Check wait/completion within timeout
        if ("wait" in assertion_lower or "timeout" in assertion_lower) and "completes" in assertion_lower:
            return self._check_wait_success()
        
        # Check extraction succeeded
        if "extracted" in assertion_lower:
            return self._check_extraction()
        
        # Check minimum count
        if "extracted at least" in assertion_lower:
            return self._check_min_count(assertion)
        
        # Check ordering (ascending, etc)
        if "ascending order" in assertion_lower or "descending order" in assertion_lower:
            return self._check_ordering(assertion)
        
        # Check no duplicates
        if "no duplicate" in assertion_lower:
            return self._check_no_duplicates(assertion)
        
        # Check success/failure
        if "report success/failure" in assertion_lower:
            return self._check_success_failure_reporting()
        
        # Check presence in output
        if re.search(r"contains|includes|equals|is equal to", assertion_lower):
            return self._check_output_contains(assertion)
        
        # Default: unknown assertion pattern
        return AssertionResult(
            assertion=assertion,
            passed=False,
            details=f"Unrecognized assertion pattern: {assertion}"
        )
    
    def _check_file_exists(self, assertion: str) -> AssertionResult:
        """Check if a specific file exists."""
        # Extract filename from assertion
        # Pattern: "screenshot file exists" -> look for screenshot.png or screenshot in workspace
        files_to_check = []
        
        if "screenshot" in assertion.lower():
            files_to_check.append("screenshot.png")
        if "video" in assertion.lower() or "webm" in assertion.lower():
            files_to_check.append("login.webm")
        if "session" in assertion.lower() and "auth" in assertion.lower():
            files_to_check.append("session.auth")
        
        # Generic: look for any file that might be mentioned
        # For simplicity in mock, we'll check if result.metadata.files created matches
        metadata_files = self.result_data.get("metadata", {}).get("files_created", [])
        
        found = any(f in metadata_files for f in files_to_check) or any(Path(f).exists() for f in files_to_check)
        
        if found:
            return AssertionResult(assertion, True, f"Found required files: {files_to_check}")
        else:
            return AssertionResult(assertion, False, f"Required files not found: {files_to_check}")
    
    def _check_command_executed(self, assertion: str) -> AssertionResult:
        """Check if a specific command was executed."""
        commands = self.result_data.get("commands", [])
        
        # Extract expected command pattern
        # Example: "command 'agent-browser open https://example.com' executed"
        # We'll look for agent-browser and keywords
        
        expected_cmd = None
        if "agent-browser open" in assertion:
            # Get URL if specified
            url_match = re.search(r"https?://[^\s'\"]+", assertion)
            if url_match:
                expected_cmd = f"agent-browser open {url_match.group()}"
        elif "agent-browser click" in assertion:
            expected_cmd = "agent-browser click"
        elif "agent-browser fill" in assertion:
            expected_cmd = "agent-browser fill"
        elif "agent-browser screenshot" in assertion:
            expected_cmd = "agent-browser screenshot"
        elif "agent-browser submit" in assertion:
            expected_cmd = "agent-browser submit"
        elif "agent-browser wait" in assertion:
            expected_cmd = "agent-browser wait"
        
        if expected_cmd:
            found = any(expected_cmd in cmd for cmd in commands)
            if found:
                return AssertionResult(assertion, True, f"Found expected command: {expected_cmd}")
            else:
                return AssertionResult(assertion, False, f"Expected command not found: {expected_cmd}")
        
        # General check that some agent-browser command executed
        has_agent_cmd = any("agent-browser" in cmd for cmd in commands)
        if has_agent_cmd:
            return AssertionResult(assertion, True, "Agent-browser commands were executed")
        else:
            return AssertionResult(assertion, False, "No agent-browser commands found")
    
    def _check_output_non_empty(self) -> AssertionResult:
        """Check that output is not empty."""
        output = self.result_data.get("output", "").strip()
        if output:
            return AssertionResult("output is non-empty", True, f"Output length: {len(output)}")
        else:
            return AssertionResult("output is non-empty", False, "Output is empty")
    
    def _check_navigation(self) -> AssertionResult:
        """Check that navigation occurred (URL changed or page updated)."""
        commands = self.result_data.get("commands", [])
        metadata = self.result_data.get("metadata", {})
        
        # Look for open command or navigation evidence
        has_open = any("agent-browser open" in cmd for cmd in commands)
        has_click_submit = any(any(kw in cmd for kw in ["click", "submit"]) for cmd in commands)
        success = self.result_data.get("success", False)
        
        if has_open or has_click_submit or success:
            return AssertionResult("navigation occurred", True, "Navigation evidence found")
        else:
            return AssertionResult("navigation occurred", False, "No navigation detected")
    
    def _check_element_located(self) -> AssertionResult:
        """Check that an element was located."""
        output = self.result_data.get("output", "").lower()
        commands = self.result_data.get("commands", [])
        
        # Look for snapshot or element references
        has_snapshot = any("snapshot" in cmd.lower() for cmd in commands)
        has_ref = any("@" in cmd for cmd in commands)
        mentions_element = any(kw in output for kw in ["located", "found", "element", "ref"])
        
        if has_snapshot or has_ref or mentions_element:
            return AssertionResult("element located", True, "Element location evidence")
        else:
            return AssertionResult("element located", False, "No element location evidence")
    
    def _check_wait_success(self) -> AssertionResult:
        """Check that wait completed successfully."""
        commands = self.result_data.get("commands", [])
        success = self.result_data.get("success", True)
        has_wait = any("agent-browser wait" in cmd for cmd in commands)
        
        if has_wait and success:
            return AssertionResult("wait completed successfully", True, "Wait command executed and success")
        elif has_wait:
            return AssertionResult("wait completed successfully", False, "Wait executed but overall failure")
        else:
            return AssertionResult("wait completed successfully", False, "No wait command found")
    
    def _check_extraction(self) -> AssertionResult:
        """Check that extraction occurred."""
        output = self.result_data.get("output", "")
        commands = self.result_data.get("commands", [])
        
        has_get = any("agent-browser get" in cmd for cmd in commands)
        has_extract = any("extract" in cmd.lower() for cmd in commands)
        
        if has_get or has_extract or any(kw in output.lower() for kw in ["extracted", "captured"]):
            return AssertionResult("extraction succeeded", True, "Extraction evidence")
        else:
            return AssertionResult("extraction succeeded", False, "No extraction evidence")
    
    def _check_min_count(self, assertion: str) -> AssertionResult:
        """Check that at least N items were extracted."""
        # Extract number
        match = re.search(r"at least (\d+)", assertion.lower())
        if match:
            expected_min = int(match.group(1))
            # In mock, we'd need result.metadata.item_count or parse output
            count = self.result_data.get("metadata", {}).get("extracted_count", 0)
            if count >= expected_min:
                return AssertionResult(assertion, True, f"Extracted {count} items (>= {expected_min})")
            else:
                return AssertionResult(assertion, False, f"Only {count} items (< {expected_min})")
        
        return AssertionResult(assertion, False, "Could not parse expected count")
    
    def _check_ordering(self, assertion: str) -> AssertionResult:
        """Check ordering of extracted items."""
        # Simplified: assume we check metadata for ordering confirmation
        ordered_correctly = self.result_data.get("metadata", {}).get("ordered_correctly", False)
        
        if ordered_correctly:
            return AssertionResult(assertion, True, "Items in expected order")
        else:
            return AssertionResult(assertion, False, "Items not in expected order")
    
    def _check_no_duplicates(self, assertion: str) -> AssertionResult:
        """Check for duplicates."""
        no_dupes = self.result_data.get("metadata", {}).get("no_duplicates", True)
        
        if no_dupes:
            return AssertionResult(assertion, True, "No duplicates found")
        else:
            return AssertionResult(assertion, False, "Duplicates detected")
    
    def _check_success_failure_reporting(self) -> AssertionResult:
        """Check that success/failure was reported."""
        output = self.result_data.get("output", "")
        success = self.result_data.get("success", None)
        
        if success is not None:
            status = "success" if success else "failure"
            return AssertionResult("report success/failure", True, f"Status reported: {status}")
        else:
            return AssertionResult("report success/failure", False, "No clear status in result")
    
    def _check_output_contains(self, assertion: str) -> AssertionResult:
        """Check that output contains specific text."""
        output = self.result_data.get("output", "")
        
        # Extract expected content
        if "equals" in assertion or "is equal to" in assertion:
            # Extract value after equals
            match = re.search(r"equals ['\"]?([^'\"]+)['\"]?", assertion)
            if match:
                expected = match.group(1).strip()
                if expected in output:
                    return AssertionResult(assertion, True, f"Output contains: {expected}")
                else:
                    return AssertionResult(assertion, False, f"Output missing: {expected}")
        
        if "includes" in assertion or "contains" in assertion:
            # Similar extraction
            match = re.search(r"(?:contains|includes) ['\"]?([^'\"]+)['\"]?", assertion)
            if match:
                expected = match.group(1).strip()
                if expected.lower() in output.lower():
                    return AssertionResult(assertion, True, f"Output includes: {expected}")
                else:
                    return AssertionResult(assertion, False, f"Output missing: {expected}")
        
        return AssertionResult(assertion, False, "Could not parse expected value")
    
    def _generate_summary(self) -> str:
        """Generate a summary of the evaluation."""
        total = len(self.assertion_results)
        passed = sum(1 for ar in self.assertion_results if ar.passed)
        failed = total - passed
        
        summary_lines = [
            f"Evaluation Summary: {passed}/{total} assertions passed",
            f"Overall: {'PASS' if self.passed else 'FAIL'}"
        ]
        
        if failed > 0:
            summary_lines.append("Failed assertions:")
            for ar in self.assertion_results:
                if not ar.passed:
                    summary_lines.append(f"  - {ar.assertion}: {ar.details}")
        
        return "\n".join(summary_lines)
