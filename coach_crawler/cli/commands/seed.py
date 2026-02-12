import csv
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import track

from coach_crawler.models import SessionLocal, School
from coach_crawler.utils.url_utils import make_slug

app = typer.Typer()
console = Console()

SEEDS_DIR = Path(__file__).resolve().parents[3] / "seeds"


@app.command("load")
def load_seeds(
    source: str = typer.Argument(help="Source: ncaa_d1, ncaa_d2, ncaa_d3, naia, njcaa, hs, ms, youth, all_colleges"),
    file: str = typer.Option(None, help="Custom CSV file path (overrides source)"),
):
    """Load seed school data from CSV files into the database."""
    if file:
        csv_path = Path(file)
    else:
        csv_path = SEEDS_DIR / f"{source}_schools.csv"

    if not csv_path.exists():
        console.print(f"[red]Seed file not found: {csv_path}[/red]")
        console.print(f"[yellow]Available seeds: {', '.join(p.stem for p in SEEDS_DIR.glob('*.csv'))}[/yellow]")
        raise typer.Exit(1)

    session = SessionLocal()
    try:
        count = 0
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        for row in track(rows, description=f"Loading {source}..."):
            slug = make_slug(row["name"])

            # Skip if already exists
            existing = session.query(School).filter(School.slug == slug).first()
            if existing:
                continue

            school = School(
                name=row["name"],
                slug=slug,
                level=row.get("level", "college"),
                sub_level=row.get("sub_level"),
                division=row.get("division"),
                conference=row.get("conference"),
                state=row.get("state", ""),
                city=row.get("city"),
                athletics_url=row.get("athletics_url"),
                organization_type=row.get("organization_type"),
                crawl_status="pending",
            )
            session.add(school)
            count += 1

        session.commit()
        console.print(f"[bold green]Loaded {count} new schools from {source}[/bold green]")
    finally:
        session.close()


@app.command("list")
def list_seeds():
    """List available seed files."""
    csv_files = sorted(SEEDS_DIR.glob("*.csv"))
    json_files = sorted(SEEDS_DIR.glob("*.json"))

    console.print("[bold]Available seed files:[/bold]")
    for f in csv_files + json_files:
        console.print(f"  {f.name}")

    if not csv_files and not json_files:
        console.print("[yellow]  No seed files found. Add CSVs to seeds/ directory.[/yellow]")


@app.command("load-nces")
def load_nces(
    file: str = typer.Argument(help="Path to NCES CCD data file (CSV)"),
    state: str = typer.Option(None, help="Filter by state (2-letter code)"),
):
    """Load high school and middle school data from NCES CCD download.

    First process the raw NCES file with: python scripts/process_nces_data.py <file>
    Then load the generated seeds: coach-crawler seed load hs --file seeds/hs_schools.csv
    Or use this command to do both steps at once.
    """
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[3] / "scripts" / "process_nces_data.py"
    cmd = [sys.executable, str(script), file]
    if state:
        cmd.extend(["--state", state])

    console.print("[bold green]Processing NCES data...[/bold green]")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Error: {result.stderr}[/red]")
        raise typer.Exit(1)
    console.print(result.stdout)

    # Now load the generated seed files
    for seed_file in ["hs_schools.csv", "ms_schools.csv"]:
        seed_path = SEEDS_DIR / seed_file
        if seed_path.exists():
            load_seeds(seed_file.replace("_schools.csv", ""), file=str(seed_path))
