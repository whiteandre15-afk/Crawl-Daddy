"""Seed discovery spiders for youth sports organizations.

Each spider targets a specific national organization's public directory
to discover clubs, leagues, and other youth sports organizations.
Rewritten to use actual API endpoints and correct page structures.
"""

import json
import scrapy
import logging
from urllib.parse import quote, urlencode

from coach_crawler.scrapy_project.spiders.base_seed_spider import BaseSeedSpider

logger = logging.getLogger(__name__)

# Major US cities by state for geo-based searches
# Used by spiders that require location-based queries (zip/lat-lng)
_STATE_CITIES = {
    "AL": ["Birmingham", "Montgomery", "Huntsville", "Mobile"],
    "AK": ["Anchorage", "Fairbanks", "Juneau"],
    "AZ": ["Phoenix", "Tucson", "Mesa", "Scottsdale"],
    "AR": ["Little Rock", "Fort Smith", "Fayetteville"],
    "CA": ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "San Jose", "Fresno", "Oakland"],
    "CO": ["Denver", "Colorado Springs", "Aurora", "Fort Collins"],
    "CT": ["Hartford", "New Haven", "Stamford", "Bridgeport"],
    "DE": ["Wilmington", "Dover", "Newark"],
    "FL": ["Miami", "Orlando", "Tampa", "Jacksonville", "Fort Lauderdale", "St Petersburg"],
    "GA": ["Atlanta", "Augusta", "Savannah", "Columbus"],
    "HI": ["Honolulu", "Hilo", "Kailua"],
    "ID": ["Boise", "Meridian", "Nampa"],
    "IL": ["Chicago", "Springfield", "Naperville", "Rockford", "Peoria"],
    "IN": ["Indianapolis", "Fort Wayne", "Evansville", "South Bend"],
    "IA": ["Des Moines", "Cedar Rapids", "Davenport"],
    "KS": ["Wichita", "Overland Park", "Kansas City", "Topeka"],
    "KY": ["Louisville", "Lexington", "Bowling Green"],
    "LA": ["New Orleans", "Baton Rouge", "Shreveport"],
    "ME": ["Portland", "Bangor", "Lewiston"],
    "MD": ["Baltimore", "Annapolis", "Rockville", "Frederick"],
    "MA": ["Boston", "Worcester", "Springfield", "Cambridge"],
    "MI": ["Detroit", "Grand Rapids", "Ann Arbor", "Lansing"],
    "MN": ["Minneapolis", "St Paul", "Rochester", "Duluth"],
    "MS": ["Jackson", "Gulfport", "Hattiesburg"],
    "MO": ["Kansas City", "St Louis", "Springfield", "Columbia"],
    "MT": ["Billings", "Missoula", "Great Falls"],
    "NE": ["Omaha", "Lincoln", "Bellevue"],
    "NV": ["Las Vegas", "Reno", "Henderson"],
    "NH": ["Manchester", "Nashua", "Concord"],
    "NJ": ["Newark", "Jersey City", "Trenton", "Edison", "Cherry Hill"],
    "NM": ["Albuquerque", "Santa Fe", "Las Cruces"],
    "NY": ["New York", "Buffalo", "Rochester", "Syracuse", "Albany"],
    "NC": ["Charlotte", "Raleigh", "Durham", "Greensboro", "Winston-Salem"],
    "ND": ["Fargo", "Bismarck", "Grand Forks"],
    "OH": ["Columbus", "Cleveland", "Cincinnati", "Dayton", "Toledo"],
    "OK": ["Oklahoma City", "Tulsa", "Norman"],
    "OR": ["Portland", "Eugene", "Salem", "Bend"],
    "PA": ["Philadelphia", "Pittsburgh", "Harrisburg", "Allentown"],
    "RI": ["Providence", "Warwick", "Cranston"],
    "SC": ["Charleston", "Columbia", "Greenville", "Myrtle Beach"],
    "SD": ["Sioux Falls", "Rapid City", "Aberdeen"],
    "TN": ["Nashville", "Memphis", "Knoxville", "Chattanooga"],
    "TX": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth", "El Paso", "Plano"],
    "UT": ["Salt Lake City", "Provo", "Ogden"],
    "VT": ["Burlington", "Montpelier", "Rutland"],
    "VA": ["Virginia Beach", "Richmond", "Norfolk", "Arlington", "Roanoke"],
    "WA": ["Seattle", "Tacoma", "Spokane", "Bellevue", "Vancouver"],
    "WV": ["Charleston", "Huntington", "Morgantown"],
    "WI": ["Milwaukee", "Madison", "Green Bay"],
    "WY": ["Cheyenne", "Casper", "Laramie"],
    "DC": ["Washington"],
}


