"""Tests for the parser module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mcp_swagger_cli.parser import OpenAPIParser


# Sample OpenAPI 3.0 spec for testing
SAMPLE_OPENAPI_30 = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.0.0",
        "description": "A test API",
    },
    "servers": [
        {"url": "https://api.example.com/v1"},
    ],
    "paths": {
        "/users": {
            "get": {
                "summary": "List users",
                "description": "Get all users",
                "operationId": "listUsers",
                "tags": ["users"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 10},
                    },
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/User"},
                                },
                            },
                        },
                    },
                },
            },
            "post": {
                "summary": "Create user",
                "operationId": "createUser",
                "tags": ["users"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/User"},
                        },
                    },
                },
                "responses": {
                    "201": {"description": "User created"},
                },
            },
        },
        "/users/{userId}": {
            "get": {
                "summary": "Get user",
                "operationId": "getUser",
                "tags": ["users"],
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                ],
                "responses": {
                    "200": {"description": "Successful response"},
                },
            },
        },
    },
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
            },
        },
    },
}


# Sample Swagger 2.0 spec for testing
SAMPLE_SWAGGER_20 = {
    "swagger": "2.0",
    "info": {
        "title": "Pet Store API",
        "version": "1.0.0",
    },
    "basePath": "/v2",
    "paths": {
        "/pets": {
            "get": {
                "summary": "List pets",
                "operationId": "listPets",
                "responses": {
                    "200": {"description": "Success"},
                },
            },
        },
    },
    "definitions": {
        "Pet": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
        },
    },
}


class TestOpenAPIParser:
    """Tests for OpenAPIParser class."""

    def test_parse_json_file(self, tmp_path: Path) -> None:
        """Test parsing a JSON OpenAPI spec."""
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(SAMPLE_OPENAPI_30))
        
        parser = OpenAPIParser(str(spec_file), validate=False)
        
        assert parser.spec["info"]["title"] == "Test API"
        assert parser.spec["openapi"] == "3.0.0"

    def test_parse_yaml_file(self, tmp_path: Path) -> None:
        """Test parsing a YAML OpenAPI spec."""
        spec_file = tmp_path / "openapi.yaml"
        spec_file.write_text(yaml.dump(SAMPLE_OPENAPI_30))
        
        parser = OpenAPIParser(str(spec_file), validate=False)
        
        assert parser.spec["info"]["title"] == "Test API"

    def test_get_spec_info(self, tmp_path: Path) -> None:
        """Test extracting spec info."""
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(SAMPLE_OPENAPI_30))
        
        parser = OpenAPIParser(str(spec_file), validate=False)
        info = parser.get_spec_info()
        
        assert info["title"] == "Test API"
        assert info["version"] == "1.0.0"
        assert info["path_count"] == 2
        assert info["operation_count"] == 3
        assert info["schema_count"] == 1

    def test_get_operations(self, tmp_path: Path) -> None:
        """Test extracting operations."""
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(SAMPLE_OPENAPI_30))
        
        parser = OpenAPIParser(str(spec_file), validate=False)
        operations = parser.get_operations()
        
        assert len(operations) == 3
        
        # Check first operation
        list_users = next(op for op in operations if op["operation_id"] == "listUsers")
        assert list_users["path"] == "/users"
        assert list_users["method"] == "get"
        assert list_users["tags"] == ["users"]
        assert len(list_users["parameters"]) == 1
        assert list_users["parameters"][0]["name"] == "limit"

    def test_get_schemas(self, tmp_path: Path) -> None:
        """Test extracting schemas."""
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(SAMPLE_OPENAPI_30))
        
        parser = OpenAPIParser(str(spec_file), validate=False)
        schemas = parser.get_schemas()
        
        assert "User" in schemas
        assert schemas["User"]["type"] == "object"

    def test_swagger_20_compatibility(self, tmp_path: Path) -> None:
        """Test parsing Swagger 2.0 spec."""
        spec_file = tmp_path / "swagger.json"
        spec_file.write_text(json.dumps(SAMPLE_SWAGGER_20))
        
        parser = OpenAPIParser(str(spec_file), validate=False)
        info = parser.get_spec_info()
        
        assert info["title"] == "Pet Store API"
        assert info["openapi_version"] == "2.0"

    def test_operation_id_generation(self, tmp_path: Path) -> None:
        """Test automatic operationId generation."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                    },
                },
            },
        }
        
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(spec))
        
        parser = OpenAPIParser(str(spec_file), validate=False)
        operations = parser.get_operations()
        
        assert operations[0]["operation_id"] is not None

    def test_request_body_extraction(self, tmp_path: Path) -> None:
        """Test extracting request body info."""
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(SAMPLE_OPENAPI_30))
        
        parser = OpenAPIParser(str(spec_file), validate=False)
        operations = parser.get_operations()
        
        create_user = next(op for op in operations if op["operation_id"] == "createUser")
        
        assert create_user["request_body"] is not None
        assert create_user["request_body"]["required"] is True

    def test_invalid_file_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid file raises appropriate error."""
        spec_file = tmp_path / "invalid.json"
        spec_file.write_text("{ invalid json }")
        
        from mcp_swagger_cli.exceptions import SpecParseError
        
        with pytest.raises(SpecParseError):
            OpenAPIParser(str(spec_file), validate=False)

    def test_not_found_raises_error(self) -> None:
        """Test that missing file raises appropriate error."""
        from mcp_swagger_cli.exceptions import SpecNotFoundError
        
        with pytest.raises(SpecNotFoundError):
            OpenAPIParser("/nonexistent/path/spec.json", validate=False)
