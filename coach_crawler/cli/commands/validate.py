import typer
from rich.console import Console
from rich.progress import track

from coach_crawler.models import SessionLocal, Coach
from coach_crawler.validators.email_validator import validate_email
from coach_crawler.validators.dedup import deduplicate_coaches

app = typer.Typer()
console = Console()


@app.command("emails")
def validate_emails(
    check_mx: bool = typer.Option(False, help="Check MX records (slow, makes DNS queries)"),
    flag_disposable: bool = typer.Option(True, help="Flag disposable email domains"),
    batch_size: int = typer.Option(1000, help="Process in batches of N"),
):
    """Validate all collected email addresses."""
    session = SessionLocal()
    try:
        coaches = session.query(Coach).filter(Coach.is_verified == False).all()
        console.print(f"Validating {len(coaches)} unverified emails...")

        valid_count = 0
        invalid_count = 0
        disposable_count = 0

        for coach in track(coaches, description="Validating..."):
            result = validate_email(coach.email, check_mx=check_mx)

            if result["valid"]:
                coach.is_verified = True
                valid_count += 1
            else:
                invalid_count += 1

            if result["is_disposable"]:
                disposable_count += 1

        session.commit()
        console.print(f"[green]Valid: {valid_count}[/green]")
        console.print(f"[red]Invalid: {invalid_count}[/red]")
        console.print(f"[yellow]Disposable: {disposable_count}[/yellow]")
    finally:
        session.close()


@app.command("dedup")
def run_dedup(
    dry_run: bool = typer.Option(True, help="Preview without deleting"),
):
    """Remove duplicate coaching records."""
    result = deduplicate_coaches(dry_run=dry_run)
    mode = "DRY RUN" if dry_run else "APPLIED"
    console.print(f"[bold]{mode}[/bold]: {result['total_dupes']} duplicates found, {result['removed']} removed")
