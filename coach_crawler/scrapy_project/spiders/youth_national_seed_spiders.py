"""Seed discovery spiders for national youth sports organization directories.

Each spider targets a specific national governing body's public club/league
finder to discover affiliated youth organizations across the US.
"""

import json
import scrapy
import logging
from urllib.parse import quote

from coach_crawler.scrapy_project.spiders.base_seed_spider import BaseSeedSpider

logger = logging.getLogger(__name__)


class USAFootballSeedSpider(BaseSeedSpider):
    """Discover youth football programs from USA Football's directory.

    USA Football (usafootball.com) is the national governing body for
    amateur football, with ~6,000+ affiliated programs.
    """

    name = "usa_football_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.usafootball.com/programs/find-a-program?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        programs = response.css(
            ".program-card, .result-item, .organization-card, "
            "[class*='program'], [class*='result'], [class*='team'], "
            ".card, article, table tbody tr"
        )

        for program in programs:
            name = program.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, [class*='title']::text, "
                "td:first-child::text, strong::text"
            ).get("").strip()
            city = program.css(
                "[class*='city']::text, [class*='location']::text, "
                "td.city::text, .address::text"
            ).get("").strip()
            link = program.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="rec_league",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="usa_football",
            )
            if item is None:
                return
            yield item

        # Pagination
        next_page = response.css("a.next::attr(href), a[rel='next']::attr(href)").get()
        if next_page:
            yield self.make_playwright_request(
                response.urljoin(next_page),
                callback=self.parse_directory,
                errback=self.handle_error,
                meta=response.meta,
            )


class USSSASeedSpider(BaseSeedSpider):
    """Discover teams from the USSSA (United States Specialty Sports Association).

    USSSA (usssa.com) covers baseball, softball, basketball, and more
    with ~5,000+ affiliated organizations.
    """

    name = "usssa_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    USSSA_SPORTS = ["baseball", "softball", "basketball", "soccer", "football"]

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for sport in self.USSSA_SPORTS:
            for state_code in states:
                url = f"https://www.usssa.com/{sport}/teams?state={state_code}"
                yield self.make_playwright_request(
                    url,
                    callback=self.parse_directory,
                    errback=self.handle_error,
                    meta={"state": state_code, "sport": sport},
                )

    def parse_directory(self, response):
        state = response.meta["state"]
        teams = response.css(
            ".team-card, .team-item, .result-item, "
            "[class*='team'], [class*='result'], [class*='organization'], "
            "table tbody tr, .card, article"
        )

        for team in teams:
            name = team.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, [class*='title']::text, "
                "td:first-child::text, strong::text"
            ).get("").strip()
            city = team.css(
                "[class*='city']::text, [class*='location']::text"
            ).get("").strip()
            link = team.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="travel_team",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="usssa",
            )
            if item is None:
                return
            yield item

        next_page = response.css("a.next::attr(href), a[rel='next']::attr(href)").get()
        if next_page:
            yield self.make_playwright_request(
                response.urljoin(next_page),
                callback=self.parse_directory,
                errback=self.handle_error,
                meta=response.meta,
            )


class BabeRuthSeedSpider(BaseSeedSpider):
    """Discover leagues from Babe Ruth League / Cal Ripken Baseball.

    Babe Ruth League (baberuthleague.org) covers Babe Ruth Baseball,
    Cal Ripken Baseball, and Babe Ruth Softball — ~8,500 leagues total.
    """

    name = "babe_ruth_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            # Try the league finder
            url = f"https://www.baberuthleague.org/league-finder?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        leagues = response.css(
            ".league-item, .league-card, .result-item, "
            "[class*='league'], [class*='result'], "
            "table tbody tr, .card, article"
        )

        for league in leagues:
            name = league.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, [class*='title']::text, "
                "td:first-child::text, strong::text"
            ).get("").strip()
            city = league.css(
                "[class*='city']::text, [class*='location']::text"
            ).get("").strip()
            link = league.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="rec_league",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="babe_ruth",
            )
            if item is None:
                return
            yield item


