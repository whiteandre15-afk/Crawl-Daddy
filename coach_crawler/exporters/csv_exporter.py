import csv
from pathlib import Path

from coach_crawler.exporters._query import query_coaches


def export_csv(output_path: str, filters: dict) -> str:
    """Export coaches to CSV file."""
    coaches = query_coaches(filters)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "email", "first_name", "last_name", "full_name", "title",
            "role_category", "sport", "school_name", "level", "sub_level", "division",
            "state", "conference", "source_url", "confidence_score", "is_verified",
        ])
        writer.writeheader()
        for coach in coaches:
            writer.writerow(coach)

    return str(path)
