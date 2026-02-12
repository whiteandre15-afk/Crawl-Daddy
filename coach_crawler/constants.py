"""Level, sub-level, and organization type constants for coach-crawler."""

LEVELS = ("college", "high_school", "youth")

SUB_LEVELS = {
    "college": (None,),
    "high_school": ("high_school", "middle_school"),
    "youth": (
        "club_team",
        "rec_league",
        "academy",
        "camp",
        "ymca",
        "pop_warner",
        "little_league",
        "aau",
        "travel_team",
        "community_center",
        "national_org",
        "municipal_rec",
        "other",
    ),
}

ORGANIZATION_TYPES = {
    "club_team": "Club / Travel Team",
    "rec_league": "Recreational League",
    "academy": "Private Academy",
    "camp": "Sports Camp",
    "ymca": "YMCA / Community Center",
    "pop_warner": "Pop Warner",
    "little_league": "Little League",
    "aau": "AAU",
    "travel_team": "Travel Team",
    "community_center": "Community Center / Parks & Rec",
    "national_org": "National Organization Chapter",
    "municipal_rec": "Municipal Recreation Program",
    "ayso": "AYSO",
    "usa_football": "USA Football",
    "usssa": "USSSA",
    "i9_sports": "i9 Sports",
    "upward_sports": "Upward Sports",
    "babe_ruth": "Babe Ruth League",
    "cal_ripken": "Cal Ripken Baseball",
    "pony_baseball": "Pony Baseball/Softball",
    "sportsengine_org": "SportsEngine Organization",
    "leagueapps_org": "LeagueApps Organization",
    "other": "Other",
}
