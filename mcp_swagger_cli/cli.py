"""CLI module for MCP Swagger CLI."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_swagger_cli import __version__
from mcp_swagger_cli.generator import MCPServerGenerator

app = typer.Typer(
    name="mcp-swagger",
    help="Generate MCP servers from Swagger/OpenAPI specifications",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]mcp-swagger[/bold cyan] version {__version__}")
        raise typer.Exit()


@app.callback()
def callback() -> None:
    """
    MCP Swagger CLI - Generate MCP servers from Swagger/OpenAPI specifications.
    
    This tool converts Swagger/OpenAPI specs into runnable MCP servers that expose:
    - API operations as MCP Tools
    - Schemas as MCP Resources
    - Operation summaries as MCP Prompts
    """
    pass


@app.command()
def create(
    spec: str = typer.Argument(
        ...,
        help="URL or file path to Swagger/OpenAPI specification (JSON or YAML)",
        show_default=False,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for generated MCP server",
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=True,
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Name for the generated MCP server (defaults to spec title or 'mcp_server')",
    ),
    transport: str = typer.Option(
        "stdio",
        "--transport",
        "-t",
        help="Transport type for MCP server (stdio or sse)",
        case_sensitive=False,
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        "-b",
        help="Base URL for API requests (defaults to server.url from spec)",
    ),
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate specification before generating",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite output directory if it exists",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Create an MCP server from a Swagger/OpenAPI specification.
    
    Examples:
    
        mcp-swagger create https://petstore.swagger.io/v2/swagger.json -o ./my_server
        
        mcp-swagger create ./api_spec.yaml -o ./server --name my_api
        
        mcp-swagger create ./spec.json -o ./server --transport sse --base-url https://api.example.com
    """
    console.print(f"[bold cyan]MCP Swagger CLI[/bold cyan] v{__version__}")
    console.print()
    
    # Resolve output path
    if output is None:
        output = Path.cwd() / "generated_mcp_server"
    
    # Check if output exists
    if output.exists() and not force:
        if not output.is_dir():
            console.print(f"[bold red]Error:[/bold red] {output} exists and is not a directory")
            raise typer.Exit(1)
        if list(output.iterdir()):
            console.print(
                f"[bold red]Error:[/bold red] Output directory {output} is not empty. "
                "Use --force to overwrite."
            )
            raise typer.Exit(1)
    
    # Determine server name
    if name is None:
        name = "mcp_server"
    
    # Validate transport
    if transport not in ("stdio", "sse"):
        console.print(
            f"[bold red]Error:[/bold red] Invalid transport '{transport}'. "
            "Must be 'stdio' or 'sse'"
        )
        raise typer.Exit(1)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=not verbose,
    ) as progress:
        # Task 1: Parse and validate specification
        task_parse = progress.add_task(
            "Parsing specification...", total=None
        )
        
        try:
            generator = MCPServerGenerator(
                spec_path=spec,
                server_name=name,
                transport=transport,
                base_url=base_url,
                validate=validate,
                verbose=verbose,
            )
            progress.update(task_parse, completed=True)
        except Exception as e:
            progress.update(task_parse, failed=True)
            console.print(f"[bold red]Error parsing specification:[/bold red] {e}")
            raise typer.Exit(1)
        
        # Task 2: Generate MCP server
        task_generate = progress.add_task(
            "Generating MCP server...", total=None
        )
        
        try:
            generator.generate(output_dir=output, force=force)
            progress.update(task_generate, completed=True)
        except Exception as e:
            progress.update(task_generate, failed=True)
            console.print(f"[bold red]Error generating server:[/bold red] {e}")
            raise typer.Exit(1)
    
    # Print summary
    console.print()
    console.print(f"[bold green]✓[/bold green] MCP server generated successfully!")
    console.print(f"  [dim]Output:[/dim] {output}")
    console.print(f"  [dim]Name:[/dim] {name}")
    console.print(f"  [dim]Transport:[/dim] {transport}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. cd {output}")
    console.print(f"  2. pip install -e .")
    console.print(f"  3. Run: mcp-server (or python -m {name})")
    console.print()


