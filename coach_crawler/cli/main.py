import typer

from coach_crawler.cli.commands.crawl import app as crawl_app
from coach_crawler.cli.commands.export import app as export_app
from coach_crawler.cli.commands.seed import app as seed_app
from coach_crawler.cli.commands.status import app as status_app
from coach_crawler.cli.commands.validate import app as validate_app

app = typer.Typer(
    name="coach-crawler",
    help="Production-grade web crawler for coaching staff email collection.",
    no_args_is_help=True,
)

app.add_typer(crawl_app, name="crawl", help="Run crawl spiders")
app.add_typer(export_app, name="export", help="Export collected data")
app.add_typer(seed_app, name="seed", help="Populate seed data")
app.add_typer(status_app, name="status", help="View crawl progress")
app.add_typer(validate_app, name="validate", help="Validate collected data")


@app.callback()
def main():
    """Coach Crawler — Collect coaching staff emails across America."""
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )


if __name__ == "__main__":
    app()
