import scrapy
import logging
from urllib.parse import urlparse

from coach_crawler.models import SessionLocal, School
from coach_crawler.scrapy_project.spiders.base_staff_spider import BaseStaffSpider

logger = logging.getLogger(__name__)

# Common staff directory URL patterns to try when no athletics_url is known
STAFF_DIR_SUFFIXES = [
    "/staff-directory",
    "/sports/staff",
    "/athletics/staff",
    "/staff",
    "/coaches",
]

# Known athletics URL patterns by school name keywords
ATHLETICS_DOMAIN_GUESSES = [
    "{slug}athletics.com",
    "{slug}sports.com",
    "athletics.{slug}.edu",
    "www.{slug}.edu/athletics",
]


class CollegeStaffSpider(BaseStaffSpider):
    """Crawl ALL college athletics staff directories."""

    name = "college_staff"

    def start_requests(self):
        session = SessionLocal()
        try:
            query = session.query(School).filter(School.level == "college")

            if self.division:
                query = query.filter(School.division == self.division)
            if self.state:
                query = query.filter(School.state == self.state)

            query = query.filter(School.crawl_status.in_(["pending", "failed"]))
            query = query.order_by(School.id)

            if self.limit:
                query = query.limit(self.limit)

            schools = query.all()
            logger.warning(f"Starting crawl for {len(schools)} schools")

            for school in schools:
                meta = {
                    "school": {
                        "id": school.id,
                        "name": school.name,
                        "level": school.level,
                        "sub_level": school.sub_level,
                        "state": school.state,
                        "division": school.division,
                    }
                }

                if school.staff_directory_url:
                    yield scrapy.Request(
                        school.staff_directory_url,
                        callback=self.parse_staff_directory,
                        meta=meta,
                        errback=self.handle_error,
                        dont_filter=True,
                    )
                elif school.athletics_url:
                    # Try staff directory first, fall back to homepage
                    url = school.athletics_url.rstrip("/")
                    yield scrapy.Request(
                        url + "/staff-directory",
                        callback=self.parse_staff_directory,
                        meta={**meta, "athletics_home": url},
                        errback=self.handle_staff_dir_error,
                        dont_filter=True,
                    )
                else:
                    # No URL at all — try to Google it or skip
                    # For now, try common patterns based on school name
                    name_slug = school.slug.replace("-", "")
                    for pattern in [
                        f"https://{name_slug}athletics.com/staff-directory",
                        f"https://www.{name_slug}.edu/athletics/staff-directory",
                    ]:
                        yield scrapy.Request(
                            pattern,
                            callback=self.parse_staff_directory,
                            meta=meta,
                            errback=self.handle_error,
                            dont_filter=True,
                        )
        finally:
            session.close()

    def handle_staff_dir_error(self, failure):
        """If /staff-directory fails, try the athletics homepage."""
        meta = failure.request.meta
        athletics_home = meta.get("athletics_home")
        if athletics_home:
            yield scrapy.Request(
                athletics_home,
                callback=self.parse_athletics_home,
                meta=meta,
                errback=self.handle_error,
                dont_filter=True,
            )

    def parse_athletics_home(self, response):
        """Find staff directory link from athletics homepage."""
        candidates = self.page_classifier.find_staff_directory_links(response)

        if candidates:
            best = candidates[0]
            yield scrapy.Request(
                best["url"],
                callback=self.parse_staff_directory,
                meta=response.meta,
                errback=self.handle_error,
            )
        else:
            # Try common suffixes
            base = response.url.rstrip("/")
            for suffix in STAFF_DIR_SUFFIXES[1:]:  # skip /staff-directory, already tried
                yield scrapy.Request(
                    base + suffix,
                    callback=self.parse_staff_directory,
                    meta=response.meta,
                    errback=self.handle_error,
                )

            # Also check if current page has emails
            confidence = self.page_classifier.is_staff_directory_page(response)
            if confidence > 0.3:
                yield from self.parse_staff_directory(response)

    def handle_error(self, failure):
        logger.debug(f"Request failed: {failure.request.url}")
