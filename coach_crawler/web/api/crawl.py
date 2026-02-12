import multiprocessing

from fastapi import APIRouter
from pydantic import BaseModel

from coach_crawler.models import SessionLocal, CrawlJob
from coach_crawler.web.crawl_runner import run_spider_process, run_all_spiders

router = APIRouter()

PLATFORM_SPIDER_MAP = {
    "sidearm": "sidearm_staff",
    "prestosports": "prestosports_staff",
    "custom": "college_staff",
}

LEVEL_SPIDER_MAP = {
    "college": "college_staff",
    "high_school": "hs_staff",
    "youth": "youth_staff",
}


class CrawlRequest(BaseModel):
    level: str = "college"
    sub_level: str | None = None
    division: str | None = None
    state: str | None = None
    limit: int | None = None
    spider_name: str | None = None
    platform: str | None = None


@router.post("/crawl")
def start_crawl(req: CrawlRequest):
    # Auto-detect spider
    if req.spider_name:
        spider_name = req.spider_name
    elif req.level == "high_school":
        spider_name = "hs_staff"
    elif req.level == "youth":
        spider_name = "youth_staff"
    else:
        spider_name = PLATFORM_SPIDER_MAP.get(req.platform, "college_staff")

    # Create crawl job record
    session = SessionLocal()
    try:
        crawl_job = CrawlJob(
            spider_name=spider_name,
            status="starting",
            config_snapshot={
                "level": req.level,
                "sub_level": req.sub_level,
                "division": req.division,
                "state": req.state,
                "limit": req.limit,
                "platform": req.platform,
            },
        )
        session.add(crawl_job)
        session.commit()
        crawl_id = crawl_job.id
    finally:
        session.close()

    # Start spider in background process
    spider_kwargs = {"level": req.level}
    if req.sub_level:
        spider_kwargs["sub_level"] = req.sub_level
    if req.division:
        spider_kwargs["division"] = req.division
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


@router.get("/crawl/{crawl_id}")
def get_crawl(crawl_id: int):
    session = SessionLocal()
    try:
        job = session.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
        if not job:
            return {"error": "Crawl not found"}
        return {
            "id": job.id,
            "spider_name": job.spider_name,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "urls_total": job.urls_total,
            "urls_completed": job.urls_completed,
            "urls_failed": job.urls_failed,
            "coaches_found": job.coaches_found,
            "config_snapshot": job.config_snapshot,
        }
    finally:
        session.close()


YOUTH_SEED_SPIDERS = [
    # Original 6 sources
    "us_club_soccer_seed", "aau_seed", "pop_warner_seed",
    "little_league_seed", "ymca_seed", "usa_swimming_seed",
    # Platform discovery
    "sportsengine_seed", "leagueapps_seed",
    # National organizations
    "usa_football_seed", "usssa_seed", "babe_ruth_seed",
    "us_youth_soccer_seed", "usa_hockey_seed", "usa_wrestling_seed",
    "us_lacrosse_seed", "pony_baseball_seed", "ayso_seed",
    "i9_sports_seed", "upward_sports_seed", "usa_volleyball_seed",
    "usatf_seed",
]


@router.post("/crawl-all")
def start_crawl_all():
    """Start crawls for all levels sequentially in one background process.

    Flow: college_staff → hs_staff → youth seed discovery → youth_staff
    """
    session = SessionLocal()
    crawl_jobs_list = []

    try:
        # 1. College extraction
        job = CrawlJob(spider_name="college_staff", status="queued", config_snapshot={"level": "college"})
        session.add(job)
        session.flush()
        crawl_jobs_list.append({"crawl_id": job.id, "spider_name": "college_staff", "spider_kwargs": {"level": "college"}, "level": "college"})

        # 2. High school extraction
        job = CrawlJob(spider_name="hs_staff", status="queued", config_snapshot={"level": "high_school"})
        session.add(job)
        session.flush()
        crawl_jobs_list.append({"crawl_id": job.id, "spider_name": "hs_staff", "spider_kwargs": {"level": "high_school"}, "level": "high_school"})

        # 3. Youth seed discovery (populate youth orgs in DB)
        for seed_spider in YOUTH_SEED_SPIDERS:
            job = CrawlJob(spider_name=seed_spider, status="queued", config_snapshot={"type": "seed_discovery"})
            session.add(job)
            session.flush()
            crawl_jobs_list.append({"crawl_id": job.id, "spider_name": seed_spider, "spider_kwargs": {}, "level": "youth_seed"})

        # 4. Youth extraction (after seeds populate the table)
        job = CrawlJob(spider_name="youth_staff", status="queued", config_snapshot={"level": "youth"})
        session.add(job)
        session.flush()
        crawl_jobs_list.append({"crawl_id": job.id, "spider_name": "youth_staff", "spider_kwargs": {"level": "youth"}, "level": "youth"})

        session.commit()
    finally:
        session.close()

    process = multiprocessing.Process(
        target=run_all_spiders,
        args=(crawl_jobs_list,),
        daemon=True,
    )
    process.start()

    return {
        "status": "starting",
        "jobs": [{"crawl_id": j["crawl_id"], "spider_name": j["spider_name"], "level": j["level"]} for j in crawl_jobs_list],
    }


@router.get("/crawls")
def list_crawls():
    session = SessionLocal()
    try:
        jobs = session.query(CrawlJob).order_by(CrawlJob.id.desc()).limit(50).all()
        return [
            {
                "id": j.id,
                "spider_name": j.spider_name,
                "status": j.status,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "coaches_found": j.coaches_found,
            }
            for j in jobs
        ]
    finally:
        session.close()
