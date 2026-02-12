import scrapy
import logging

from coach_crawler.scrapy_project.spiders.base_seed_spider import BaseSeedSpider

logger = logging.getLogger(__name__)

# State athletic association directories — starting with the 10 largest states.
# Each entry maps a state code to its association's school directory URL and
# CSS selectors for extracting school data. Expand this dict as new states
# are reverse-engineered.
STATE_CONFIGS = {
    "TX": {
        "name": "UIL",
        "url": "https://www.uiltexas.org/athletics/schools",
        "school_selector": "table.schools tr, .school-list li, .school-item",
        "name_selector": "td:first-child a::text, a.school-name::text, .school-name::text",
        "city_selector": "td:nth-child(2)::text, .school-city::text",
        "link_selector": "td:first-child a::attr(href), a.school-name::attr(href)",
    },
    "CA": {
        "name": "CIF",
        "url": "https://www.cifstate.org/member_schools/index",
        "school_selector": "table tr, .school-list li, .school-item",
        "name_selector": "td:first-child a::text, a::text, .school-name::text",
        "city_selector": "td:nth-child(2)::text, .city::text",
        "link_selector": "td:first-child a::attr(href), a::attr(href)",
    },
    "FL": {
        "name": "FHSAA",
        "url": "https://www.fhsaa.org/schools",
        "school_selector": "table tr, .school-list li",
        "name_selector": "td:first-child::text, a::text",
        "city_selector": "td:nth-child(2)::text",
        "link_selector": "a::attr(href)",
    },
    "NY": {
        "name": "NYSPHSAA",
        "url": "https://www.nysphsaa.org/Schools",
        "school_selector": "table tr, .school-list li",
        "name_selector": "td:first-child::text, a::text",
        "city_selector": "td:nth-child(2)::text",
        "link_selector": "a::attr(href)",
    },
    "PA": {
        "name": "PIAA",
        "url": "https://www.piaa.org/schools/directory.aspx",
        "school_selector": "table tr, .school-row",
        "name_selector": "td:first-child a::text, .school-name::text",
        "city_selector": "td:nth-child(2)::text",
        "link_selector": "td:first-child a::attr(href)",
    },
    "OH": {
        "name": "OHSAA",
        "url": "https://www.ohsaa.org/School-Directory",
        "school_selector": "table tr, .school-list li",
        "name_selector": "td:first-child a::text, a::text",
        "city_selector": "td:nth-child(2)::text",
        "link_selector": "td:first-child a::attr(href)",
    },
    "IL": {
        "name": "IHSA",
        "url": "https://www.ihsa.org/Schools-Facilities/School-Directory",
        "school_selector": "table tr, .school-directory li",
        "name_selector": "td:first-child a::text, a::text",
        "city_selector": "td:nth-child(2)::text",
        "link_selector": "td:first-child a::attr(href)",
    },
    "GA": {
        "name": "GHSA",
        "url": "https://www.ghsa.net/member-schools",
        "school_selector": "table tr, .views-row",
        "name_selector": "td:first-child a::text, .views-field-title a::text",
        "city_selector": "td:nth-child(2)::text, .views-field-city::text",
        "link_selector": "td:first-child a::attr(href), .views-field-title a::attr(href)",
    },
    "NC": {
        "name": "NCHSAA",
        "url": "https://www.nchsaa.org/member-schools",
        "school_selector": "table tr, .school-list li",
        "name_selector": "td:first-child a::text, a::text",
        "city_selector": "td:nth-child(2)::text",
        "link_selector": "td:first-child a::attr(href)",
    },
    "MI": {
        "name": "MHSAA",
        "url": "https://www.mhsaa.com/Schools",
        "school_selector": "table tr, .school-list li",
        "name_selector": "td:first-child a::text, a::text",
        "city_selector": "td:nth-child(2)::text",
        "link_selector": "td:first-child a::attr(href)",
    },
}


class StateAthleticAssocSeedSpider(BaseSeedSpider):
    """Discover high schools from state athletic association member directories.

    Each state has its own athletic association with different site structures.
    Uses configurable selectors per state to handle the diversity.
    """

    name = "state_athletic_assoc_seed"

    def start_requests(self):
        if self.state:
            states = {self.state: STATE_CONFIGS.get(self.state)}
            if not states[self.state]:
                logger.warning(f"No config for state {self.state}. Available: {list(STATE_CONFIGS.keys())}")
                return
        else:
            states = STATE_CONFIGS

        for state_code, config in states.items():
            if not config:
                continue
            yield scrapy.Request(
                config["url"],
                callback=self.parse_directory,
                meta={"state": state_code, "config": config},
                errback=self.handle_error,
            )

    def parse_directory(self, response):
        """Parse a state athletic association member directory."""
        state = response.meta["state"]
        config = response.meta["config"]

        school_els = response.css(config["school_selector"])
        logger.info(f"{config['name']}: Found {len(school_els)} potential school rows for {state}")

        for el in school_els:
            name = el.css(config["name_selector"]).get("").strip()
            if not name or len(name) < 3:
                continue

            city = el.css(config["city_selector"]).get("").strip() if config.get("city_selector") else None
            link = el.css(config["link_selector"]).get() if config.get("link_selector") else None

            athletics_url = response.urljoin(link) if link else None

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

        # Follow pagination if present
        next_page = response.css(
            "a[rel='next']::attr(href), a.pager-next::attr(href), "
            "li.next a::attr(href), .pagination a.next::attr(href)"
        ).get()
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse_directory,
                meta=response.meta,
                errback=self.handle_error,
            )

    def handle_error(self, failure):
        logger.error(f"State athletic assoc request failed: {failure.request.url} — {failure.value}")