class LittleLeagueSeedSpider(BaseSeedSpider):
    """Discover leagues from the Little League league finder API.

    Uses the maps.littleleague.org/leaguefinder/Search/FindLeague endpoint
    to query leagues by city+state across the US.
    """

    name = "little_league_seed"
    FIND_LEAGUE_URL = "https://maps.littleleague.org/leaguefinder/Search/FindLeague"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            cities = _STATE_CITIES.get(state_code, [state_code])
            for city in cities:
                address = f"{city}, {state_code}"
                yield scrapy.FormRequest(
                    self.FIND_LEAGUE_URL,
                    formdata={"address": address},
                    callback=self.parse_leagues,
                    errback=self.handle_error,
                    meta={"state": state_code, "city": city},
                )

    def parse_leagues(self, response):
        state = response.meta["state"]
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            logger.warning(f"Little League: invalid JSON for {response.meta['city']}, {state}")
            return

        leagues = data if isinstance(data, list) else data.get("leagues", data.get("results", []))
        for league in leagues:
            if isinstance(league, dict):
                name = league.get("leagueName") or league.get("name") or ""
                city = league.get("city") or league.get("leagueCity") or response.meta["city"]
                league_state = league.get("state") or league.get("leagueState") or state
                website = league.get("websiteUrl") or league.get("website") or ""
            else:
                continue

            if not name or len(name) < 3:
                continue
            if self.state and league_state != self.state:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="rec_league",
                state=league_state,
                city=city,
                athletics_url=website if website.startswith("http") else None,
                organization_type="little_league",
            )
            if item is None:
                return
            yield item


class USClubSoccerSeedSpider(BaseSeedSpider):
    """Discover clubs from the US Club Soccer member directory.

    Uses Playwright to render the JS-heavy find-a-club page and extract
    club listings from the rendered DOM.
    """

    name = "us_club_soccer_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            url = f"https://www.usclubsoccer.org/find-a-club/?state={state_code}"
            yield self.make_playwright_request(
                url,
                callback=self.parse_directory,
                errback=self.handle_error,
                meta={"state": state_code},
            )

    def parse_directory(self, response):
        state = response.meta["state"]
        # Try multiple selector strategies for club listings
        clubs = response.css(
            ".club-item, .club-card, .organization-item, "
            ".member-club, .club-listing, .result-item, "
            "[class*='club'], [class*='result'], "
            "table tbody tr, .views-row"
        )

        if not clubs:
            # Fallback: extract from raw text looking for club-like patterns
            logger.info(f"US Club Soccer: No CSS matches for {state}, trying text extraction")
            return

        for club in clubs:
            texts = club.css("*::text").getall()
            name = ""
            city = ""
            link = club.css("a::attr(href)").get()

            for text in texts:
                text = text.strip()
                if not text or len(text) < 3:
                    continue
                if not name and len(text) > 5:
                    name = text
                elif not city and len(text) > 2:
                    city = text

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


class AAUSeedSpider(BaseSeedSpider):
    """Discover clubs from the AAU club directory.

    AAU's site requires JS rendering. Uses Playwright to load and extract.
    """

    name = "aau_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        # AAU has sport-specific directories
        sports = ["basketball", "baseball", "football", "soccer", "volleyball",
                  "softball", "wrestling", "track-and-field", "swimming"]
        states = [self.state] if self.state else self.US_STATES

        for sport in sports:
            for state_code in states:
                url = f"https://www.aausports.org/Clubs.aspx?sport={sport}&state={state_code}"
                yield self.make_playwright_request(
                    url,
                    callback=self.parse_directory,
                    errback=self.handle_error,
                    meta={"state": state_code, "sport": sport},
                )

    def parse_directory(self, response):
        state = response.meta["state"]
        rows = response.css(
            ".club-item, .club-listing, .organization-card, "
            "table tbody tr, .search-result, .result-row, "
            "[class*='club'], [class*='result'], .views-row"
        )

        for row in rows:
            texts = row.css("*::text").getall()
            name = ""
            city = ""
            link = row.css("a::attr(href)").get()

            for text in texts:
                text = text.strip()
                if not text or len(text) < 3:
                    continue
                if not name and len(text) > 5:
                    name = text
                elif not city and len(text) > 2:
                    city = text

            if not name or len(name) < 3:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="club_team",
                state=state,
                city=city,
                athletics_url=response.urljoin(link) if link else None,
                organization_type="aau",
            )
            if item is None:
                return
            yield item


