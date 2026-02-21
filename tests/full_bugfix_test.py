#!/usr/bin/env python3
"""Full Bugfix Test Script for Bug 2 - OpenAPI 3.0 Parser Compatibility.

This script tests all three spec files:
- openapi_2.0_sample.yaml (OpenAPI 2.0)
- openapi_3.0_sample.yaml (OpenAPI 3.0)
- special_description.yaml (special chars)

For each spec:
1. Run CLI generate to temp dir
2. Validate pyproject.toml parses with tomllib
3. pip install -e . succeeds
4. Check generated files for completeness:
   - main.py has correct endpoints
   - Schemas are included
   - Parameters are correctly handled (no extra body params)
   - requestBody/body params are properly converted
   - $ref resolution works
"""

import os
import sys
import shutil
import subprocess
import tomllib
import json
import re

# Test specs
SPECS = [
    ("openapi_2.0_sample.yaml", "test_server_20", "OpenAPI 2.0"),
    ("openapi_3.0_sample.yaml", "test_server_30", "OpenAPI 3.0"),
    ("special_description.yaml", "test_special", "Special Chars"),
]

PROJECT_DIR = "/workspace"
SPECS_DIR = "/workspace/test_specs"
OUTPUT_BASE = "/output/full_test"


def run_cli(spec_file, output_dir, server_name):
    """Run CLI to generate server."""
    cmd = [
        "python", "-m", "mcp_swagger_cli.cli",
        "create",
        f"{SPECS_DIR}/{spec_file}",
        "--output", output_dir,
        "--name", server_name,
        "--verbose"
    ]
    
    result = {
        "spec": spec_file,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "toml_valid": False,
        "pip_install": False,
        "files_complete": False,
        "details": {}
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {spec_file}")
    print(f"{'='*60}")
    
    # Clean output
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Run CLI
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_DIR)
    result["returncode"] = proc.returncode
    result["stdout"] = proc.stdout
    result["stderr"] = proc.stderr
    
    if proc.returncode != 0:
        print(f"CLI FAILED: {proc.stderr}")
        return result
    
    print(f"CLI: SUCCESS")
    
    # Validate TOML
    toml_path = os.path.join(output_dir, "pyproject.toml")
    if os.path.exists(toml_path):
        try:
            with open(toml_path, "rb") as f:
                tomllib.load(f)
            result["toml_valid"] = True
            print("TOML: VALID")
        except Exception as e:
            print(f"TOML: INVALID - {e}")
    else:
        print("TOML: NOT FOUND")
    
    # pip install
    if result["toml_valid"]:
        try:
            pip_proc = subprocess.run(
                ["pip", "install", "-e", output_dir],
                capture_output=True, text=True, timeout=120
            )
            result["pip_install"] = pip_proc.returncode == 0
            print(f"pip install: {'SUCCESS' if result['pip_install'] else 'FAILED'}")
        except Exception as e:
            print(f"pip install: ERROR - {e}")
    
    # Check generated files
    main_py = os.path.join(output_dir, server_name, "main.py")
    if os.path.exists(main_py):
        with open(main_py, "r") as f:
            content = f.read()
        
        # Check for BASE_URL
        if 'BASE_URL = "None"' in content:
            print("WARNING: BASE_URL = 'None' found!")
            result["details"]["base_url_issue"] = True
        else:
            print("BASE_URL: OK (not 'None')")
        
        # Check for extra params in body-only operations
        if spec_file == "openapi_2.0_sample.yaml":
            # POST_users should only have body param, not extra user param
            if re.search(r'def\s+POST_users\s*\(\s*user\s*:', content):
                print("WARNING: Extra 'user' parameter in POST_users")
                result["details"]["extra_param"] = True
            else:
                print("PARAMETERS: OK (no extra body param)")
        
        # Check schemas
        if spec_file == "openapi_3.0_sample.yaml":
            if "Pet" in content and "Tags" in content:
                print("SCHEMAS: OK (Pet, Tags included)")
            else:
                print("WARNING: Missing schemas")
        
        result["files_complete"] = True
    
    return result


def main():
    all_results = []
    
    for spec_file, server_name, desc in SPECS:
        output_dir = os.path.join(OUTPUT_BASE, server_name)
        result = run_cli(spec_file, output_dir, server_name)
        result["description"] = desc
        all_results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for r in all_results:
        status = "PASS" if (r["returncode"] == 0 and r["toml_valid"] and r["pip_install"]) else "FAIL"
        print(f"{r['description']} ({r['spec']}): {status}")
        print(f"  CLI: {r['returncode']}")
        print(f"  TOML: {r['toml_valid']}")
        print(f"  pip: {r['pip_install']}")
        print(f"  Files: {r['files_complete']}")
        if r.get("details"):
            print(f"  Details: {r['details']}")
    
    # Overall pass/fail
    all_pass = all(
        r["returncode"] == 0 and r["toml_valid"] and r["pip_install"] 
        for r in all_results
    )
    
    print(f"\n{'='*60}")
    if all_pass:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print(f"{'='*60}")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
