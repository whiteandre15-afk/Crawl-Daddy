import scrapy
import logging

from coach_crawler.scrapy_project.items import SchoolItem
from coach_crawler.utils.url_utils import make_slug

logger = logging.getLogger(__name__)


class BaseSeedSpider(scrapy.Spider):
    """Base spider for discovering schools/organizations to seed the schools table.

    Seed discovery spiders use SchoolSeedPipeline instead of the default coach
    pipeline chain. They yield SchoolItem instances rather than CoachItem.
    """

    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 3.0,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        "ROBOTSTXT_OBEY": True,
        "ITEM_PIPELINES": {
            "coach_crawler.scrapy_project.pipelines.SchoolSeedPipeline": 300,
        },
    }

    # All 50 US state codes for iteration
    US_STATES = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        "DC",
    ]

    def __init__(self, state=None, limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state
        self.limit = int(limit) if limit else None
        self.items_yielded = 0

    def make_playwright_request(self, url, callback, errback=None, meta=None):
        """Create a request that uses Playwright for JS rendering."""
        meta = meta or {}
        meta["playwright"] = True
        meta["playwright_include_page"] = False
        return scrapy.Request(url, callback=callback, errback=errback, meta=meta)

    def handle_error(self, failure):
        logger.error(f"{self.name} request failed: {failure.request.url} — {failure.value}")

    def make_school_item(self, name, level, sub_level, state, city=None,
                         athletics_url=None, organization_type=None, **kwargs):
        """Helper to construct a SchoolItem with slug generation."""
        if self.limit and self.items_yielded >= self.limit:
            return None

        # Append state to slug to avoid collisions (e.g. "Central High School" in every state)
        slug = make_slug(name) + "-" + state.lower() if state else make_slug(name)

        self.items_yielded += 1
        return SchoolItem(
            name=name,
            slug=slug,
            level=level,
            sub_level=sub_level,
            state=state or "",
            city=city,
            athletics_url=athletics_url,
            organization_type=organization_type,
            **kwargs,
        )
