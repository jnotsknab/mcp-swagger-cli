"""Tests for the generator module."""

import json
import tempfile
from pathlib import Path

import pytest

from mcp_swagger_cli.generator import MCPServerGenerator


# Sample OpenAPI spec for testing
SAMPLE_OPENAPI = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test Pet API",
        "version": "1.0.0",
        "description": "API for testing",
    },
    "servers": [
        {"url": "https://api.example.com/v1"},
    ],
    "paths": {
        "/pets": {
            "get": {
                "summary": "List pets",
                "description": "Get all pets",
                "operationId": "listPets",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 10},
                    },
                ],
                "responses": {
                    "200": {"description": "Success"},
                },
            },
            "post": {
                "summary": "Create a pet",
                "operationId": "createPet",
                "tags": ["pets"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Pet"},
                        },
                    },
                },
                "responses": {
                    "201": {"description": "Created"},
                },
            },
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Get a pet",
                "operationId": "getPet",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                ],
                "responses": {
                    "200": {"description": "Success"},
                },
            },
            "delete": {
                "summary": "Delete a pet",
                "operationId": "deletePet",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                ],
                "responses": {
                    "204": {"description": "Deleted"},
                },
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
                    "status": {"type": "string", "enum": ["available", "pending", "sold"]},
                },
            },
        },
    },
}


class TestMCPServerGenerator:
    """Tests for MCPServerGenerator class."""

    @pytest.fixture
    def spec_file(self, tmp_path: Path) -> Path:
        """Create a temporary spec file."""
        spec_file = tmp_path / "test_api.json"
        spec_file.write_text(json.dumps(SAMPLE_OPENAPI))
        return spec_file

    def test_generator_init(self, spec_file: Path) -> None:
        """Test generator initialization."""
        generator = MCPServerGenerator(
            spec_path=str(spec_file),
            server_name="test_server",
            transport="stdio",
            validate=False,
        )
        
        assert generator.server_name == "test_server"
        assert generator.transport == "stdio"
        assert generator.spec_info["title"] == "Test Pet API"

    def test_generate_server(self, spec_file: Path, tmp_path: Path) -> None:
        """Test generating a server."""
        output_dir = tmp_path / "generated_server"
        
        generator = MCPServerGenerator(
            spec_path=str(spec_file),
            server_name="pet_mcp_server",
            transport="stdio",
            validate=False,
            verbose=True,
        )
        
        generator.generate(output_dir)
        
        # Check that key files were created
        assert (output_dir / "main.py").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "requirements.txt").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "SPEC_INFO.md").exists()

    def test_sanitize_name(self) -> None:
        """Test name sanitization."""
        assert MCPServerGenerator._sanitize_name("my-server") == "my_server"
        assert MCPServerGenerator._sanitize_name("My Server") == "My_Server"
        assert MCPServerGenerator._sanitize_name("123-server") == "_123_server"
        assert MCPServerGenerator._sanitize_name("test@#$%") == "test"

    def test_to_python_type(self) -> None:
        """Test Python type conversion."""
        assert MCPServerGenerator._to_python_type("string") == "str"
        assert MCPServerGenerator._to_python_type("integer") == "int"
        assert MCPServerGenerator._to_python_type("boolean") == "bool"
        assert MCPServerGenerator._to_python_type("array") == "list"
        assert MCPServerGenerator._to_python_type("unknown") == "Any"

    def test_escape_docstring(self) -> None:
        """Test docstring escaping."""
        assert MCPServerGenerator._escape_docstring("test") == "test"
        assert MCPServerGenerator._escape_docstring('test """ quotes') == r'test \"\"\" quotes'
        assert MCPServerGenerator._escape_docstring(None) == ""

    def test_generate_with_sse_transport(self, spec_file: Path, tmp_path: Path) -> None:
        """Test generating a server with SSE transport."""
        output_dir = tmp_path / "generated_server_sse"
        
        generator = MCPServerGenerator(
            spec_path=str(spec_file),
            server_name="pet_server",
            transport="sse",
            validate=False,
        )
        
        generator.generate(output_dir)
        
        main_py = output_dir / "main.py"
        content = main_py.read_text()
        
        assert 'transport = "sse"' in content

    def test_generate_with_custom_base_url(self, spec_file: Path, tmp_path: Path) -> None:
        """Test generating a server with custom base URL."""
        output_dir = tmp_path / "generated_server"
        
        generator = MCPServerGenerator(
            spec_path=str(spec_file),
            server_name="pet_server",
            base_url="https://custom.api.com/v2",
            validate=False,
        )
        
        generator.generate(output_dir)
        
        main_py = output_dir / "main.py"
        content = main_py.read_text()
        
        assert "https://custom.api.com/v2" in content

    def test_generate_force_overwrite(self, spec_file: Path, tmp_path: Path) -> None:
        """Test generating with force overwrite."""
        output_dir = tmp_path / "generated_server"
        output_dir.mkdir()
        (output_dir / "existing.txt").write_text("existing")
        
        generator = MCPServerGenerator(
            spec_path=str(spec_file),
            server_name="pet_server",
            validate=False,
        )
        
        # Should succeed with force=True
        generator.generate(output_dir, force=True)
        
        # New files should exist
        assert (output_dir / "main.py").exists()

    def test_main_py_contains_operations(self, spec_file: Path, tmp_path: Path) -> None:
        """Test that generated main.py contains operations."""
        output_dir = tmp_path / "generated_server"
        
        generator = MCPServerGenerator(
            spec_path=str(spec_file),
            server_name="pet_server",
            validate=False,
        )
        
        generator.generate(output_dir)
        
        main_py = output_dir / "main.py"
        content = main_py.read_text()
        
        # Check for tool decorators
        assert "@mcp.tool()" in content
        assert "listPets" in content
        assert "createPet" in content

    def test_main_py_contains_resources(self, spec_file: Path, tmp_path: Path) -> None:
        """Test that generated main.py contains resources."""
        output_dir = tmp_path / "generated_server"
        
        generator = MCPServerGenerator(
            spec_path=str(spec_file),
            server_name="pet_server",
            validate=False,
        )
        
        generator.generate(output_dir)
        
        main_py = output_dir / "main.py"
        content = main_py.read_text()
        
        # Check for resource decorators
        assert "@mcp.resource" in content
