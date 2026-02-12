from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from coach_crawler.exporters.csv_exporter import export_csv
from coach_crawler.exporters.json_exporter import export_json
from coach_crawler.exporters.excel_exporter import export_excel

router = APIRouter()

EXPORTS_DIR = Path(__file__).resolve().parents[3] / "exports"


class ExportRequest(BaseModel):
    format: str = "csv"
    level: str | None = None
    sub_level: str | None = None
    division: str | None = None
    state: str | None = None
    sport: str | None = None
    verified_only: bool = False


@router.post("/export")
def run_export(req: ExportRequest):
    EXPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"coaches_{timestamp}"

    filters = {
        "level": req.level,
        "sub_level": req.sub_level,
        "division": req.division,
        "state": req.state,
        "sport": req.sport,
        "verified_only": req.verified_only,
    }

    if req.format == "csv":
        path = export_csv(str(EXPORTS_DIR / f"{filename}.csv"), filters)
    elif req.format == "json":
        path = export_json(str(EXPORTS_DIR / f"{filename}.json"), filters)
    elif req.format == "excel":
        path = export_excel(str(EXPORTS_DIR / f"{filename}.xlsx"), filters)
    else:
        return {"error": f"Unknown format: {req.format}"}

    return {"filename": Path(path).name, "path": f"/exports/{Path(path).name}"}


@router.get("/export/download/{filename}")
def download_export(filename: str):
    path = EXPORTS_DIR / filename
    if not path.exists():
        return {"error": "File not found"}
    return FileResponse(path, filename=filename)
