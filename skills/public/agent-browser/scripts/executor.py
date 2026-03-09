#!/usr/bin/env python3
"""
Executor abstraction for agent-browser evaluations.
Provides mock execution for fixture-based testing and real CLI execution.
"""

import sys
import json
import time
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any

# Support running as script directly from scripts/ directory
if __name__ == "__main__" or __package__ is None:
    # Add parent directory to path to enable imports
    sys.path.insert(0, str(Path(__file__).parent))

from fixtures import HTML_FIXTURES


class ExecutionResult:
    """Container for execution results."""
    def __init__(
        self,
        success: bool,
        commands: List[str],
        output: str,
        error: str = "",
        duration: float = 0.0,
        metadata: Dict[str, Any] = None
    ):
        self.success = success
        self.commands = commands
        self.output = output
        self.error = error
        self.duration = duration
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "duration": self.duration,
            "commands": self.commands,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }


class Executor(ABC):
    """Abstract base class for execution backends."""
    
    @abstractmethod
    def execute(self, prompt: str, workspace_dir: Path) -> ExecutionResult:
        """
        Execute the given prompt in the agent-browser environment.
        
        Args:
            prompt: User prompt to execute
            workspace_dir: Working directory for this test case (contains fixtures)
            
        Returns:
            ExecutionResult with commands, output, and status
        """
        pass


