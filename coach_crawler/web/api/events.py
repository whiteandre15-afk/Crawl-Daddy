import json
import asyncio

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from coach_crawler.models import SessionLocal, CrawlJob

router = APIRouter()


@router.get("/events/crawl/{crawl_id}")
async def crawl_events(crawl_id: int):
    async def event_generator():
        last_coaches = -1
        last_urls = -1

        while True:
            session = SessionLocal()
            try:
                job = session.query(CrawlJob).filter(CrawlJob.id == crawl_id).first()
                if not job:
                    yield f"data: {json.dumps({'error': 'Crawl not found'})}\n\n"
                    break

                coaches = job.coaches_found or 0
                urls = job.urls_completed or 0

                if coaches != last_coaches or urls != last_urls:
                    data = {
                        "status": job.status,
                        "urls_completed": urls,
                        "urls_total": job.urls_total or 0,
                        "urls_failed": job.urls_failed or 0,
                        "coaches_found": coaches,
                        "spider_name": job.spider_name,
                    }
                    yield f"event: progress\ndata: {json.dumps(data)}\n\n"
                    last_coaches = coaches
                    last_urls = urls

                if job.status in ("completed", "failed"):
                    data = {
                        "status": job.status,
                        "coaches_found": coaches,
                    }
                    yield f"event: {job.status}\ndata: {json.dumps(data)}\n\n"
                    break
            finally:
                session.close()

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
