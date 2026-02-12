import re
import scrapy
import logging

from coach_crawler.models import SessionLocal, School
from coach_crawler.scrapy_project.spiders.base_staff_spider import BaseStaffSpider

logger = logging.getLogger(__name__)

# URL patterns for domain guessing when youth orgs lack a URL
YOUTH_URL_PATTERNS = [
    "https://www.{slug}.org",
    "https://{slug}.org",
    "https://www.{slug}.com",
    "https://www.{slug}.net",
    "https://{slug}.sportsengine.com",
    "https://{slug}.leagueapps.com",
]

# Staff page suffixes to try on youth org domains
YOUTH_STAFF_SUFFIXES = [
    "/staff", "/coaches", "/about/staff", "/our-team",
    "/staff-directory", "/coaching-staff", "/contacts",
    "/about-us", "/board-of-directors", "/board",
    "/leadership", "/our-coaches", "/league-officers",
]


class YouthStaffSpider(BaseStaffSpider):
    """Crawl youth organization websites for coaching contacts.

    Covers club teams, rec leagues, academies, camps, YMCA, Pop Warner,
    Little League, AAU, and other youth sports organizations.
    """

    name = "youth_staff"

    custom_settings = {
        **BaseStaffSpider.custom_settings,
        "DEPTH_LIMIT": 3,
    }

    def _make_url_slug(self, name: str) -> str:
        """Convert org name to URL-friendly slug for domain guessing."""
        name = re.sub(
            r'\s*(youth|sports|league|club|association|organization|inc\.?|llc)\s*$',
            '', name, flags=re.IGNORECASE,
        )
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s]', '', slug)
        slug = re.sub(r'\s+', '', slug)
        return slug

    def start_requests(self):
        session = SessionLocal()
        try:
            query = session.query(School).filter(
                School.level == "youth",
                School.crawl_status.in_(["pending", "failed"]),
            )

            if self.sub_level:
                query = query.filter(School.sub_level == self.sub_level)
            if self.state:
                query = query.filter(School.state == self.state)
            if self.limit:
                query = query.limit(self.limit)

            schools = query.all()
            logger.info(f"Starting youth crawl for {len(schools)} organizations")

            for school in schools:
                meta = {
                    "school": {
                        "id": school.id,
                        "name": school.name,
                        "level": school.level,
                        "sub_level": school.sub_level,
                        "state": school.state,
                    },
                    "depth": 0,
                }

                # Direct staff directory URL — best case
                if school.staff_directory_url:
                    yield scrapy.Request(
                        school.staff_directory_url,
                        callback=self.parse_staff_directory,
                        meta={**meta, "playwright": True, "playwright_include_page": False},
                        errback=self.handle_error,
                    )
                    continue

                # Has a homepage/athletics URL
                if school.athletics_url:
                    yield scrapy.Request(
                        school.athletics_url,
                        callback=self.parse_youth_home,
                        meta={**meta, "playwright": True, "playwright_include_page": False},
                        errback=self.handle_error,
                    )
                    continue

                # No URL — try domain guessing
                slug = self._make_url_slug(school.name)
                if not slug:
                    continue

                urls_to_try = [p.format(slug=slug) for p in YOUTH_URL_PATTERNS]
                meta["fallback_urls"] = urls_to_try[1:]
                yield scrapy.Request(
                    urls_to_try[0],
                    callback=self.parse_youth_home,
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
                callback=self.parse_youth_home,
                meta=meta,
                errback=self.try_next_url,
                dont_filter=True,
            )

    def parse_youth_home(self, response):
        """Find coaching/staff/about pages from youth org homepage."""
        # Check platform for optimized parsing
        platform = self.detect_platform(response)
        if platform == "sportsengine":
            yield from self._parse_platform_site(response, [
                "/staff", "/contacts", "/about/staff", "/page/show/staff",
            ])
            return
        if platform == "leagueapps":
            yield from self._parse_platform_site(response, [
                "/staff", "/contacts", "/about", "/coaches",
            ])
            return

        # Try page classifier first — finds scored staff directory links
        candidates = self.page_classifier.find_staff_directory_links(response)
        if candidates:
            best = candidates[0]
            yield scrapy.Request(
                best["url"],
                callback=self.parse_staff_directory,
                meta=response.meta,
                errback=self.handle_error,
            )
            return

        # Search for keyword links — follow ALL matches, not just first
        keywords = [
            "coaches", "staff", "about", "contact", "our team",
            "trainers", "instructors", "directors", "league info", "programs",
            "board of directors", "board members", "league officers",
            "volunteer coaches", "team managers", "coaching staff",
            "our coaches", "meet our coaches", "league contacts",
            "administration", "leadership", "who we are",
        ]

        found_any = False
        seen_urls = set()
        for link in response.css("a"):
            text = " ".join(link.css("::text").getall()).strip().lower()
            href = link.attrib.get("href", "")

            if any(kw in text for kw in keywords):
                full_url = response.urljoin(href)
                if full_url not in seen_urls and full_url != response.url:
                    seen_urls.add(full_url)
                    found_any = True
                    yield scrapy.Request(
                        full_url,
                        callback=self.parse_staff_directory,
                        meta=response.meta,
                        errback=self.handle_error,
                    )

        if found_any:
            return

        # Try common staff page suffixes
        base = response.url.rstrip("/")
        for suffix in YOUTH_STAFF_SUFFIXES:
            yield scrapy.Request(
                base + suffix,
                callback=self.parse_staff_directory,
                meta=response.meta,
                errback=self.handle_error,
            )

    def _parse_platform_site(self, response, staff_paths):
        """For known platforms, try standardized staff page paths."""
        base = response.url.rstrip("/")
        for path in staff_paths:
            yield scrapy.Request(
                base + path,
                callback=self.parse_staff_directory,
                meta=response.meta,
                errback=self.handle_error,
            )
        # Also check if the homepage itself has contacts
        confidence = self.page_classifier.is_staff_directory_page(response)
        if confidence > 0.15:
            yield from self.parse_staff_directory(response)

    def handle_error(self, failure):
        logger.debug(f"Youth request failed: {failure.request.url}")