@app.command()
def validate_spec(
    spec: str = typer.Argument(
        ...,
        help="URL or file path to Swagger/OpenAPI specification",
        show_default=False,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation results",
    ),
) -> None:
    """
    Validate a Swagger/OpenAPI specification.
    
    Examples:
    
        mcp-swagger validate-spec https://petstore.swagger.io/v2/swagger.json
        
        mcp-swagger validate-spec ./api_spec.yaml
    """
    from mcp_swagger_cli.parser import OpenAPIParser
    
    console.print(f"[bold cyan]Validating specification...[/bold cyan]")
    console.print()
    
    try:
        parser = OpenAPIParser(spec_path=spec, validate=True)
        spec_info = parser.get_spec_info()
        
        console.print(f"[bold green]✓ Specification is valid![/bold green]")
        console.print()
        console.print(f"  [bold]Title:[/bold] {spec_info.get('title', 'N/A')}")
        console.print(f"  [bold]Version:[/bold] {spec_info.get('version', 'N/A')}")
        console.print(f"  [bold]OpenAPI Version:[/bold] {spec_info.get('openapi_version', 'N/A')}")
        console.print(f"  [bold]Paths:[/bold] {spec_info.get('path_count', 0)}")
        console.print(f"  [bold]Operations:[/bold] {spec_info.get('operation_count', 0)}")
        console.print(f"  [bold]Schemas:[/bold] {spec_info.get('schema_count', 0)}")
        
        if verbose:
            console.print()
            console.print("[bold]Paths:[/bold]")
            for path in spec_info.get('paths', [])[:20]:
                console.print(f"  • {path}")
            if len(spec_info.get('paths', [])) > 20:
                console.print(f"  ... and {len(spec_info['paths']) - 20} more")
            
            console.print()
            console.print("[bold]Schemas:[/bold]")
            for schema in spec_info.get('schemas', [])[:20]:
                console.print(f"  • {schema}")
            if len(spec_info.get('schemas', [])) > 20:
                console.print(f"  ... and {len(spec_info['schemas']) - 20} more")
        
    except Exception as e:
        console.print(f"[bold red]✗ Validation failed:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    spec: str = typer.Argument(
        ...,
        help="URL or file path to Swagger/OpenAPI specification",
        show_default=False,
    ),
) -> None:
    """
    Show information about a Swagger/OpenAPI specification.
    
    This command parses the spec and displays:
    - Basic info (title, version, description)
    - Available paths and operations
    - Schemas/models
    - Servers
    
    Examples:
    
        mcp-swagger info https://petstore.swagger.io/v2/swagger.json
    """
    from mcp_swagger_cli.parser import OpenAPIParser
    
    console.print(f"[bold cyan]Loading specification...[/bold cyan]")
    console.print()
    
    try:
        parser = OpenAPIParser(spec_path=spec, validate=False)
        spec_info = parser.get_spec_info()
        
        # Title and version
        console.print(f"[bold]{spec_info.get('title', 'Untitled')}[/bold]")
        console.print(f"Version: {spec_info.get('version', 'N/A')}")
        console.print()
        
        # Description
        if spec_info.get('description'):
            console.print(f"[dim]{spec_info['description']}[/dim]")
            console.print()
        
        # Servers
        servers = spec_info.get('servers', [])
        if servers:
            console.print("[bold]Servers:[/bold]")
            for server in servers:
                console.print(f"  • {server}")
            console.print()
        
        # Paths grouped by tag
        paths_by_tag = spec_info.get('paths_by_tag', {})
        if paths_by_tag:
            console.print("[bold]API Endpoints by Tag:[/bold]")
            for tag, paths in paths_by_tag.items():
                console.print(f"\n  [cyan]{tag}:[/cyan]")
                for path, methods in paths:
                    for method in methods:
                        console.print(f"    {method.upper():6} {path}")
            console.print()
        
        # Schemas
        schemas = spec_info.get('schemas', [])
        if schemas:
            console.print("[bold]Schemas:[/bold]")
            for schema in schemas:
                console.print(f"  • {schema}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