class MockBrowser:
    """In-memory mock browser state for realistic simulation."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.current_url = "/"
        self.history = []
        self.files_created = []
        self.extractions = []
        self.page_content = ""
        self.downloads_dir = workspace_dir / "downloads"
        self.downloads_dir.mkdir(exist_ok=True)
        self.snapshots_dir = workspace_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        
    def navigate(self, url: str):
        self.history.append(self.current_url)
        self.current_url = url
        self._load_page(url)
        
    def _load_page(self, url: str):
        """Load page content from fixtures based on URL."""
        if url in ["/", "/start-page", "start-page"]:
            self.page_content = fixtures.HTML_FIXTURES["simple_click"]
        elif url in ["/form", "form"]:
            self.page_content = fixtures.HTML_FIXTURES["form_fill"]
        elif url in ["/page1", "page1"]:
            self.page_content = fixtures.HTML_FIXTURES["multi_page"]
        elif url in ["/page2", "page2"]:
            self.page_content = fixtures.HTML_FIXTURES["page2"]
        elif url in ["/page3", "page3"]:
            self.page_content = fixtures.HTML_FIXTURES["page3"]
        elif url.startswith("/download/"):
            filename = url.split("/")[-1] or "file"
            filepath = self.downloads_dir / filename
            filepath.write_text(f"Mock content of {filename}")
            self.files_created.append(filepath.relative_to(self.workspace_dir).as_posix())
        else:
            self.page_content = "<html><body>Unknown page</body></html>"
            
    def click(self, text_match: str):
        """Simulate click by matching visible text."""
        if any(k in text_match.lower() for k in ["next", "page 2", "go to"]):
            self.navigate("/page2")
        elif "download" in text_match.lower():
            self.navigate("/download/report.pdf")
        elif "submit" in text_match.lower():
            pass  # form submission stays on page
        else:
            pass  # generic click
            
    def fill(self, field_id: str, value: str):
        """Simulate filling a form field."""
        log = f"field:{field_id}=value:{value}"
        self.extractions.append(log)
        
    def submit(self, form_selector: str):
        """Simulate form submission."""
        self.extractions.append("form:submitted")
        
    def extract(self, selector: str) -> str:
        """Extract content from page using CSS selector simulation."""
        content = self.page_content
        if selector.startswith("#"):
            # Simple id extraction
            pattern = f'id="{selector[1:]}"[^>]*>(.*?)<'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                self.extractions.append(f"selector:{selector}={extracted[:30]}")
                return extracted
        elif selector == "table":
            # Simulate table extraction
            table_match = re.search(r'<table.*?>(.*?)</table>', content, re.DOTALL)
            if table_match:
                self.extractions.append("selector:table=extracted")
                return "Table data extracted"
        return ""
        
    def download(self, url: str):
        self.navigate(url)
        
    def wait(self, condition: str = "load"):
        if condition == "load":
            time.sleep(0.05)


class MockExecutor(Executor):
    """
    Mock executor that simulates browser automation using local fixtures.
    Deterministic and fast for development and CI.
    """
    
    def __init__(self, fixtures_dir: Path = None):
        self.fixtures_dir = fixtures_dir or (Path(__file__).parent.parent / "fixtures")
    
    def execute(self, prompt: str, workspace_dir: Path) -> ExecutionResult:
        start = time.time()
        browser = MockBrowser(workspace_dir)
        commands = []
        output_lines = []
        success = True
        error = ""
        
        prompt_lower = prompt.lower()
        
        # Simulate sequence of actions based on prompt content
        if any(k in prompt_lower for k in ["open", "navigate", "go to"]):
            # Determine target page
            if "form" in prompt_lower:
                browser.navigate("/form")
                commands.append("open /form")
                output_lines.append("Navigated to form page")
            elif "page1" in prompt_lower or ("page" in prompt_lower and "2" not in prompt_lower):
                browser.navigate("/page1")
                commands.append("open /page1")
                output_lines.append("Navigated to page1")
            else:
                browser.navigate("/")
                commands.append("open /")
                output_lines.append("Opened start page")
                
        if "click" in prompt_lower:
            # Determine what to click
            if "next" in prompt_lower or "page 2" in prompt_lower:
                browser.click("Next Page")
                commands.append("click 'Next Page'")
                output_lines.append("Clicked Next Page link")
            elif "download" in prompt_lower:
                browser.click("Download Report")
                commands.append("click 'Download Report'")
                output_lines.append("Clicked download button")
            else:
                browser.click("Submit")
                commands.append("click 'Submit'")
                output_lines.append("Clicked submit button")
                
        if "fill" in prompt_lower:
            # Extract fill values (very simplified)
            fills = []
            if "name" in prompt_lower and "'" in prompt:
                name_val = prompt.split("'")[1]
                browser.fill("name", name_val)
                fills.append(f"name='{name_val}'")
            elif "email" in prompt_lower and "@" in prompt:
                email_val = "test@example.com"
                browser.fill("email", email_val)
                fills.append(f"email='{email_val}'")
            else:
                browser.fill("field", "test value")
                fills.append("field='test value'")
                
            for f in fills:
                commands.append(f"fill {f}")
            output_lines.append(f"Filled {len(fills)} field(s)")
            
        if "submit" in prompt_lower:
            browser.submit("form")
            commands.append("submit form")
            output_lines.append("Submitted form")
            
        if "wait" in prompt_lower:
            browser.wait("load")
            commands.append("wait --load")
            output_lines.append("Waited for page load")
            
        if "extract" in prompt_lower or "get" in prompt_lower or "table" in prompt_lower:
            selector = "#data" if "table" in prompt_lower else "#result"
            extracted = browser.extract(selector)
            commands.append(f"extract '{selector}'")
            output_lines.append(f"Extracted content: {extracted[:50] if extracted else '(empty)'}")
            
        if "download" in prompt_lower:
            browser.download("/download/report.pdf")
            commands.append("download /download/report.pdf")
            output_lines.append("Download initiated")
            
        # Handle failure simulation
        if "fail" in prompt_lower:
            success = False
            error = "Simulated failure: element not found"
            commands = ["open /test", "click 'nonexistent'"]
            output_lines = [error]
            
        # Handle order issues for multi-page tests
        if "wrong_order" in prompt_lower:
            pass  # Default success, but metadata will reflect
            
        # If no commands generated, still succeed but note it
        if not commands:
            commands.append("no-op")
            output_lines.append("No specific actions recognized")
            
        duration = time.time() - start
        
        # Prepare result data with metadata
        result_dict = {
            "success": success,
            "duration": duration,
            "commands": commands,
            "output": "\n".join(output_lines),
            "error": error,
            "metadata": {
                "files_created": browser.files_created,
                "extracted_count": len(browser.extractions),
                "extractions": browser.extractions[-10:],
            }
        }
        
        # Add test-specific metadata
        if any(k in prompt_lower for k in ["page2", "multi", "two page", "navigate"]):
            result_dict["metadata"]["ordered_correctly"] = "wrong_order" not in prompt_lower
            result_dict["metadata"]["no_duplicates"] = "duplicate" not in prompt_lower
        if "download" in prompt_lower:
            result_dict["metadata"]["files_created"] = browser.files_created
            
        # Write result.json
        result_file = workspace_dir / "result.json"
        with open(result_file, "w") as f:
            json.dump(result_dict, f, indent=2)
            
        # Also write simple output.txt for compatibility
        (workspace_dir / "output.txt").write_text(result_dict["output"])
        
        return ExecutionResult(
            success=success,
            commands=commands,
            output=result_dict["output"],
            error=error,
            duration=duration,
            metadata=result_dict.get("metadata", {})
        )


class RealExecutor(Executor):
    """
    Real executor that runs actual agent-browser CLI commands.
    Requires agent-browser to be installed and available in PATH.
    """
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
    
    def execute(self, prompt: str, workspace_dir: Path) -> ExecutionResult:
        start = time.time()
        commands = []
        output_lines = []
        success = True
        error = ""
        
        try:
            # Check agent-browser availability
            import subprocess
            subprocess.run(
                ["agent-browser", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            commands.append("check: agent-browser available")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            success = False
            error = f"agent-browser CLI not available: {e}"
            output_lines.append(error)
            duration = time.time() - start
            return ExecutionResult(success, commands, "\n".join(output_lines), error, duration)
        
        # Here we would implement actual prompt-to-CLI translation
        # For now, this is a placeholder that would be replaced with actual AI reasoning
        # The real execution would involve:
        # 1. Parse prompt into sequence of actions
        # 2. For each action: run agent-browser command, capture output
        # 3. Handle snapshots, refs, and conditional logic
        
        # For demonstration, we'll simulate a basic flow
        # In practice, this would be where the AI agent uses the skill to reason
        
        commands.append("Simulated real execution would happen here")
        output_lines.append("Real executor stub - needs AI reasoning integration")
        
        duration = time.time() - start
        
        result_data = {
            "success": success,
            "duration": duration,
            "commands": commands,
            "output": "\n".join(output_lines),
            "error": error
        }
        result_file = workspace_dir / "result.json"
        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2)
        
        return ExecutionResult(success, commands, "\n".join(output_lines), error, duration)


def get_executor(executor_type: str = "mock", **kwargs) -> Executor:
    """Factory for creating executors."""
    if executor_type == "mock":
        fixtures_dir = kwargs.get("fixtures_dir")
        return MockExecutor(fixtures_dir)
    elif executor_type == "real":
        timeout = kwargs.get("timeout", 60)
        return RealExecutor(timeout)
    else:
        raise ValueError(f"Unknown executor type: {executor_type}")
