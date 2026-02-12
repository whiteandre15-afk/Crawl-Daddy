import re

# Sport name normalization map
SPORT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bfootball\b", re.I), "football"),
    (re.compile(r"\bmen'?s?\s+basketball\b", re.I), "mens_basketball"),
    (re.compile(r"\bwomen'?s?\s+basketball\b", re.I), "womens_basketball"),
    (re.compile(r"\bbasketball\b", re.I), "basketball"),
    (re.compile(r"\bbaseball\b", re.I), "baseball"),
    (re.compile(r"\bsoftball\b", re.I), "softball"),
    (re.compile(r"\bmen'?s?\s+soccer\b", re.I), "mens_soccer"),
    (re.compile(r"\bwomen'?s?\s+soccer\b", re.I), "womens_soccer"),
    (re.compile(r"\bsoccer\b", re.I), "soccer"),
    (re.compile(r"\bvolleyball\b", re.I), "volleyball"),
    (re.compile(r"\bmen'?s?\s+tennis\b", re.I), "mens_tennis"),
    (re.compile(r"\bwomen'?s?\s+tennis\b", re.I), "womens_tennis"),
    (re.compile(r"\btennis\b", re.I), "tennis"),
    (re.compile(r"\bmen'?s?\s+golf\b", re.I), "mens_golf"),
    (re.compile(r"\bwomen'?s?\s+golf\b", re.I), "womens_golf"),
    (re.compile(r"\bgolf\b", re.I), "golf"),
    (re.compile(r"\btrack\s*(?:&|and)\s*field\b", re.I), "track_and_field"),
    (re.compile(r"\bcross\s+country\b", re.I), "cross_country"),
    (re.compile(r"\bswimming\s*(?:&|and)?\s*diving\b", re.I), "swimming_diving"),
    (re.compile(r"\bswimming\b", re.I), "swimming"),
    (re.compile(r"\bwrestling\b", re.I), "wrestling"),
    (re.compile(r"\blacrosse\b", re.I), "lacrosse"),
    (re.compile(r"\bfield\s+hockey\b", re.I), "field_hockey"),
    (re.compile(r"\bice\s+hockey|hockey\b", re.I), "ice_hockey"),
    (re.compile(r"\bgymnastics\b", re.I), "gymnastics"),
    (re.compile(r"\browing\b", re.I), "rowing"),
    (re.compile(r"\bwater\s+polo\b", re.I), "water_polo"),
    (re.compile(r"\bcheer(?:leading)?\b", re.I), "cheerleading"),
    (re.compile(r"\bdance\b", re.I), "dance"),
    (re.compile(r"\bfencing\b", re.I), "fencing"),
    (re.compile(r"\brifl(?:e|ery)\b", re.I), "rifle"),
    (re.compile(r"\bbowling\b", re.I), "bowling"),
    (re.compile(r"\beach\s+volleyball\b|sand\s+volleyball\b", re.I), "beach_volleyball"),
]


class SportClassifier:
    """Detect and normalize sport names from text."""

    def classify(self, text: str | None) -> str | None:
        """Return normalized sport name from text, or None."""
        if not text:
            return None
        for pattern, sport in SPORT_PATTERNS:
            if pattern.search(text):
                return sport
        return None

    def classify_from_url(self, url: str) -> str | None:
        """Try to detect sport from URL path segments."""
        return self.classify(url.replace("-", " ").replace("/", " "))
