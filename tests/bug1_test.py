#!/usr/bin/env python3
"""Test script for Bug 1: TOML description sanitization.

This test verifies that the description field in pyproject.toml is properly sanitized
to handle problematic characters (newlines, quotes, backslashes, tabs).

Test spec: test_specs/special_description.yaml contains:
- description: "Description with newlines\nand \"double quotes\", \\backslashes\\, \tand tabs."

Expected after fix:
- Newlines/tabs replaced with spaces
- Backslashes escaped: \ -> \\
- Double quotes escaped: " -> \"
- Total length <= 200 chars
"""

import os
import sys
import subprocess
import tomllib
import tempfile
import shutil

def run_test():
    """Run the bug 1 test."""
    # Paths
    project_dir = "/workspace"  # mcp-swagger-cli project
    spec_path = "/workspace/test_specs/special_description.yaml"
    output_dir = "/output/bug1_test_output"
    
    # Clean output
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Run CLI to generate server
    cmd = [
        "python", "-m", "mcp_swagger_cli.cli",
        "create",
        spec_path,
        "--output", output_dir,
        "--name", "test_special",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
    
    if result.returncode != 0:
        print("FAIL: CLI execution failed")
        print(f"stderr: {result.stderr}")
        return False
    
    # Check pyproject.toml exists
    toml_path = os.path.join(output_dir, "pyproject.toml")
    if not os.path.exists(toml_path):
        print("FAIL: pyproject.toml not generated")
        return False
    
    print("PASS: pyproject.toml generated")
    
    # Validate TOML parses correctly
    try:
        with open(toml_path, "rb") as f:
            toml_data = tomllib.load(f)
    except Exception as e:
        print(f"FAIL: TOML parse error: {e}")
        return False
    
    print("PASS: TOML parses correctly")
    
    # Check description is properly sanitized
    description = toml_data["tool"]["poetry"]["description"]
    
    # Should NOT contain literal newlines
    if "\n" in description or "\r" in description:
        print(f"FAIL: Description contains newlines: {repr(description)}")
        return False
    
    print("PASS: No newlines in description")
    
    # Should NOT contain literal tabs
    if "\t" in description:
        print(f"FAIL: Description contains tabs: {repr(description)}")
        return False
    
    print("PASS: No tabs in description")
    
    # Should NOT contain unescaped quotes (TOML uses \")
    # In the Python string, escaped quotes appear as \"
    if '"' in description and '\\"' not in description:
        print(f"FAIL: Description contains unescaped quotes: {repr(description)}")
        return False
    
    print("PASS: Quotes are escaped")
    
    # Length should be <= 200
    if len(description) > 200:
        print(f"FAIL: Description too long ({len(description)} chars): {description}")
        return False
    
    print(f"PASS: Description length OK ({len(description)} chars)")
    
    # Test pip install -e .
    pip_result = subprocess.run(
        ["pip", "install", "-e", output_dir],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if pip_result.returncode != 0:
        print(f"FAIL: pip install failed: {pip_result.stderr}")
        return False
    
    print("PASS: pip install -e . succeeded")
    
    print("\n=== ALL TESTS PASSED ===")
    return True


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)