#!/usr/bin/env python3
"""Test script to run CLI and validate outputs."""

import os
import sys
import shutil
import subprocess

# Test specs directory
SPECS_DIR = "/workspace/test_specs"
OUTPUT_BASE = "/output/test_output"

def run_cli(spec_path, output_dir, server_name):
    """Run the CLI to generate a server."""
    cmd = [
        "python", "-m", "mcp_swagger_cli.cli",
        spec_path,
        "--output", output_dir,
        "--server-name", server_name,
        "--verbose"
    ]
    
    result = {
        "spec": spec_path,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "toml_valid": False,
        "pip_install": False,
    }
    
    print(f"\n=== Testing: {spec_path} ===")
    print(f"Output: {output_dir}")
    
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="/workspace"
    )
    
    result["returncode"] = proc.returncode
    result["stdout"] = proc.stdout
    result["stderr"] = proc.stderr
    
    if proc.returncode != 0:
        print(f"CLI ERROR: {proc.stderr}")
        return result
    
    print(f"CLI OK")
    
    # Check if pyproject.toml exists
    toml_path = os.path.join(output_dir, "pyproject.toml")
    if os.path.exists(toml_path):
        print(f"pyproject.toml exists")
        
        # Print the generated TOML content for debugging
        with open(toml_path, "r") as f:
            content = f.read()
            print("--- Generated pyproject.toml (first 500 chars) ---")
            print(content[:500])
            print("---")
        
        # Validate TOML
        try:
            import tomllib
            with open(toml_path, "rb") as f:
                tomllib.load(f)
            result["toml_valid"] = True
            print("TOML VALID")
        except Exception as e:
            print(f"TOML INVALID: {e}")
    else:
        print("pyproject.toml NOT FOUND")
    
    # Try pip install
    if result["toml_valid"]:
        try:
            pip_cmd = f"pip install -e {output_dir}"
            pip_proc = subprocess.run(
                pip_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            if pip_proc.returncode == 0:
                result["pip_install"] = True
                print("pip install SUCCESS")
            else:
                print(f"pip install FAILED: {pip_proc.stderr[:200]}")
        except Exception as e:
            print(f"pip install ERROR: {e}")
    
    return result


def main():
    # Test all three specs
    specs = [
        ("openapi_2.0_sample.yaml", "test_server_20"),
        ("openapi_3.0_sample.yaml", "test_server_30"),
        ("special_description.yaml", "test_server_special"),
    ]
    
    results = []
    
    for spec_file, server_name in specs:
        spec_path = os.path.join(SPECS_DIR, spec_file)
        output_dir = os.path.join(OUTPUT_BASE, server_name)
        
        # Clean output dir
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        result = run_cli(spec_path, output_dir, server_name)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for r in results:
        spec_name = os.path.basename(r["spec"])
        status = "OK" if (r["returncode"] == 0 and r["toml_valid"] and r["pip_install"]) else "FAIL"
        print(f"{spec_name}: {status}")
        print(f"  CLI: {r['returncode']}")
        print(f"  TOML: {r['toml_valid']}")
        print(f"  pip: {r['pip_install']}")
        if r['stderr']:
            print(f"  Errors: {r['stderr'][:200]}")


if __name__ == "__main__":
    main()