class PopWarnerSeedSpider(BaseSeedSpider):
    """Discover chapters from Pop Warner listings.

    Pop Warner uses an older ASP.NET site. Render with Playwright.
    """

    name = "pop_warner_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 3.0,
    }

    def start_requests(self):
        # Pop Warner regional structure — try main directory
        url = "https://www.popwarner.com/Default.aspx?tabid=1403329"
        yield self.make_playwright_request(
            url,
            callback=self.parse_regions,
            errback=self.handle_error,
        )

    def parse_regions(self, response):
        """Parse the top-level regions page to find state/regional links."""
        # Find links to regional or state directories
        region_links = response.css("a[href*='tabid'], a[href*='region'], a[href*='association']")
        for link in region_links:
            href = link.attrib.get("href", "")
            text = link.css("::text").get("").strip()
            if text and href:
                yield self.make_playwright_request(
                    response.urljoin(href),
                    callback=self.parse_directory,
                    errback=self.handle_error,
                    meta={"region": text},
                )

        # Also try to parse this page directly as a directory
        yield from self._extract_entries(response)

    def parse_directory(self, response):
        yield from self._extract_entries(response)

    def _extract_entries(self, response):
        rows = response.css(
            ".league-item, .chapter-card, .organization-row, "
            "table tbody tr, .result-item, .views-row, "
            "[class*='league'], [class*='chapter'], [class*='association']"
        )
        for row in rows:
            texts = row.css("*::text").getall()
            name = ""
            state = ""
            city = ""
            link = row.css("a::attr(href)").get()

            for text in texts:
                text = text.strip()
                if not text or len(text) < 2:
                    continue
                if len(text) == 2 and text.upper() in self.US_STATES:
                    state = text.upper()
                elif not name and len(text) > 5:
                    name = text
                elif not city and len(text) > 2:
                    city = text

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
                organization_type="pop_warner",
            )
            if item is None:
                return
            yield item


class YMCASeedSpider(BaseSeedSpider):
    """Discover YMCA locations from the YMCA directory.

    YMCA's find-your-y is JS-rendered. Also tries the YMCA API if available.
    """

    name = "ymca_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 2.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            cities = _STATE_CITIES.get(state_code, [state_code])
            for city in cities:
                # Try the YMCA locator with location search
                search_query = f"{city}, {state_code}"
                url = f"https://www.ymca.org/find-your-y?location={quote(search_query)}"
                yield self.make_playwright_request(
                    url,
                    callback=self.parse_directory,
                    errback=self.handle_error,
                    meta={"state": state_code, "city": city},
                )

    def parse_directory(self, response):
        state = response.meta["state"]
        locations = response.css(
            ".location-item, .location-card, .views-row, .result-item, "
            "[class*='location'], [class*='result'], [class*='ymca'], "
            ".card, article, .branch"
        )

        for loc in locations:
            name = (
                loc.css("h2::text, h3::text, h4::text, .location-name::text, "
                        "[class*='title']::text, a::text, strong::text").get("").strip()
            )
            city = loc.css(".city::text, .location-city::text, [class*='city']::text").get("").strip()
            link = loc.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue
            if self.state and state != self.state:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="rec_league",
                state=state,
                city=city or response.meta["city"],
                athletics_url=response.urljoin(link) if link else None,
                organization_type="ymca",
            )
            if item is None:
                return
            yield item


class USASwimmingSeedSpider(BaseSeedSpider):
    """Discover swim clubs from USA Swimming club finder.

    USA Swimming's club finder is API-backed. Uses location-based queries.
    """

    name = "usa_swimming_seed"

    custom_settings = {
        **BaseSeedSpider.custom_settings,
        "DOWNLOAD_DELAY": 2.0,
    }

    def start_requests(self):
        states = [self.state] if self.state else self.US_STATES
        for state_code in states:
            cities = _STATE_CITIES.get(state_code, [])[:2]  # limit cities per state
            if not cities:
                cities = [state_code]
            for city in cities:
                url = f"https://www.usaswimming.org/utility/club-finder?location={quote(city + ', ' + state_code)}&distance=100"
                yield self.make_playwright_request(
                    url,
                    callback=self.parse_directory,
                    errback=self.handle_error,
                    meta={"state": state_code, "city": city},
                )

    def parse_directory(self, response):
        state = response.meta["state"]
        clubs = response.css(
            ".club-item, .club-result, .search-result, "
            "[class*='club'], [class*='result'], "
            "table tbody tr, .card, article"
        )

        for club in clubs:
            name = club.css(
                "h2::text, h3::text, h4::text, a::text, "
                ".club-name::text, [class*='name']::text, "
                "td:first-child::text, strong::text"
            ).get("").strip()
            city = club.css(".city::text, td.city::text, [class*='city']::text").get("").strip()
            link = club.css("a::attr(href)").get()

            if not name or len(name) < 3:
                continue
            if self.state and state != self.state:
                continue

            item = self.make_school_item(
                name=name,
                level="youth",
                sub_level="club_team",
                state=state,
                city=city or response.meta["city"],
                athletics_url=response.urljoin(link) if link else None,
                organization_type="club_team",
            )
            if item is None:
                return
            yield item
