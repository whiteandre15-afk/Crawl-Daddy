import re

# Ordered by specificity — check most specific first
ROLE_PATTERNS = [
    (r'\b(?:head\s+coach)\b', "head_coach"),
    (r'\b(?:associate\s+head\s+coach)\b', "associate_head_coach"),
    (r'\b(?:assistant\s+coach|asst\.?\s+coach)\b', "assistant_coach"),
    (r'\b(?:offensive\s+coordinator|oc)\b', "coordinator"),
    (r'\b(?:defensive\s+coordinator|dc)\b', "coordinator"),
    (r'\b(?:coordinator)\b', "coordinator"),
    (r'\b(?:athletic\s+director|ad|director\s+of\s+athletics)\b', "athletic_director"),
    (r'\b(?:director\s+of\s+(?:operations|player\s+development|recruiting|performance))\b', "director"),
    (r'\b(?:strength\s+and\s+conditioning|s&c)\b', "support_staff"),
    (r'\b(?:sports\s+information|sid|media\s+relations)\b', "support_staff"),
    (r'\b(?:trainer|athletic\s+trainer)\b', "support_staff"),
    # Youth-specific roles
    (r'\b(?:league\s+president|president)\b', "league_officer"),
    (r'\b(?:league\s+director|program\s+director)\b', "director"),
    (r'\b(?:commissioner)\b', "league_officer"),
    (r'\b(?:team\s+manager|manager)\b', "team_manager"),
    (r'\b(?:registrar)\b', "support_staff"),
    (r'\b(?:player\s+agent)\b', "support_staff"),
    (r'\b(?:safety\s+officer)\b', "support_staff"),
    (r'\b(?:board\s+(?:member|chair(?:man|person|woman)?))\b', "board_member"),
    (r'\b(?:treasurer|secretary)\b', "board_member"),
    (r'\b(?:volunteer\s+(?:assistant|coach))\b', "volunteer"),
    (r'\b(?:graduate\s+assistant|ga)\b', "graduate_assistant"),
    (r'\b(?:intern)\b', "intern"),
    (r'\b(?:coach)\b', "coach"),  # generic fallback
]

_COMPILED = [(re.compile(pattern, re.IGNORECASE), category) for pattern, category in ROLE_PATTERNS]


class RoleExtractor:
    """Classify coaching title strings into standardized role categories."""

    def classify(self, title: str | None) -> str | None:
        if not title:
            return None

        for pattern, category in _COMPILED:
            if pattern.search(title):
                return category

        return None
