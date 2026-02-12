import json
from pathlib import Path

from coach_crawler.exporters._query import query_coaches


def export_json(output_path: str, filters: dict) -> str:
    """Export coaches to JSON file."""
    coaches = query_coaches(filters)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(coaches, f, indent=2, default=str)

    return str(path)