class USYouthSoccerSeedSpider(BaseSeedSpider):
    """Discover clubs from US Youth Soccer state associations.

    US Youth Soccer (usyouthsoccer.org) has 55 state associations
    with ~3,000+ affiliated clubs.
    """

    name = "us_youth_soccer_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        # US Youth Soccer has state associations — start from main directory
        url = "https://www.usyouthsoccer.org/state-associations/"
        yield self.make_playwright_request(
            url,
            callback=self.parse_state_list,
            errback=self.handle_error,
        )

    def parse_state_list(self, response):
        """Find links to individual state association pages."""
        for link in response.css("a"):
            href = link.attrib.get("href", "")
            text = link.css("::text").get("").strip()
            if not href or not text:
                continue
            # Look for state names or state association links
            for state_code in self.US_STATES:
                if self.state and state_code != self.state:
                    continue
                if state_code.lower() in href.lower() or state_code.lower() in text.lower():
                    yield self.make_playwright_request(
                        response.urljoin(href),
                        callback=self.parse_state_clubs,
                        errback=self.handle_error,
                        meta={"state": state_code},
                    )
                    break

    def parse_state_clubs(self, response):
        state = response.meta["state"]
        clubs = response.css(
            ".club-item, .organization-item, .member-club, "
            "[class*='club'], [class*='member'], [class*='organization'], "
            "table tbody tr, .card, article, li"
        )

        for club in clubs:
            name = club.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, strong::text, "
                "td:first-child::text"
            ).get("").strip()
            city = club.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = club.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="club_team",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="club_team",
            )
            if item is None:
                return
            yield item


class USAHockeySeedSpider(BaseSeedSpider):
    """Discover programs from USA Hockey's association directory.

    USA Hockey (usahockey.com) has ~2,500 affiliated programs.
    """

    name = "usa_hockey_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.usahockey.com/associationdirectory?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        programs = response.css(
            ".association-item, .program-item, .result-item, "
            "[class*='association'], [class*='program'], [class*='result'], "
            "table tbody tr, .card, article"
        )

        for prog in programs:
            name = prog.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, td:first-child::text, strong::text"
            ).get("").strip()
            city = prog.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = prog.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="club_team",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="club_team",
            )
            if item is None:
                return
            yield item


class USAWrestlingSeedSpider(BaseSeedSpider):
    """Discover clubs from USA Wrestling's club finder.

    USA Wrestling (usawrestling.org) has ~3,000 affiliated clubs.
    """

    name = "usa_wrestling_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.usawrestling.org/clubs?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        clubs = response.css(
            ".club-item, .club-card, .result-item, "
            "[class*='club'], [class*='result'], "
            "table tbody tr, .card, article"
        )

        for club in clubs:
            name = club.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, td:first-child::text, strong::text"
            ).get("").strip()
            city = club.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = club.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="club_team",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="club_team",
            )
            if item is None:
                return
            yield item


class USLacrosseSeedSpider(BaseSeedSpider):
    """Discover clubs from US Lacrosse club finder.

    US Lacrosse (uslacrosse.org) has ~3,000 affiliated clubs.
    """

    name = "us_lacrosse_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.uslacrosse.org/find-a-club?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        clubs = response.css(
            ".club-item, .club-card, .result-item, "
            "[class*='club'], [class*='result'], "
            "table tbody tr, .card, article"
        )

        for club in clubs:
            name = club.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, td:first-child::text, strong::text"
            ).get("").strip()
            city = club.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = club.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="club_team",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="club_team",
            )
            if item is None:
                return
            yield item


class PONYBaseballSeedSpider(BaseSeedSpider):
    """Discover leagues from PONY Baseball/Softball.

    PONY (pony.org) has ~2,000 affiliated leagues.
    """

    name = "pony_baseball_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.pony.org/league-locator?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        leagues = response.css(
            ".league-item, .league-card, .result-item, "
            "[class*='league'], [class*='result'], "
            "table tbody tr, .card, article"
        )

        for league in leagues:
            name = league.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, td:first-child::text, strong::text"
            ).get("").strip()
            city = league.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = league.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="rec_league",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="pony_baseball",
            )
            if item is None:
                return
            yield item


