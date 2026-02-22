# Contributing to mcp-swagger-cli

## Project Structure

```
mcp-swagger-cli/
├── mcp_swagger_cli/
│   ├── __init__.py
│   ├── cli.py           # CLI commands and argument parsing
│   ├── generator.py     # Server generation logic and filtering
│   ├── parser.py        # OpenAPI spec parsing
│   ├── exceptions.py    # Custom exceptions
│   └── templates/       # Jinja2 templates for generated output
│       ├── main.py.j2           # Generated MCP server
│       ├── pyproject_toml.j2    # Generated pyproject.toml
│       ├── README_md.j2         # Generated README
│       └── example_spec_info_md.j2
├── tests/
├── pyproject.toml
└── README.md
```

## Setup

```bash
git clone https://github.com/mcp-swagger/mcp-swagger-cli.git
cd mcp-swagger-cli
pip install -e .
```

## Key Areas

### Templates (`mcp_swagger_cli/templates/`)

The Jinja2 templates control what gets generated. `main.py.j2` is the most critical — it defines the structure of every generated MCP server.

A few things to be aware of when editing templates:

- **Literal curly braces in generated Python** — use `{{ '{' }}` and `{{ '}' }}` to output `{` and `}` without Jinja2 interpreting them
- **Whitespace control** — avoid `{%-` and `-%}` strippers unless intentional; they collapse newlines and can merge Python statements onto one line
- **Return types** — generated tool functions return `Any` (not `dict`) to handle both list and dict API responses

### Generator (`generator.py`)

Handles filtering logic for `--tag`, `--path-filter`, and `--max-operations`. Filtering is applied post-parse — the full spec is always loaded, only the generated output is scoped.

### Parser (`parser.py`)

Wraps `prance` for spec resolution. Supports OpenAPI 3.x and Swagger 2.0.

## Known Behaviours

- **Large specs** — filtering is post-parse so download/parse time is always the full spec cost regardless of filters
- **Tag filtering** — some APIs (e.g. Stripe) use a single `default` tag. `--path-filter` is more reliable for these
- **Optional parameters** — generated tool functions use `= None` defaults. Callers should omit optional params entirely rather than passing `null`
- **Path parameter substitution** — URL paths with `{param}` placeholders are resolved at runtime using `.replace()` calls generated per-parameter

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Submitting Changes

1. Fork the repo and create a branch
2. Make your changes
3. Test against at least one real spec (Petstore is a good baseline)
4. Open a PR with a clear description of what changed and why
