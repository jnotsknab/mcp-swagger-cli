#!/usr/bin/env python
"""Test script to verify CLI installation and basic functionality."""

import sys
import tempfile
import json
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test 1: Import the CLI module
print("Test 1: Import CLI module...")
try:
    from mcp_swagger_cli.cli import app
    from mcp_swagger_cli import __version__
    print(f"  ✓ CLI imported, version: {__version__}")
except Exception as e:
    print(f"  ✗ Failed to import CLI: {e}")
    sys.exit(1)

# Test 2: Import parser
print("Test 2: Import parser module...")
try:
    from mcp_swagger_cli.parser import OpenAPIParser
    print("  ✓ Parser imported")
except Exception as e:
    print(f"  ✗ Failed to import parser: {e}")
    sys.exit(1)

# Test 3: Import generator
print("Test 3: Import generator module...")
try:
    from mcp_swagger_cli.generator import MCPServerGenerator
    print("  ✓ Generator imported")
except Exception as e:
    print(f"  ✗ Failed to import generator: {e}")
    sys.exit(1)

# Test 4: Create a test spec file
print("Test 4: Create test spec and parse...")
SAMPLE_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test Pet API",
        "version": "1.0.0",
    },
    "paths": {
        "/pets": {
            "get": {
                "summary": "List pets",
                "operationId": "listPets",
                "responses": {"200": {"description": "Success"}},
            },
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Get a pet",
                "operationId": "getPet",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "Success"}},
            },
        },
    },
    "components": {
        "schemas": {
            "Pet": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            }
        }
    },
}

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(SAMPLE_SPEC, f)
    spec_path = f.name

try:
    parser = OpenAPIParser(spec_path, validate=False)
    info = parser.get_spec_info()
    print(f"  ✓ Parsed spec: {info['title']} v{info['version']}")
    print(f"    Paths: {info['path_count']}, Operations: {info['operation_count']}")
except Exception as e:
    print(f"  ✗ Failed to parse spec: {e}")
    sys.exit(1)

# Test 5: Generate a server
print("Test 5: Generate MCP server...")
try:
    generator = MCPServerGenerator(
        spec_path=spec_path,
        server_name="test_pet_server",
        transport="stdio",
        validate=False,
    )
    
    output_dir = Path(tempfile.mkdtemp())
    generator.generate(output_dir, force=True)
    
    # Check generated files
    assert (output_dir / "main.py").exists(), "main.py not generated"
    assert (output_dir / "pyproject.toml").exists(), "pyproject.toml not generated"
    assert (output_dir / "README.md").exists(), "README.md not generated"
    
    print(f"  ✓ Generated server in {output_dir}")
    print(f"    Files: main.py, pyproject.toml, README.md, requirements.txt, SPEC_INFO.md")
except Exception as e:
    print(f"  ✗ Failed to generate server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Check generated main.py content
print("Test 6: Verify generated code...")
try:
    main_py = (output_dir / "main.py").read_text()
    assert "@mcp.tool()" in main_py, "No @mcp.tool() decorator found"
    assert "listPets" in main_py, "listPets function not generated"
    assert "getPet" in main_py, "getPet function not generated"
    assert "Pet" in main_py, "Pet resource not generated"
    print("  ✓ Generated code contains expected MCP components")
except Exception as e:
    print(f"  ✗ Generated code verification failed: {e}")
    sys.exit(1)

# Cleanup
import os
os.unlink(spec_path)

print("\n✓ All tests passed!")
