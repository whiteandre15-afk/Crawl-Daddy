import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import func

from coach_crawler.models import SessionLocal, School, Coach, CrawlJob

app = typer.Typer()
console = Console()


@app.command("overview")
def overview():
    """Show crawl progress overview."""
    session = SessionLocal()
    try:
        # Schools stats
        total_schools = session.query(func.count(School.id)).scalar()
        crawled_schools = session.query(func.count(School.id)).filter(School.crawl_status == "crawled").scalar()
        pending_schools = session.query(func.count(School.id)).filter(School.crawl_status == "pending").scalar()
        failed_schools = session.query(func.count(School.id)).filter(School.crawl_status == "failed").scalar()

        # Coach stats
        total_coaches = session.query(func.count(Coach.id)).scalar()
        verified_coaches = session.query(func.count(Coach.id)).filter(Coach.is_verified).scalar()
        unique_emails = session.query(func.count(func.distinct(Coach.email))).scalar()

        # By level
        level_stats = (
            session.query(Coach.level, func.count(Coach.id))
            .group_by(Coach.level)
            .all()
        )

        # By state (top 10)
        state_stats = (
            session.query(Coach.state, func.count(Coach.id))
            .group_by(Coach.state)
            .order_by(func.count(Coach.id).desc())
            .limit(10)
            .all()
        )

        # Schools table
        school_table = Table(title="Schools")
        school_table.add_column("Status", style="cyan")
        school_table.add_column("Count", justify="right")
        school_table.add_row("Total", str(total_schools))
        school_table.add_row("Crawled", str(crawled_schools))
        school_table.add_row("Pending", str(pending_schools))
        school_table.add_row("Failed", str(failed_schools))
        console.print(school_table)

        # Coaches table
        coach_table = Table(title="Coaches")
        coach_table.add_column("Metric", style="cyan")
        coach_table.add_column("Count", justify="right")
        coach_table.add_row("Total Records", str(total_coaches))
        coach_table.add_row("Unique Emails", str(unique_emails))
        coach_table.add_row("Verified", str(verified_coaches))
        console.print(coach_table)

        # By level
        if level_stats:
            level_table = Table(title="By Level")
            level_table.add_column("Level", style="cyan")
            level_table.add_column("Count", justify="right")
            for level, count in level_stats:
                level_table.add_row(level or "unknown", str(count))
            console.print(level_table)

        # By level/sub-level
        sub_level_stats = (
            session.query(Coach.level, Coach.sub_level, func.count(Coach.id))
            .group_by(Coach.level, Coach.sub_level)
            .all()
        )

        if sub_level_stats:
            sub_table = Table(title="By Level / Sub-Level")
            sub_table.add_column("Level", style="cyan")
            sub_table.add_column("Sub-Level", style="green")
            sub_table.add_column("Count", justify="right")
            for level, sub_level, count in sub_level_stats:
                sub_table.add_row(level or "unknown", sub_level or "-", str(count))
            console.print(sub_table)

        # Schools by level
        school_level_stats = (
            session.query(School.level, func.count(School.id))
            .group_by(School.level)
            .all()
        )

        if school_level_stats:
            school_level_table = Table(title="Schools by Level")
            school_level_table.add_column("Level", style="cyan")
            school_level_table.add_column("Count", justify="right")
            for level, count in school_level_stats:
                school_level_table.add_row(level or "unknown", str(count))
            console.print(school_level_table)

        # By state
        if state_stats:
            state_table = Table(title="Top 10 States")
            state_table.add_column("State", style="cyan")
            state_table.add_column("Count", justify="right")
            for state, count in state_stats:
                state_table.add_row(state or "??", str(count))
            console.print(state_table)

    finally:
        session.close()
