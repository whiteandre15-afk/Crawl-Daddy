import re
import scrapy
import logging
from urllib.parse import urlparse

from coach_crawler.models import SessionLocal, School
from coach_crawler.scrapy_project.spiders.base_staff_spider import BaseStaffSpider

logger = logging.getLogger(__name__)

# Common URL patterns for US high school websites
HS_URL_PATTERNS = [
    "https://www.{slug}.org",
    "https://{slug}.org",
    "https://www.{slug}.net",
    "https://www.{slug}.com",
    "https://www.{slug}hs.org",
    "https://www.{slug}highschool.org",
    "https://www.{slug}.k12.{state_lower}.us",
]

# State-specific ISD/USD patterns
STATE_DISTRICT_PATTERNS = {
    "TX": ["https://www.{slug}isd.org", "https://www.{slug}isd.net"],
    "KS": ["https://www.{slug}usd.org", "https://www.usd{slug}.org"],
    "CA": ["https://www.{slug}unified.org", "https://www.{slug}usd.org"],
}

# Staff directory suffixes to try on discovered school websites
STAFF_SUFFIXES = ["/staff", "/coaches", "/athletics/staff", "/athletics/coaches",
                  "/about/staff", "/our-team", "/staff-directory", "/coaching-staff"]


class HighSchoolStaffSpider(BaseStaffSpider):
    """Crawl high school athletics staff directories.

    Constructs likely school website URLs from school name and state,
    then finds staff/coaching pages on those sites.
    """

    name = "hs_staff"

    def _make_url_slug(self, name: str) -> str:
        """Convert school name to a URL-friendly slug for domain guessing."""
        # Remove common suffixes that aren't part of the domain
        name = re.sub(r'\s*(high school|hs|senior high|jr[./]?sr[./]?|middle school|ms)\s*$', '', name, flags=re.IGNORECASE)
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s]', '', slug)
        slug = re.sub(r'\s+', '', slug)  # no separators — domains like "allenhs.org"
        return slug

    def _make_hyphen_slug(self, name: str) -> str:
        """Hyphenated slug for k12 domains."""
        name = re.sub(r'\s*(high school|hs|senior high)\s*$', '', name, flags=re.IGNORECASE)
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug.strip('-')

    def start_requests(self):
        session = SessionLocal()
        try:
            query = session.query(School).filter(
                School.level == "high_school",
                School.crawl_status.in_(["pending", "failed"]),
            )

            if self.sub_level:
                query = query.filter(School.sub_level == self.sub_level)
            if self.state:
                query = query.filter(School.state == self.state)
            if self.limit:
                query = query.limit(self.limit)

            schools = query.all()
            logger.warning(f"Starting HS crawl for {len(schools)} schools")

            for school in schools:
                meta = {
                    "school": {
                        "id": school.id,
                        "name": school.name,
                        "level": school.level,
                        "sub_level": school.sub_level,
                        "state": school.state,
                    },
                    "tried_urls": set(),
                }

                # If we have a direct staff directory URL, use it
                if school.staff_directory_url:
                    yield scrapy.Request(
                        school.staff_directory_url,
                        callback=self.parse_staff_directory,
                        meta=meta,
                        errback=self.handle_error,
                        dont_filter=True,
                    )
                    continue

                # If the URL is a real school website (not MaxPreps), try it
                url = school.athletics_url or ""
                if url and "maxpreps.com" not in url:
                    yield scrapy.Request(
                        url,
                        callback=self.parse_school_home,
                        meta=meta,
                        errback=self.handle_error,
                        dont_filter=True,
                    )
                    continue

                # Construct likely school website URLs from name + state
                slug = self._make_url_slug(school.name)
                hyphen_slug = self._make_hyphen_slug(school.name)
                state_lower = (school.state or "").lower()

                if not slug:
                    continue

                urls_to_try = []

                # State-specific patterns
                state_upper = (school.state or "").upper()
                if state_upper in STATE_DISTRICT_PATTERNS:
                    for pattern in STATE_DISTRICT_PATTERNS[state_upper]:
                        urls_to_try.append(pattern.format(slug=slug, state_lower=state_lower))

                # General patterns
                for pattern in HS_URL_PATTERNS:
                    urls_to_try.append(pattern.format(slug=slug, state_lower=state_lower))

                # Also try hyphenated k12 domain
                urls_to_try.append(f"https://www.{hyphen_slug}.k12.{state_lower}.us")

                # Yield first URL, store rest as fallbacks
                if urls_to_try:
                    meta["fallback_urls"] = urls_to_try[1:]
                    yield scrapy.Request(
                        urls_to_try[0],
                        callback=self.parse_school_home,
                        meta=meta,
                        errback=self.try_next_url,
                        dont_filter=True,
                    )
        finally:
            session.close()

    def try_next_url(self, failure):
        """On failure, try the next URL in the fallback list."""
        meta = failure.request.meta
        fallbacks = meta.get("fallback_urls", [])

        if fallbacks:
            next_url = fallbacks.pop(0)
            meta["fallback_urls"] = fallbacks
            yield scrapy.Request(
                next_url,
                callback=self.parse_school_home,
                meta=meta,
                errback=self.try_next_url,
                dont_filter=True,
            )

    def parse_school_home(self, response):
        """Found a school website — look for staff/coaches pages."""
        # First check if this page itself has emails
        confidence = self.page_classifier.is_staff_directory_page(response)
        if confidence > 0.3:
            yield from self.parse_staff_directory(response)
            return

        # Look for staff directory links
        candidates = self.page_classifier.find_staff_directory_links(response)
        if candidates:
            best = candidates[0]
            logger.info(f"HS: Found staff link on {response.url}: {best['url']}")
            yield scrapy.Request(
                best["url"],
                callback=self.parse_staff_directory,
                meta=response.meta,
                errback=self.handle_error,
            )
            return

        # Try common staff page suffixes on this domain
        base = response.url.rstrip("/")
        for suffix in STAFF_SUFFIXES:
            yield scrapy.Request(
                base + suffix,
                callback=self.parse_staff_directory,
                meta=response.meta,
                errback=self.handle_error,
            )

    def handle_error(self, failure):
        logger.debug(f"HS request failed: {failure.request.url}")
