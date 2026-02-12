import re
import hashlib
from urllib.parse import unquote

# Domains to exclude (infrastructure, not coaching emails)
EXCLUDED_DOMAINS = frozenset({
    "example.com", "sidearm.com", "sidearmsports.com", "prestosports.com",
    "maxpreps.com", "facebook.com", "twitter.com", "instagram.com",
    "youtube.com", "google.com", "w3.org", "schema.org", "jquery.com",
    "wordpress.org", "wordpress.com", "squarespace.com", "wix.com",
    "godaddy.com", "cloudflare.com", "amazonaws.com",
    # Youth platform domains
    "sportsengine.com", "leagueapps.com", "teamsnap.com",
    "bluestarsports.com", "stacksports.com", "sportsconnect.com",
    "teamsideline.com",
})

EXCLUDED_PREFIXES = frozenset({
    "noreply", "no-reply", "webmaster", "info", "admin", "support",
    "contact", "help", "abuse", "postmaster", "mailer-daemon",
    "donotreply", "do-not-reply",
})

# Compiled regex patterns ordered by confidence
_MAILTO_RE = re.compile(r'href=["\']mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', re.IGNORECASE)
_PLAIN_EMAIL_RE = re.compile(r'\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b')
_OBFUSCATED_AT_RE = re.compile(
    r'\b([a-zA-Z0-9._%+\-]+)\s*[\[\(]?\s*(?:at|AT)\s*[\]\)]?\s*([a-zA-Z0-9.\-]+)\s*[\[\(]?\s*(?:dot|DOT)\s*[\]\)]?\s*([a-zA-Z]{2,})\b'
)


def email_hash(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()


def _is_excluded(email: str) -> bool:
    local, _, domain = email.partition("@")
    if domain.lower() in EXCLUDED_DOMAINS:
        return True
    if local.lower() in EXCLUDED_PREFIXES:
        return True
    # Skip image/file extensions misidentified as emails
    if domain.lower().endswith((".png", ".jpg", ".gif", ".css", ".js")):
        return True
    return False


class EmailExtractor:
    """Extracts email addresses from HTML content with confidence scoring."""

    def extract(self, html: str, url: str = "") -> list[dict]:
        """Extract all emails from HTML string.

        Returns list of dicts: {email, confidence, source_method}
        """
        results = {}

        # 1. mailto: links — highest confidence
        for match in _MAILTO_RE.finditer(html):
            email = unquote(match.group(1)).strip().lower()
            if not _is_excluded(email):
                results[email] = {"email": email, "confidence": 0.95, "source_method": "mailto"}

        # 2. Plain text email regex
        for match in _PLAIN_EMAIL_RE.finditer(html):
            email = match.group(1).strip().lower()
            if email not in results and not _is_excluded(email):
                results[email] = {"email": email, "confidence": 0.80, "source_method": "regex"}

        # 3. Obfuscated "user [at] domain [dot] com"
        for match in _OBFUSCATED_AT_RE.finditer(html):
            email = f"{match.group(1)}@{match.group(2)}.{match.group(3)}".lower()
            if email not in results and not _is_excluded(email):
                results[email] = {"email": email, "confidence": 0.70, "source_method": "obfuscated"}

        return list(results.values())

    def extract_with_context(self, selector, url: str = "") -> list[dict]:
        """Extract emails from a Scrapy Selector, including surrounding context for name/role association.

        Each result includes: {email, confidence, source_method, context_name, context_title}
        """
        results = []

        # Strategy 1: Find mailto links and walk up to parent for name/title
        for link in selector.css('a[href^="mailto:"]'):
            href = link.attrib.get("href", "")
            email_match = re.match(r'mailto:([^?]+)', href, re.IGNORECASE)
            if not email_match:
                continue
            email = unquote(email_match.group(1)).strip().lower()
            if _is_excluded(email):
                continue

            # Walk up DOM to find context
            parent = link.xpath("ancestor::*[position() <= 4]")
            context_name = None
            context_title = None

            for ancestor in parent:
                # Look for name-like text in headings or strong tags
                name_candidates = ancestor.css("h1::text, h2::text, h3::text, h4::text, strong::text, b::text").getall()
                for name in name_candidates:
                    name = name.strip()
                    if name and len(name) > 3 and "@" not in name:
                        context_name = context_name or name

                # Look for title-like text
                title_candidates = ancestor.css('.title::text, .position::text, .role::text, [class*="title"]::text, [class*="position"]::text').getall()
                for title in title_candidates:
                    title = title.strip()
                    if title and len(title) > 3:
                        context_title = context_title or title

            results.append({
                "email": email,
                "confidence": 0.95,
                "source_method": "mailto",
                "context_name": context_name,
                "context_title": context_title,
            })

        # Strategy 2: Fall back to plain regex on full page text
        page_text = selector.css("body").get("")
        regex_results = self.extract(page_text, url)
        existing_emails = {r["email"] for r in results}
        for r in regex_results:
            if r["email"] not in existing_emails:
                r["context_name"] = None
                r["context_title"] = None
                results.append(r)

        return results
