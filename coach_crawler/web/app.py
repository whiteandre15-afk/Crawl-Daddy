from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from coach_crawler.web.api import stats, crawl, coaches, export, events, seeds, schools, validate

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Coach Crawler", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/exports", StaticFiles(directory=str(BASE_DIR.parent.parent / "exports")), name="exports")

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# API routes (all still needed for the crawl button + data access)
app.include_router(stats.router, prefix="/api")
app.include_router(crawl.router, prefix="/api")
app.include_router(coaches.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(seeds.router, prefix="/api")
app.include_router(schools.router, prefix="/api")
app.include_router(validate.router, prefix="/api")


# Pages
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/coaches", response_class=HTMLResponse)
async def coaches_page(request: Request):
    return templates.TemplateResponse("coaches.html", {"request": request})


@app.get("/schools", response_class=HTMLResponse)
async def schools_page(request: Request):
    return templates.TemplateResponse("schools.html", {"request": request})


@app.get("/crawl", response_class=HTMLResponse)
async def crawl_page(request: Request):
    return templates.TemplateResponse("crawl.html", {"request": request})


@app.get("/crawl/{crawl_id}", response_class=HTMLResponse)
async def crawl_detail_page(request: Request, crawl_id: int):
    return templates.TemplateResponse("crawl_detail.html", {"request": request, "crawl_id": crawl_id})


@app.get("/seeds", response_class=HTMLResponse)
async def seeds_page(request: Request):
    return templates.TemplateResponse("seeds.html", {"request": request})


@app.get("/tools", response_class=HTMLResponse)
async def tools_page(request: Request):
    return templates.TemplateResponse("tools.html", {"request": request})


@app.on_event("startup")
async def startup():
    from coach_crawler.models import init_db
    init_db()
    exports_dir = BASE_DIR.parent.parent / "exports"
    exports_dir.mkdir(exist_ok=True)
