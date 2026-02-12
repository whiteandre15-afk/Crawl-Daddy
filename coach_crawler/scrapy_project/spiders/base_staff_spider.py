import scrapy
import logging

from coach_crawler.extractors import EmailExtractor, NameExtractor, RoleExtractor, SportClassifier, PageClassifier, email_hash
from coach_crawler.scrapy_project.items import CoachItem

logger = logging.getLogger(__name__)


class BaseStaffSpider(scrapy.Spider):
    """Abstract base spider for crawling staff directories across any level."""

    name = "base_staff"

    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 1.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 4.0,
        "ROBOTSTXT_OBEY": True,
    }

    def __init__(self, level=None, sub_level=None, state=None, division=None, limit=None, crawl_job_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.level = level
        self.sub_level = sub_level
        self.state = state
        self.division = division
        self.limit = int(limit) if limit else None
        self.crawl_job_id = int(crawl_job_id) if crawl_job_id else None

        self.email_extractor = EmailExtractor()
        self.name_extractor = NameExtractor()
        self.role_extractor = RoleExtractor()
        self.sport_classifier = SportClassifier()
        self.page_classifier = PageClassifier()

    def detect_platform(self, response) -> str:
        """Detect if page is SIDEARM, PrestoSports, SportsEngine, or other."""
        body = response.text[:5000].lower()
        if "sidearm" in body or "sidearmsports" in body:
            return "sidearm"
        if "prestosports" in body or "presto" in body:
            return "prestosports"
        if "sportsengine" in body or "se-page" in body or ".sportsengine.com" in body:
            return "sportsengine"
        if "leagueapps" in body or ".leagueapps.com" in body:
            return "leagueapps"
        if "wix.com" in body or "wixsite" in body:
            return "wix"
        if "squarespace" in body or "sqsp" in body:
            return "squarespace"
        return "custom"

    def parse_staff_directory(self, response):
        """Extract coaches from a staff directory page.

        Override in subclasses for platform-specific parsing.
        """
        school_meta = response.meta.get("school", {})
        results = self.email_extractor.extract_with_context(response, response.url)

        for result in results:
            name_parts = self.name_extractor.parse(result.get("context_name"))
            role = self.role_extractor.classify(result.get("context_title"))
            sport = self.sport_classifier.classify(result.get("context_title") or "")
            if not sport:
                sport = self.sport_classifier.classify_from_url(response.url)

            item = CoachItem(
                email=result["email"],
                email_hash=email_hash(result["email"]),
                first_name=name_parts["first_name"],
                last_name=name_parts["last_name"],
                full_name=name_parts["full_name"],
                title=result.get("context_title"),
                role_category=role,
                sport=result.get("context_title"),
                sport_normalized=sport,
                school_id=school_meta.get("id"),
                school_name=school_meta.get("name", ""),
                level=school_meta.get("level", self.level or ""),
                sub_level=school_meta.get("sub_level", self.sub_level or ""),
                state=school_meta.get("state", self.state or ""),
                source_url=response.url,
                confidence_score=result["confidence"],
            )
            yield item

        logger.info(f"Extracted {len(results)} contacts from {response.url}")
