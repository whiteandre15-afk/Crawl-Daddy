"""Scrape NCAA.com school directory to get athletics URLs for all member schools.

NCAA.com has paginated school listings at /schools-index (pages 0-23+).
Each school links to /schools/{slug} which has the actual athletics URL.
"""

import scrapy
import logging

from coach_crawler.models import SessionLocal, School
from coach_crawler.scrapy_project.spiders.base_seed_spider import BaseSeedSpider
from coach_crawler.utils.url_utils import make_slug

logger = logging.getLogger(__name__)

# Map NCAA division text to our division codes
DIVISION_MAP = {
    "division i": "NCAA_D1",
    "division i-fbs": "NCAA_D1_FBS",
    "division i-fcs": "NCAA_D1_FCS",
    "division ii": "NCAA_D2",
    "division iii": "NCAA_D3",
}


class NCAADirectorySpider(BaseSeedSpider):
    """Scrape NCAA.com to get athletics website URLs for all NCAA schools.

    Two-phase approach:
    1. Crawl /schools-index pages to get all school slugs
    2. Visit each /schools/{slug} page to get athletics URL, division, conference
    """

    name = "ncaa_directory_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def start_requests(self):
        # NCAA.com school index has ~24 pages (0-23)
        for page in range(24):
            url = f"https://www.ncaa.com/schools-index/{page}"
            yield scrapy.Request(url, callback=self.parse_index_page, errback=self.handle_error)

    def parse_index_page(self, response):
        """Extract school links from the paginated index."""
        for link in response.css("a[href*='/schools/']"):
            href = link.attrib.get("href", "")
            if "/schools-index" in href or not href.startswith("/schools/"):
                continue

            school_url = response.urljoin(href)

            # Deduplicate — only visit each school page once
            yield scrapy.Request(
                school_url,
                callback=self.parse_school_page,
                errback=self.handle_error,
                dont_filter=False,
            )

    def parse_school_page(self, response):
        """Extract athletics URL, division, conference from individual school page."""
        # School name
        name = response.css("h1::text").get("").strip()
        if not name:
            return

        # Division — look for "Division I", "Division II", "Division III"
        page_text = response.text.lower()
        division = None
        for div_text, div_code in DIVISION_MAP.items():
            if div_text in page_text:
                division = div_code
                break

        # Conference
        conference = None
        for el in response.css("p::text, span::text, div::text"):
            text = el.get("").strip()
            if "conference" in text.lower() or "Conference" in text:
                conference = text.replace("Conference:", "").replace("conference:", "").strip()
                break

        # Location — look for "City, ST" pattern
        state = ""
        city = ""
        import re
        for el in response.css("p::text, span::text, div::text"):
            text = el.get("").strip()
            match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})', text)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                break

        if self.state and state != self.state:
            return

        # Athletics URL — find external link to the athletics site
        athletics_url = None
        for link in response.css("a[href]"):
            href = link.attrib.get("href", "")
            text = " ".join(link.css("::text").getall()).strip().lower()

            # Skip NCAA.com internal links and social media
            if "ncaa.com" in href or "ncaa.org" in href:
                continue
            if any(s in href for s in ["twitter.com", "facebook.com", "instagram.com", "youtube.com"]):
                continue
            if not href.startswith("http"):
                continue

            # This is likely the athletics website
            athletics_url = href
            break

        if not athletics_url:
            logger.warning(f"NCAA: No athletics URL found for {name}")
            return

        # Check if this school already exists and just needs a URL update
        session = SessionLocal()
        try:
            slug = make_slug(name)
            existing = session.query(School).filter(School.slug == slug).first()
            if existing:
                if not existing.athletics_url or existing.athletics_url == "":
                    existing.athletics_url = athletics_url
                    if division and not existing.division:
                        existing.division = division
                    if conference and not existing.conference:
                        existing.conference = conference
                    session.commit()
                    logger.info(f"NCAA: Updated URL for {name}: {athletics_url}")
                return  # Don't yield a new item for existing schools
        finally:
            session.close()

        item = self.make_school_item(
            name=name,
            level="college",
            sub_level=None,
            state=state,
            city=city,
            athletics_url=athletics_url,
            division=division,
            conference=conference,
        )
        if item is None:
            return
        yield item

    def handle_error(self, failure):
        logger.error(f"NCAA directory request failed: {failure.request.url} — {failure.value}")
