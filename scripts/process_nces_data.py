#!/usr/bin/env python3
"""Process NCES CCD (Common Core of Data) school files into seed CSVs.

The NCES provides downloadable public data files at:
https://nces.ed.gov/ccd/files.asp

Download the "Directory" file (school-level data) and pass it to this script.
The script classifies schools by grade range:
  - Grades 9-12 → high_school
  - Grades 6-8  → middle_school

Usage:
    python scripts/process_nces_data.py <nces_csv_path> [--state TX]

Output:
    seeds/hs_schools.csv
    seeds/ms_schools.csv
"""

import csv
import sys
import re
import argparse
from pathlib import Path


def make_slug(name: str, state: str = "") -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    if state:
        slug = f"{slug}-{state.lower()}"
    return slug


def classify_grade_range(low_grade: str, high_grade: str) -> str | None:
    """Classify a school as high_school or middle_school based on grade range."""
    grade_order = {
        "PK": -1, "KG": 0, "01": 1, "02": 2, "03": 3, "04": 4,
        "05": 5, "06": 6, "07": 7, "08": 8, "09": 9, "10": 10,
        "11": 11, "12": 12, "13": 13, "UG": 14,
    }

    high_num = grade_order.get(high_grade.strip().upper(), -1)
    low_num = grade_order.get(low_grade.strip().upper(), -1)

    if high_num >= 9:
        return "high_school"
    elif 6 <= high_num <= 8 and low_num >= 4:
        return "middle_school"
    return None


def process_nces(input_path: str, state_filter: str | None = None):
    seeds_dir = Path(__file__).resolve().parents[1] / "seeds"
    seeds_dir.mkdir(exist_ok=True)

    hs_schools = []
    ms_schools = []

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # NCES CCD common column names (may vary by year)
        # Try multiple common column name patterns
        for row in reader:
            # School name
            name = (
                row.get("SCH_NAME")
                or row.get("SCHNAM")
                or row.get("school_name")
                or row.get("NAME")
                or ""
            ).strip()

            if not name:
                continue

            # State
            state = (
                row.get("LSTATE")
                or row.get("STATENAME")
                or row.get("state")
                or row.get("ST")
                or ""
            ).strip()

            if state_filter and state != state_filter:
                continue

            # City
            city = (
                row.get("LCITY")
                or row.get("CITY")
                or row.get("city")
                or ""
            ).strip()

            # Grade range
            low_grade = (
                row.get("GSLO")
                or row.get("LOW_GRADE")
                or row.get("low_grade")
                or ""
            ).strip()

            high_grade = (
                row.get("GSHI")
                or row.get("HIGH_GRADE")
                or row.get("high_grade")
                or ""
            ).strip()

            # Website
            website = (
                row.get("WEBSITE")
                or row.get("SCH_WEB")
                or row.get("website")
                or ""
            ).strip()

            if not low_grade or not high_grade:
                continue

            sub_level = classify_grade_range(low_grade, high_grade)
            if not sub_level:
                continue

            school_data = {
                "name": name,
                "level": "high_school",
                "sub_level": sub_level,
                "state": state,
                "city": city,
                "athletics_url": website if website else "",
            }

            if sub_level == "high_school":
                hs_schools.append(school_data)
            else:
                ms_schools.append(school_data)

    # Write HS seeds
    hs_path = seeds_dir / "hs_schools.csv"
    fieldnames = ["name", "level", "sub_level", "state", "city", "athletics_url"]

    with open(hs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for school in hs_schools:
            writer.writerow(school)

    # Write MS seeds
    ms_path = seeds_dir / "ms_schools.csv"
    with open(ms_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for school in ms_schools:
            writer.writerow(school)

    print(f"Written {len(hs_schools)} high schools to {hs_path}")
    print(f"Written {len(ms_schools)} middle schools to {ms_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process NCES CCD data into seed CSVs")
    parser.add_argument("input", help="Path to NCES CCD CSV file")
    parser.add_argument("--state", help="Filter by state (2-letter code)", default=None)
    args = parser.parse_args()

    process_nces(args.input, args.state)
