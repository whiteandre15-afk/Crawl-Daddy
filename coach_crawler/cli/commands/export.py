from pathlib import Path

import typer
from rich.console import Console

from coach_crawler.exporters.csv_exporter import export_csv
from coach_crawler.exporters.json_exporter import export_json
from coach_crawler.exporters.excel_exporter import export_excel

app = typer.Typer()
console = Console()


@app.command("run")
def run_export(
    format: str = typer.Option("csv", help="Output format: csv, json, excel"),
    output: str = typer.Option("exports/coaches", help="Output file path (without extension)"),
    level: str = typer.Option(None, help="Filter by level: college, high_school, youth"),
    sub_level: str = typer.Option(None, help="Filter by sub-level: middle_school, club_team, rec_league, etc."),
    division: str = typer.Option(None, help="Filter by division"),
    state: str = typer.Option(None, help="Filter by state (2-letter code)"),
    sport: str = typer.Option(None, help="Filter by sport (normalized name)"),
    verified_only: bool = typer.Option(False, help="Only export verified emails"),
):
    """Export coaching data to file."""
    output_dir = Path(output).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    filters = {
        "level": level,
        "sub_level": sub_level,
        "division": division,
        "state": state,
        "sport": sport,
        "verified_only": verified_only,
    }

    if format == "csv":
        path = export_csv(f"{output}.csv", filters)
    elif format == "json":
        path = export_json(f"{output}.json", filters)
    elif format == "excel":
        path = export_excel(f"{output}.xlsx", filters)
    else:
        console.print(f"[red]Unknown format: {format}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold green]Exported to {path}[/bold green]")
