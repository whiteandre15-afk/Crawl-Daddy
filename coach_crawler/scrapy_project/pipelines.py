import hashlib
import logging
import re
from datetime import datetime, timezone

from scrapy.exceptions import DropItem

from coach_crawler.models import SessionLocal, Coach, School, CrawlJob
from coach_crawler.utils.url_utils import make_slug

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


class EmailValidationPipeline:
    """Validate and normalize email addresses."""

    def process_item(self, item, spider):
        email = item.get("email", "").strip().lower()
        if not email or not _EMAIL_RE.match(email):
            raise DropItem(f"Invalid email: {email}")

        item["email"] = email
        item["email_hash"] = hashlib.sha256(email.encode()).hexdigest()
        return item


class DeduplicationPipeline:
    """Skip duplicate emails within a single crawl run."""

    def __init__(self):
        self.seen: set[tuple[str, int | None]] = set()

    def process_item(self, item, spider):
        key = (item["email_hash"], item.get("school_id"))
        if key in self.seen:
            raise DropItem(f"Duplicate: {item['email']}")
        self.seen.add(key)
        return item


class DatabasePipeline:
    """Write validated, deduplicated coach items to the database."""

    def open_spider(self, spider):
        self.session = SessionLocal()
        self.crawl_job_id = getattr(spider, "crawl_job_id", None)
        self.items_saved = 0
        self.items_found = 0
        self.crawled_schools: set[int] = set()

    def close_spider(self, spider):
        if self.crawl_job_id:
            try:
                job = self.session.query(CrawlJob).filter(CrawlJob.id == self.crawl_job_id).first()
                if job:
                    job.coaches_found = self.items_found
                    job.urls_completed = len(self.crawled_schools)
                    self.session.commit()
            except Exception:
                self.session.rollback()
        self.session.close()
        logger.info(f"Pipeline: found {self.items_found} coaches, {self.items_saved} new saves, {len(self.crawled_schools)} schools processed")

    def process_item(self, item, spider):
        self.items_found += 1
        school_id = item.get("school_id")

        # Mark school as crawled
        if school_id and school_id not in self.crawled_schools:
            try:
                school = self.session.query(School).filter(School.id == school_id).first()
                if school:
                    school.crawl_status = "crawled"
                    school.last_crawled_at = datetime.now(timezone.utc)
                    self.session.commit()
                self.crawled_schools.add(school_id)
            except Exception:
                self.session.rollback()

        # Upsert: check if coach already exists
        existing = self.session.query(Coach).filter(
            Coach.email_hash == item["email_hash"],
            Coach.school_id == school_id,
        ).first()

        try:
            if existing:
                # Update existing record with fresh data
                if item.get("full_name"):
                    existing.full_name = item["full_name"]
                    existing.first_name = item.get("first_name")
                    existing.last_name = item.get("last_name")
                if item.get("title"):
                    existing.title = item["title"]
                if item.get("role_category"):
                    existing.role_category = item["role_category"]
                if item.get("sport_normalized"):
                    existing.sport = item.get("sport")
                    existing.sport_normalized = item["sport_normalized"]
                existing.source_url = item["source_url"]
                existing.confidence_score = item.get("confidence_score", 0.0)
            else:
                coach = Coach(
                    email=item["email"],
                    email_hash=item["email_hash"],
                    first_name=item.get("first_name"),
                    last_name=item.get("last_name"),
                    full_name=item.get("full_name"),
                    title=item.get("title"),
                    role_category=item.get("role_category"),
                    sport=item.get("sport"),
                    sport_normalized=item.get("sport_normalized"),
                    school_id=school_id,
                    level=item.get("level", ""),
                    sub_level=item.get("sub_level"),
                    state=item.get("state", ""),
                    source_url=item["source_url"],
                    confidence_score=item.get("confidence_score", 0.0),
                )
                self.session.add(coach)
                self.items_saved += 1

            self.session.commit()

            # Update crawl job progress every 10 items
            if self.crawl_job_id and self.items_found % 10 == 0:
                job = self.session.query(CrawlJob).filter(CrawlJob.id == self.crawl_job_id).first()
                if job:
                    job.coaches_found = self.items_found
                    job.urls_completed = len(self.crawled_schools)
                    self.session.commit()

        except Exception:
            self.session.rollback()
            logger.exception(f"Failed to save coach: {item['email']}")

        return item


class SchoolSeedPipeline:
    """Write discovered school/organization records to the schools table."""

    def open_spider(self, spider):
        self.session = SessionLocal()
        self.items_saved = 0

    def close_spider(self, spider):
        self.session.close()
        logger.info(f"SchoolSeedPipeline: saved {self.items_saved} new schools")

    def process_item(self, item, spider):
        from coach_crawler.scrapy_project.items import SchoolItem

        if not isinstance(item, SchoolItem):
            return item

        slug = item.get("slug") or make_slug(item["name"])
        existing = self.session.query(School).filter(School.slug == slug).first()
        if existing:
            raise DropItem(f"School already exists: {slug}")

        school = School(
            name=item["name"],
            slug=slug,
            level=item["level"],
            sub_level=item.get("sub_level"),
            organization_type=item.get("organization_type"),
            division=item.get("division"),
            conference=item.get("conference"),
            state=item.get("state", ""),
            city=item.get("city"),
            athletics_url=item.get("athletics_url"),
            staff_directory_url=item.get("staff_directory_url"),
            website_platform=item.get("website_platform"),
            crawl_status="pending",
        )
        self.session.add(school)
        try:
            self.session.commit()
            self.items_saved += 1
        except Exception:
            self.session.rollback()
            logger.exception(f"Failed to save school: {item['name']}")

        return item
