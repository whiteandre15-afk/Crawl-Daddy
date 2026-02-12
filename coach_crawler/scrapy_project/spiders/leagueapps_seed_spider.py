"""LeagueApps platform seed spider.

LeagueApps (leagueapps.com) is a major youth sports management platform
used by thousands of leagues and clubs. Discovers organizations from
their public directory.
"""

import json
import scrapy
import logging
from urllib.parse import quote

from coach_crawler.scrapy_project.spiders.base_seed_spider import BaseSeedSpider

logger = logging.getLogger(__name__)

# Sports commonly managed on LeagueApps
LA_SPORTS = [
    "baseball", "basketball", "football", "soccer", "softball",
    "volleyball", "lacrosse", "hockey", "swimming", "wrestling",
    "tennis", "track-field", "gymnastics", "cheerleading",
]


class LeagueAppsSeedSpider(BaseSeedSpider):
    """Discover youth organizations from the LeagueApps directory.

    Uses the LeagueApps public site directory and search endpoints
    to find organizations by sport and location.
    """

    name = "leagueapps_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    # Common search terms to find LeagueApps-hosted orgs
    SEARCH_TERMS = [
        "youth baseball league", "youth soccer club", "youth basketball league",
        "youth football league", "travel baseball", "travel soccer",
        "rec league", "little league", "youth softball",
        "youth lacrosse club", "youth hockey",
    ]

    def start_requests(self):
        # Strategy 1: Browse LeagueApps directory pages by sport
        states = [self.state] if self.state else self.US_STATES
        for sport in LA_SPORTS:
            for state_code in states:
                url = f"https://www.leagueapps.com/leagues/{sport}?state={state_code}"
                yield self.make_playwright_request(
                    url,
                    callback=self.parse_directory,
                    errback=self.handle_error,
                    meta={"state": state_code, "sport": sport},
                )

        # Strategy 2: Search the LeagueApps site directory
        for state_code in states:
            url = f"https://www.leagueapps.com/leagues?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code, "sport": "all"},
            )

    def parse_directory(self, response):
        state = response.meta["state"]

        # Look for organization cards/listings
        orgs = response.css(
            ".league-card, .organization-card, .result-card, "
            "[class*='league'], [class*='organization'], [class*='result'], "
            ".card, article, .listing"
        )

        for org in orgs:
            name = org.css(
                "h2::text, h3::text, h4::text, "
                "[class*='name']::text, [class*='title']::text, "
                "a::text, strong::text"
            ).get("").strip()
            city = org.css(
                "[class*='city']::text, [class*='location']::text, "
                ".address::text, [class*='address']::text"
            ).get("").strip()
            link = org.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level=self._classify_sub_level(name),
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="leagueapps_org",
            )
            if item is None:
                return
            yield item

        # Follow pagination
        next_page = response.css(
            "a.next::attr(href), a[rel='next']::attr(href), "
            "[class*='next'] a::attr(href), .pagination a:last-child::attr(href)"
        ).get()
        if next_page:
            yield self.make_playwright_request(
                response.urljoin(next_page),
                callback=self.parse_directory,
                errback=self.handle_error,
                meta=response.meta,
            )

    def _classify_sub_level(self, name: str) -> str:
        name_lower = name.lower()
        if any(w in name_lower for w in ["club", "select", "premier", "elite", "travel"]):
            return "club_team"
        if any(w in name_lower for w in ["rec", "recreation", "parks", "community"]):
            return "rec_league"
        if any(w in name_lower for w in ["academy", "training"]):
            return "academy"
        return "other"
