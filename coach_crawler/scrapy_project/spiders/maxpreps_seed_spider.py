import re
import scrapy
import logging

from coach_crawler.scrapy_project.spiders.base_seed_spider import BaseSeedSpider

logger = logging.getLogger(__name__)

# All 50 US states + DC
US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
    "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
    "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]


class MaxPrepsSeedSpider(BaseSeedSpider):
    """Discover high schools from MaxPreps school listings by state.

    MaxPreps URL pattern: https://www.maxpreps.com/{state_abbrev}/schools/
    School entries are <a> tags with href like /tx/city-slug/school-slug/
    containing <strong>School Name</strong> and "City, ST" text.
    """

    name = "maxpreps_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 5.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def start_requests(self):
        states = [self.state] if self.state else US_STATES

        for state_code in states:
            # MaxPreps uses 2-letter lowercase state codes in URL
            url = f"https://www.maxpreps.com/{state_code.lower()}/schools/"
            yield scrapy.Request(
                url,
                callback=self.parse_state_page,
                meta={"state": state_code},
                errback=self.handle_error,
            )

    def parse_state_page(self, response):
        """Parse the state school listing page.

        Structure: <a href="/tx/city-slug/school-slug/">
                     <img ...>
                     <div><strong>School Name</strong></div>
                     <div>City, TX</div>
                   </a>
        """
        state = response.meta["state"]
        state_lower = state.lower()

        # Match school links: href pattern /{state}/{city}/{school}/
        for link in response.css(f"a[href^='/{state_lower}/']"):
            href = link.attrib.get("href", "")

            # School pages have 3 path segments: /tx/city/school/
            parts = [p for p in href.strip("/").split("/") if p]
            if len(parts) != 3:
                continue

            # Get school name from <strong> or first text div
            name = link.css("strong::text").get("")
            if not name:
                name = link.css("div::text").get("")
            name = name.strip()

            if not name or len(name) < 3:
                continue

            # Get city from the "City, ST" text
            city = None
            texts = link.css("div::text").getall()
            for t in texts:
                t = t.strip()
                if "," in t and len(t) > 3:
                    city = t.split(",")[0].strip()
                    break

            athletics_url = response.urljoin(href)

            item = self.make_school_item(
                name=name,
                level="high_school",
                sub_level="high_school",
                state=state,
                city=city,
                athletics_url=athletics_url,
            )
            if item is None:
                return
            yield item

        # Follow pagination
        next_page = response.css("a[rel='next']::attr(href), a.next::attr(href)").get()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse_state_page,
                meta=response.meta,
                errback=self.handle_error,
            )

    def handle_error(self, failure):
        logger.error(f"MaxPreps request failed: {failure.request.url} — {failure.value}")
