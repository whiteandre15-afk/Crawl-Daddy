import os
import sys
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def run_spider_process(crawl_id: int, spider_name: str, spider_kwargs: dict):
    """Run a Scrapy spider in a separate process."""
    _setup_env()
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from coach_crawler.models import SessionLocal, CrawlJob, School
    from sqlalchemy import func

    # Mark job as running
    session = SessionLocal()
    try:
        job = session.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
        if job:
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            if "seed" not in spider_name:
                level = spider_kwargs.get("level", "college")
                total = session.query(func.count(School.id)).filter(
                    School.level == level,
                    School.crawl_status.in_(["pending", "failed"]),
                ).scalar() or 0
                job.urls_total = total
            session.commit()
    finally:
        session.close()

    spider_kwargs["crawl_job_id"] = str(crawl_id)

    try:
        settings = _get_settings()
        process = CrawlerProcess(settings)
        process.crawl(spider_name, **spider_kwargs)
        process.start()

        session = SessionLocal()
        try:
            job = session.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
            if job:
                job.status = "completed"
                job.finished_at = datetime.now(timezone.utc)
                session.commit()
        finally:
            session.close()

    except Exception as e:
        logger.exception(f"Spider {spider_name} failed: {e}")
        session = SessionLocal()
        try:
            job = session.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
            if job:
                job.status = "failed"
                job.finished_at = datetime.now(timezone.utc)
                session.commit()
        finally:
            session.close()


def run_all_spiders(crawl_jobs: list[dict]):
    """Run multiple spiders sequentially in a single process.

    Each entry: {"crawl_id": int, "spider_name": str, "spider_kwargs": dict}
    """
    _setup_env()
    from scrapy.crawler import CrawlerRunner
    from scrapy.utils.project import get_project_settings
    from coach_crawler.models import SessionLocal, CrawlJob, School
    from sqlalchemy import func
    from twisted.internet import reactor, defer

    settings = _get_settings()
    runner = CrawlerRunner(settings)

    @defer.inlineCallbacks
    def crawl_sequentially():
        for entry in crawl_jobs:
            crawl_id = entry["crawl_id"]
            spider_name = entry["spider_name"]
            spider_kwargs = entry["spider_kwargs"]
            spider_kwargs["crawl_job_id"] = str(crawl_id)

            # Mark as running
            session = SessionLocal()
            try:
                job = session.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
                if job:
                    job.status = "running"
                    job.started_at = datetime.now(timezone.utc)
                    if "seed" not in spider_name:
                        level = spider_kwargs.get("level", "college")
                        total = session.query(func.count(School.id)).filter(
                            School.level == level,
                            School.crawl_status.in_(["pending", "failed"]),
                        ).scalar() or 0
                        job.urls_total = total
                    session.commit()
            finally:
                session.close()

            # Run spider
            try:
                yield runner.crawl(spider_name, **spider_kwargs)

                session = SessionLocal()
                try:
                    job = session.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
                    if job:
                        job.status = "completed"
                        job.finished_at = datetime.now(timezone.utc)
                        session.commit()
                finally:
                    session.close()

            except Exception as e:
                logger.exception(f"Spider {spider_name} failed: {e}")
                session = SessionLocal()
                try:
                    job = session.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
                    if job:
                        job.status = "failed"
                        job.finished_at = datetime.now(timezone.utc)
                        session.commit()
                finally:
                    session.close()

        reactor.stop()

    crawl_sequentially()
    reactor.run()


def _setup_env():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "coach_crawler.scrapy_project.settings")


def _get_settings():
    from scrapy.utils.project import get_project_settings
    settings = get_project_settings()
    settings.set("DOWNLOAD_HANDLERS", {})
    settings.set("TWISTED_REACTOR", None)
    settings.set("CONCURRENT_REQUESTS", 32)
    settings.set("CONCURRENT_REQUESTS_PER_DOMAIN", 2)
    settings.set("DOWNLOAD_DELAY", 0.5)
    settings.set("AUTOTHROTTLE_TARGET_CONCURRENCY", 8.0)
    settings.set("LOG_LEVEL", "INFO")
    return settings
