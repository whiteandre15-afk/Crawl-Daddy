import csv
import multiprocessing
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from coach_crawler.models import SessionLocal, CrawlJob, School
from coach_crawler.utils.url_utils import make_slug
from coach_crawler.web.crawl_runner import run_spider_process

router = APIRouter()

SEEDS_DIR = Path(__file__).resolve().parents[3] / "seeds"

SEED_SPIDER_MAP = {
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


class SeedDiscoverRequest(BaseModel):
    source: str
    state: str | None = None
    limit: int | None = None


class SeedLoadRequest(BaseModel):
    filename: str


@router.post("/seed-discover")
def seed_discover(req: SeedDiscoverRequest):
    """Start a seed discovery spider to populate the schools table."""
    spider_name = SEED_SPIDER_MAP.get(req.source)
    if not spider_name:
        return {"error": f"Unknown source: {req.source}", "available": list(SEED_SPIDER_MAP.keys())}

    session = SessionLocal()
    try:
        crawl_job = CrawlJob(
            spider_name=spider_name,
            status="starting",
            config_snapshot={
                "source": req.source,
                "state": req.state,
                "limit": req.limit,
                "type": "seed_discovery",
            },
        )
        session.add(crawl_job)
        session.commit()
        crawl_id = crawl_job.id
    finally:
        session.close()

    spider_kwargs = {}
    if req.state:
        spider_kwargs["state"] = req.state
    if req.limit:
        spider_kwargs["limit"] = str(req.limit)

    process = multiprocessing.Process(
        target=run_spider_process,
        args=(crawl_id, spider_name, spider_kwargs),
        daemon=True,
    )
    process.start()

    return {"crawl_id": crawl_id, "status": "starting", "spider_name": spider_name}


@router.get("/seed-files")
def list_seed_files():
    """List available seed CSV/JSON files."""
    files = []
    for path in sorted(SEEDS_DIR.glob("*.csv")):
        row_count = 0
        try:
            with open(path, newline="", encoding="utf-8") as f:
                row_count = sum(1 for _ in f) - 1  # subtract header
        except Exception:
            pass
        files.append({
            "name": path.name,
            "size_kb": round(path.stat().st_size / 1024, 1),
            "rows": max(0, row_count),
        })
    for path in sorted(SEEDS_DIR.glob("*.json")):
        files.append({
            "name": path.name,
            "size_kb": round(path.stat().st_size / 1024, 1),
            "rows": 0,
        })
    return {"files": files}


@router.post("/seed-load")
def seed_load(req: SeedLoadRequest):
    """Load a specific seed CSV file into the database."""
    # Prevent path traversal
    safe_name = Path(req.filename).name
    csv_path = SEEDS_DIR / safe_name

    if not csv_path.exists():
        return {"error": f"File not found: {safe_name}"}

    session = SessionLocal()
    try:
        total_new = 0
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                slug = make_slug(row["name"])
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
                    city=row.get("city", ""),
                    athletics_url=row.get("athletics_url", ""),
                    organization_type=row.get("organization_type"),
                    crawl_status="pending",
                )
                session.add(school)
                total_new += 1
        session.commit()
        total = session.query(School).count()
        return {"new_schools": total_new, "total_schools": total, "filename": safe_name}
    finally:
        session.close()


@router.post("/seed-all")
def seed_all():
    """Auto-load all available seed CSVs into the database."""
    session = SessionLocal()
    try:
        total_new = 0
        for csv_path in sorted(SEEDS_DIR.glob("*.csv")):
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    slug = make_slug(row["name"])
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
                        city=row.get("city", ""),
                        athletics_url=row.get("athletics_url", ""),
                        crawl_status="pending",
                    )
                    session.add(school)
                    total_new += 1
        session.commit()
        total = session.query(School).count()
        return {"new_schools": total_new, "total_schools": total}
    finally:
        session.close()
