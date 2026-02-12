from pathlib import Path

import pandas as pd

from coach_crawler.exporters._query import query_coaches


def export_excel(output_path: str, filters: dict) -> str:
    """Export coaches to Excel file."""
    coaches = query_coaches(filters)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(coaches)
    df.to_excel(path, index=False, engine="openpyxl")

    return str(path)