class AYSOSeedSpider(BaseSeedSpider):
    """Discover regions from the American Youth Soccer Organization.

    AYSO (ayso.org) has ~900 regions across the US.
    """

    name = "ayso_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        url = "https://www.ayso.org/find-a-region/"
        yield self.make_playwright_request(
            url,
            callback=self.parse_directory,
            errback=self.handle_error,
        )

    def parse_directory(self, response):
        regions = response.css(
            ".region-item, .region-card, .result-item, "
            "[class*='region'], [class*='result'], "
            "table tbody tr, .card, article, li"
        )

        for region in regions:
            name = region.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, td:first-child::text, strong::text"
            ).get("").strip()
            # Try to extract state from text
            all_text = " ".join(region.css("*::text").getall())
            state = ""
            for code in self.US_STATES:
                if f" {code} " in all_text or all_text.endswith(f" {code}"):
                    state = code
                    break
            city = region.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = region.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue
            if self.state and state and state != self.state:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="rec_league",
                state=state or self.state or "",
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="ayso",
            )
            if item is None:
                return
            yield item


class I9SportsSeedSpider(BaseSeedSpider):
    """Discover franchise locations from i9 Sports.

    i9 Sports (i9sports.com) is a multi-sport youth franchise
    with ~1,000 locations.
    """

    name = "i9_sports_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        url = "https://www.i9sports.com/Programs/FindAProgram"
        yield self.make_playwright_request(
            url,
            callback=self.parse_directory,
            errback=self.handle_error,
        )

    def parse_directory(self, response):
        locations = response.css(
            ".location-card, .program-card, .result-item, "
            "[class*='location'], [class*='program'], [class*='result'], "
            ".card, article, table tbody tr"
        )

        for loc in locations:
            name = loc.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, [class*='title']::text, strong::text"
            ).get("").strip()
            all_text = " ".join(loc.css("*::text").getall())
            state = ""
            for code in self.US_STATES:
                if f" {code} " in all_text or all_text.endswith(f" {code}") or f", {code}" in all_text:
                    state = code
                    break
            city = loc.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = loc.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue
            if self.state and state and state != self.state:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="rec_league",
                state=state or self.state or "",
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="i9_sports",
            )
            if item is None:
                return
            yield item


class UpwardSportsSeedSpider(BaseSeedSpider):
    """Discover church-based locations from Upward Sports.

    Upward Sports (upward.org) runs youth sports programs at ~3,000 churches.
    """

    name = "upward_sports_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.upward.org/find-a-league?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        leagues = response.css(
            ".league-card, .league-item, .result-item, "
            "[class*='league'], [class*='result'], [class*='church'], "
            ".card, article, table tbody tr"
        )

        for league in leagues:
            name = league.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, [class*='title']::text, strong::text"
            ).get("").strip()
            city = league.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = league.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="rec_league",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="upward_sports",
            )
            if item is None:
                return
            yield item


class USAVolleyballSeedSpider(BaseSeedSpider):
    """Discover clubs from USA Volleyball's region/club directory.

    USA Volleyball (usavolleyball.org) has ~1,500 affiliated clubs.
    """

    name = "usa_volleyball_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.usavolleyball.org/membership/find-a-club?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        clubs = response.css(
            ".club-item, .club-card, .result-item, "
            "[class*='club'], [class*='result'], "
            "table tbody tr, .card, article"
        )

        for club in clubs:
            name = club.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, td:first-child::text, strong::text"
            ).get("").strip()
            city = club.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = club.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="club_team",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="club_team",
            )
            if item is None:
                return
            yield item


class USATFSeedSpider(BaseSeedSpider):
    """Discover clubs from USA Track & Field's club search.

    USATF (usatf.org) has ~2,500 affiliated clubs.
    """

    name = "usatf_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.usatf.org/clubs/search?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        clubs = response.css(
            ".club-item, .club-card, .result-item, "
            "[class*='club'], [class*='result'], "
            "table tbody tr, .card, article"
        )

        for club in clubs:
            name = club.css(
                "h2::text, h3::text, h4::text, a::text, "
                "[class*='name']::text, td:first-child::text, strong::text"
            ).get("").strip()
            city = club.css("[class*='city']::text, [class*='location']::text").get("").strip()
            link = club.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="club_team",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="club_team",
            )
            if item is None:
                return
            yield item
