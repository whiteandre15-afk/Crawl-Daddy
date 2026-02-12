"""SportsEngine platform seed spider.

SportsEngine (sportsengine.com) hosts 35,000+ youth sports organizations.
Uses the SportsEngine organization suggest API and the SportsEngine Play
directory to discover organizations.
"""

import json
import scrapy
import logging
from urllib.parse import quote

from coach_crawler.scrapy_project.spiders.base_seed_spider import BaseSeedSpider

logger = logging.getLogger(__name__)

# Sports available on SportsEngine Play directory
SE_SPORTS = [
    "baseball", "basketball", "cheerleading", "football", "gymnastics",
    "hockey", "lacrosse", "soccer", "softball", "swimming",
    "tennis", "track-and-field", "volleyball", "wrestling",
]


class SportsEngineSeedSpider(BaseSeedSpider):
    """Discover youth sports organizations from SportsEngine's directory.

    Two strategies:
    1. Organization suggest API: search by common youth org name patterns
    2. SportsEngine Play directory: browse sport-specific pages by location
    """

    name = "sportsengine_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    # Organization suggest API endpoint (discovered from find-your-org page)
    SUGGEST_API = "https://www.sportsengine.com/portal/api/v1/organizations/suggest"

    # Common search terms for youth orgs
    SEARCH_TERMS = [
        "youth baseball", "youth football", "youth soccer", "youth basketball",
        "little league", "rec league", "youth hockey", "youth lacrosse",
        "travel baseball", "travel soccer", "travel basketball",
        "youth softball", "youth volleyball", "youth wrestling",
        "club soccer", "club baseball", "club basketball",
        "select baseball", "select soccer", "select basketball",
        "pee wee football", "flag football", "tee ball",
        "youth swim", "youth track", "youth tennis",
        "sports association", "athletic association",
        "recreation", "parks and rec",
    ]

    def start_requests(self):
        # Strategy 1: Search the organization suggest API with many terms
        for term in self.SEARCH_TERMS:
            url = f"{self.SUGGEST_API}?name={quote(term)}"
            yield scrapy.Request(
                url,
                callback=self.parse_suggest_response,
                errback=self.handle_error,
                meta={"search_term": term},
                headers={"Accept": "application/json"},
            )

        # Strategy 2: Browse the SportsEngine Play directory by sport + state
        states = [self.state] if self.state else self.US_STATES
        for sport in SE_SPORTS:
            for state_code in states:
                url = f"https://discover.sportsengineplay.com/{sport}/?location={state_code}"
                yield self.make_playwright_request(
                    url,
                    callback=self.parse_play_directory,
                    errback=self.handle_error,
                    meta={"state": state_code, "sport": sport},
                )

    def parse_suggest_response(self, response):
        """Parse the organization suggest API response."""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            logger.warning(f"SportsEngine: invalid JSON from suggest API")
            return

        orgs = data if isinstance(data, list) else data.get("organizations", data.get("results", []))
        for org in orgs:
            if not isinstance(org, dict):
                continue

            name = org.get("name", "").strip()
            state = org.get("state", "").strip()
            city = org.get("city", "").strip()
            org_url = org.get("url") or org.get("website") or ""
            claimed = org.get("claimed", False)

            if not name or len(name) < 3:
                continue
            if self.state and state and state != self.state:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level=self._classify_sub_level(name),
                state=state,
                city=city,
                athletics_url=org_url if org_url.startswith("http") else None,
                organization_type="sportsengine_org",
            )
            if item is None:
                return
            yield item

    def parse_play_directory(self, response):
        """Parse the SportsEngine Play sport directory page."""
        state = response.meta["state"]
        listings = response.css(
            ".program-card, .listing-card, .result-card, "
            "[class*='program'], [class*='listing'], [class*='result'], "
            ".card, article, .organization"
        )

        for listing in listings:
            name = listing.css(
                "h2::text, h3::text, h4::text, "
                "[class*='name']::text, [class*='title']::text, "
                "a::text, strong::text"
            ).get("").strip()
            city = listing.css(
                "[class*='city']::text, [class*='location']::text, "
                ".address::text"
            ).get("").strip()
            link = listing.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level=self._classify_sub_level(name),
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="sportsengine_org",
            )
            if item is None:
                return
            yield item

    def _classify_sub_level(self, name: str) -> str:
        name_lower = name.lower()
        if any(w in name_lower for w in ["club", "select", "premier", "elite", "travel"]):
            return "club_team"
        if any(w in name_lower for w in ["rec", "recreation", "parks", "community"]):
            return "rec_league"
        if any(w in name_lower for w in ["academy", "training"]):
            return "academy"
        if any(w in name_lower for w in ["camp", "clinic"]):
            return "camp"
        if "ymca" in name_lower or "y " in name_lower:
            return "ymca"
        return "other"
