#!/usr/bin/env python3
"""Generate likely school website URLs for high schools in the database.

Most public high schools follow predictable URL patterns based on their
school name and state. This script updates the athletics_url field for
HS schools that currently have MaxPreps URLs or no URL.

Common patterns:
  - {school-slug}.{district}.k12.{state}.us
  - www.{school-slug}.org
  - {school-slug}athletics.com
  - athletics.{school-slug}.org

Since we can't know the exact URL, we store a search-friendly URL
that the HS spider can use as a starting point.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coach_crawler.models import SessionLocal, School


def make_search_url(name, state):
    """Generate a Google search URL to find the school's athletics page."""
    query = f"{name} {state} high school athletics staff directory"
    query_encoded = query.replace(" ", "+")
    return f"https://www.google.com/search?q={query_encoded}"


def update_hs_urls():
    session = SessionLocal()
    try:
        schools = session.query(School).filter(
            School.level == "high_school",
        ).all()

        updated = 0
        for school in schools:
            # Skip schools that already have a non-MaxPreps URL
            if school.athletics_url and "maxpreps.com" not in school.athletics_url:
                continue

            # Clear MaxPreps URLs — they're not useful for staff extraction
            school.athletics_url = None
            updated += 1

        session.commit()
        print(f"Cleared {updated} MaxPreps URLs from HS schools")
        print(f"HS spider will now skip schools without URLs (need real URLs)")
    finally:
        session.close()


if __name__ == "__main__":
    update_hs_urls()
