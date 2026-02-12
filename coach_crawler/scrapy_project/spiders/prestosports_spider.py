import scrapy
import logging

from scrapy_playwright.page import PageMethod

from coach_crawler.models import SessionLocal, School
from coach_crawler.extractors import email_hash
from coach_crawler.scrapy_project.spiders.base_staff_spider import BaseStaffSpider
from coach_crawler.scrapy_project.items import CoachItem

logger = logging.getLogger(__name__)


class PrestoSportsStaffSpider(BaseStaffSpider):
    """Specialized spider for PrestoSports platform sites.

    PrestoSports powers ~1,600+ programs (heavy in D2/D3/NAIA/JUCO).
    Uses JS rendering for staff data.
    """

    name = "prestosports_staff"

    custom_settings = {
        **BaseStaffSpider.custom_settings,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
    }

    def start_requests(self):
        session = SessionLocal()
        try:
            query = session.query(School).filter(
                School.level == "college",
                School.website_platform == "prestosports",
                School.crawl_status.in_(["pending", "failed"]),
            )

            if self.division:
                query = query.filter(School.division == self.division)
            if self.state:
                query = query.filter(School.state == self.state)
            if self.limit:
                query = query.limit(self.limit)

            schools = query.all()
            logger.info(f"Starting PrestoSports crawl for {len(schools)} schools")

            for school in schools:
                url = school.staff_directory_url or school.athletics_url
                if not url:
                    continue

                if school.staff_directory_url:
                    target_url = school.staff_directory_url
                else:
                    target_url = url.rstrip("/") + "/staff-directory"

                yield scrapy.Request(
                    target_url,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", ".staff-list, .roster-coach, [class*='staff'], [class*='coach']", timeout=15000),
                        ],
                        "school": {
                            "id": school.id,
                            "name": school.name,
                            "level": school.level,
                            "sub_level": school.sub_level,
                            "state": school.state,
                            "division": school.division,
                        },
                    },
                    callback=self.parse_staff_directory,
                    errback=self.handle_error,
                )
        finally:
            session.close()

    def parse_staff_directory(self, response):
        """Parse rendered PrestoSports staff page."""
        school_meta = response.meta.get("school", {})

        staff_cards = response.css(
            ".staff-list-item, .roster-coach, [class*='staff-member'], "
            "[class*='coach-card'], .coach-info"
        )

        if staff_cards:
            for card in staff_cards:
                name = card.css(
                    "h3::text, h4::text, .coach-name::text, "
                    "[class*='name']::text, strong::text"
                ).get()

                title = card.css(
                    "[class*='title']::text, [class*='position']::text, "
                    ".coach-title::text, em::text"
                ).get()

                email_link = card.css("a[href^='mailto:']::attr(href)").get()

                if email_link:
                    email = email_link.replace("mailto:", "").split("?")[0].strip().lower()
                    if not email:
                        continue

                    name_parts = self.name_extractor.parse(name)
                    role = self.role_extractor.classify(title)
                    sport = self.sport_classifier.classify(title or "")
                    if not sport:
                        sport = self.sport_classifier.classify_from_url(response.url)

                    yield CoachItem(
                        email=email,
                        email_hash=email_hash(email),
                        first_name=name_parts["first_name"],
                        last_name=name_parts["last_name"],
                        full_name=name_parts["full_name"],
                        title=title.strip() if title else None,
                        role_category=role,
                        sport=title,
                        sport_normalized=sport,
                        school_id=school_meta.get("id"),
                        school_name=school_meta.get("name", ""),
                        level=school_meta.get("level", "college"),
                        sub_level=school_meta.get("sub_level"),
                        state=school_meta.get("state", ""),
                        source_url=response.url,
                        confidence_score=0.90,
                    )

            logger.info(f"PrestoSports: Extracted from {len(staff_cards)} cards at {response.url}")
        else:
            logger.info(f"PrestoSports: No cards found, falling back to generic at {response.url}")
            yield from super().parse_staff_directory(response)

    def handle_error(self, failure):
        logger.error(f"PrestoSports request failed: {failure.request.url} — {failure.value}")
