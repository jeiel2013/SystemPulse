"""Command-line entry point for the development package."""

import typer

from systempulse.version import get_version

app = typer.Typer(
    add_completion=False,
    help="Local system monitoring and diagnostics for your terminal.",
)


@app.callback(invoke_without_command=True)
def root(context: typer.Context) -> None:
    """Show the current development state when no command is selected."""
    if context.invoked_subcommand is None:
        typer.echo("Live monitoring is not available in this development build.")


@app.command()
def version() -> None:
    """Show the installed SystemPulse version."""
    typer.echo(f"SystemPulse {get_version()}")


def main() -> None:
    """Run the SystemPulse command-line application."""
    app()
