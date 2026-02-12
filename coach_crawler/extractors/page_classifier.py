import re
from urllib.parse import urlparse

# URL path patterns that indicate staff directories
STAFF_URL_PATTERNS = [
    "/staff-directory", "/staff", "/coaches", "/coaching-staff",
    "/athletics/staff", "/about/staff", "/directory",
    "/sports-information/staff", "/athletic-department/staff",
    "/athletic-staff", "/sports/staff", "/athletics-staff",
    # Youth-specific patterns
    "/board-of-directors", "/board", "/our-board", "/leadership",
    "/about-us", "/our-league", "/coaches-and-managers",
    "/league-officers", "/contacts", "/meet-our-team",
    "/volunteer-coaches", "/our-staff",
]

# Link text patterns that lead to staff directories
STAFF_LINK_TEXT_PATTERNS = [
    "staff directory", "coaching staff", "our coaches", "athletic staff",
    "meet the coaches", "staff & coaches", "department staff",
    "coaches & staff", "administration", "staff listing",
    "athletic directory", "coaches directory",
    # Youth-specific patterns
    "board of directors", "board members", "league officers",
    "volunteer coaches", "team managers", "our coaches",
    "league contacts", "meet our team", "league leadership",
    "who we are", "our staff", "contact us",
]

# Keywords on a page that confirm it IS a staff directory
COACHING_TITLE_KEYWORDS = [
    "head coach", "assistant coach", "associate head coach",
    "athletic director", "offensive coordinator", "defensive coordinator",
    "pitching coach", "hitting coach", "goalkeeping coach",
    "director of operations", "director of player development",
    "strength and conditioning", "sports information director",
    # Youth-specific keywords
    "league president", "vice president", "board member",
    "league director", "commissioner", "registrar",
    "team manager", "volunteer coach", "league administrator",
    "treasurer", "secretary", "safety officer",
    "player agent", "coaching coordinator", "program director",
]


class PageClassifier:
    """Heuristics for identifying and finding staff directory pages."""

    def find_staff_directory_links(self, response) -> list[dict]:
        """Given an athletics homepage response, find URLs likely to be staff directories.

        Returns list of {url, score} sorted by score descending.
        """
        candidates = []

        for link in response.css("a"):
            href = link.attrib.get("href", "").strip()
            text = " ".join(link.css("::text").getall()).strip().lower()

            if not href or href.startswith(("#", "javascript:", "mailto:")):
                continue

            score = 0.0

            # Score URL pattern matches
            parsed_path = urlparse(href).path.lower().rstrip("/")
            for pattern in STAFF_URL_PATTERNS:
                if pattern in parsed_path:
                    score += 0.5
                    break

            # Score link text matches
            for pattern in STAFF_LINK_TEXT_PATTERNS:
                if pattern in text:
                    score += 0.4
                    break

            # Boost if both match
            if score >= 0.9:
                score = 1.0

            if score > 0:
                candidates.append({"url": response.urljoin(href), "score": score})

        # Deduplicate by URL and return sorted
        seen = set()
        unique = []
        for c in sorted(candidates, key=lambda x: x["score"], reverse=True):
            if c["url"] not in seen:
                seen.add(c["url"])
                unique.append(c)

        return unique

    def is_staff_directory_page(self, response) -> float:
        """Return confidence 0.0-1.0 that this page IS a staff directory.

        Signals:
        - Multiple coaching title keywords on the page
        - Multiple email addresses
        - Table or list structure with repeated patterns
        """
        page_text = response.text.lower()
        score = 0.0

        # Count coaching title keywords found
        title_hits = sum(1 for kw in COACHING_TITLE_KEYWORDS if kw in page_text)
        if title_hits >= 5:
            score += 0.4
        elif title_hits >= 2:
            score += 0.2

        # Count email addresses on page
        email_count = len(re.findall(r'mailto:', page_text))
        if email_count >= 5:
            score += 0.3
        elif email_count >= 2:
            score += 0.15

        # Check URL pattern
        path = urlparse(response.url).path.lower()
        for pattern in STAFF_URL_PATTERNS:
            if pattern in path:
                score += 0.2
                break

        # Check for repeating card/list structures
        cards = response.css('[class*="staff"], [class*="person"], [class*="coach"], [class*="card"]')
        if len(cards) >= 3:
            score += 0.2

        return min(score, 1.0)
