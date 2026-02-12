import typer
from rich.console import Console
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

app = typer.Typer()
console = Console()


@app.command("extract")
def extract(
    level: str = typer.Option("college", help="Level: college, high_school, youth"),
    sub_level: str = typer.Option(None, help="Sub-level: middle_school, club_team, rec_league, academy, camp, etc."),
    platform: str = typer.Option(None, help="Platform filter: sidearm, prestosports, custom"),
    division: str = typer.Option(None, help="Division filter: NCAA_D1_FBS, NCAA_D2, etc."),
    state: str = typer.Option(None, help="State filter: 2-letter code"),
    limit: int = typer.Option(None, help="Max schools to crawl"),
):
    """Run email extraction crawl."""
    import os
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "coach_crawler.scrapy_project.settings")

    settings = get_project_settings()
    process = CrawlerProcess(settings)

    # Pick spider based on platform
    spider_map = {
        "sidearm": "sidearm_staff",
        "prestosports": "prestosports_staff",
        "custom": "college_staff",
    }

    if level == "high_school":
        spider_name = "hs_staff"
    elif level == "youth":
        spider_name = "youth_staff"
    else:
        spider_name = spider_map.get(platform, "college_staff")

    kwargs = {}
    if division:
        kwargs["division"] = division
    if state:
        kwargs["state"] = state
    if limit:
        kwargs["limit"] = limit
    if sub_level:
        kwargs["sub_level"] = sub_level
    kwargs["level"] = level

    console.print(f"[bold green]Starting {spider_name} spider...[/bold green]")
    process.crawl(spider_name, **kwargs)
    process.start()
    console.print("[bold green]Crawl complete.[/bold green]")


@app.command("discover")
def discover(
    level: str = typer.Option("college", help="Level: college, high_school, youth"),
    sub_level: str = typer.Option(None, help="Sub-level filter"),
    division: str = typer.Option(None, help="Division filter"),
    state: str = typer.Option(None, help="State filter"),
    limit: int = typer.Option(None, help="Max schools"),
):
    """Discover staff directory URLs from athletics homepages."""
    import os
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "coach_crawler.scrapy_project.settings")

    settings = get_project_settings()
    process = CrawlerProcess(settings)

    kwargs = {"level": level}
    if sub_level:
        kwargs["sub_level"] = sub_level
    if division:
        kwargs["division"] = division
    if state:
        kwargs["state"] = state
    if limit:
        kwargs["limit"] = limit

    console.print(f"[bold green]Starting directory discovery for {level}...[/bold green]")
    process.crawl("college_staff", **kwargs)
    process.start()
    console.print("[bold green]Discovery complete.[/bold green]")


@app.command("seed-discover")
def seed_discover(
    source: str = typer.Argument(help="Source: maxpreps, state_athletic, us_club_soccer, aau, pop_warner, little_league, ymca, usa_swimming, sportsengine, leagueapps, usa_football, usssa, babe_ruth, us_youth_soccer, usa_hockey, usa_wrestling, us_lacrosse, pony_baseball, ayso, i9_sports, upward_sports, usa_volleyball, usatf"),
    state: str = typer.Option(None, help="State filter"),
    limit: int = typer.Option(None, help="Max items to discover"),
):
    """Run a seed discovery spider to populate the schools table from public directories."""
    import os
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "coach_crawler.scrapy_project.settings")

    spider_map = {
        # College/HS seeds
        "ncaa_directory": "ncaa_directory_seed",
        "maxpreps": "maxpreps_seed",
        "state_athletic": "state_athletic_assoc_seed",
        # Youth — original 6 sources
        "us_club_soccer": "us_club_soccer_seed",
        "aau": "aau_seed",
        "pop_warner": "pop_warner_seed",
        "little_league": "little_league_seed",
        "ymca": "ymca_seed",
        "usa_swimming": "usa_swimming_seed",
        # Youth — platforms
        "sportsengine": "sportsengine_seed",
        "leagueapps": "leagueapps_seed",
        # Youth — national organizations
        "usa_football": "usa_football_seed",
        "usssa": "usssa_seed",
        "babe_ruth": "babe_ruth_seed",
        "us_youth_soccer": "us_youth_soccer_seed",
        "usa_hockey": "usa_hockey_seed",
        "usa_wrestling": "usa_wrestling_seed",
        "us_lacrosse": "us_lacrosse_seed",
        "pony_baseball": "pony_baseball_seed",
        "ayso": "ayso_seed",
        "i9_sports": "i9_sports_seed",
        "upward_sports": "upward_sports_seed",
        "usa_volleyball": "usa_volleyball_seed",
        "usatf": "usatf_seed",
    }

    spider_name = spider_map.get(source)
    if not spider_name:
        console.print(f"[red]Unknown source: {source}[/red]")
        console.print(f"[yellow]Available: {', '.join(spider_map.keys())}[/yellow]")
        raise typer.Exit(1)

    settings = get_project_settings()
    process = CrawlerProcess(settings)

    kwargs = {}
    if state:
        kwargs["state"] = state
    if limit:
        kwargs["limit"] = limit

    console.print(f"[bold green]Starting seed discovery: {source}...[/bold green]")
    process.crawl(spider_name, **kwargs)
    process.start()
    console.print("[bold green]Seed discovery complete.[/bold green]")
