from fastapi import APIRouter
from sqlalchemy import func

from coach_crawler.models import SessionLocal, School, Coach, CrawlJob

router = APIRouter()


@router.get("/stats")
def get_stats():
    session = SessionLocal()
    try:
        total_schools = session.query(func.count(School.id)).scalar() or 0
        crawled_schools = session.query(func.count(School.id)).filter(School.crawl_status == "crawled").scalar() or 0
        pending_schools = session.query(func.count(School.id)).filter(School.crawl_status == "pending").scalar() or 0
        failed_schools = session.query(func.count(School.id)).filter(School.crawl_status == "failed").scalar() or 0

        total_coaches = session.query(func.count(Coach.id)).scalar() or 0
        unique_emails = session.query(func.count(func.distinct(Coach.email))).scalar() or 0
        verified = session.query(func.count(Coach.id)).filter(Coach.is_verified == True).scalar() or 0

        by_level = [
            {"level": level or "unknown", "count": count}
            for level, count in session.query(Coach.level, func.count(Coach.id)).group_by(Coach.level).all()
        ]

        by_state = [
            {"state": state or "??", "count": count}
            for state, count in session.query(Coach.state, func.count(Coach.id))
            .group_by(Coach.state)
            .order_by(func.count(Coach.id).desc())
            .limit(15)
            .all()
        ]

        by_sub_level = [
            {"level": level or "unknown", "sub_level": sub or "-", "count": count}
            for level, sub, count in session.query(Coach.level, Coach.sub_level, func.count(Coach.id))
            .group_by(Coach.level, Coach.sub_level)
            .all()
        ]

        by_sport = [
            {"sport": sport or "unknown", "count": count}
            for sport, count in session.query(Coach.sport_normalized, func.count(Coach.id))
            .filter(Coach.sport_normalized.isnot(None))
            .group_by(Coach.sport_normalized)
            .order_by(func.count(Coach.id).desc())
            .limit(10)
            .all()
        ]

        recent_crawls = [
            {
                "id": job.id,
                "spider_name": job.spider_name,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "status": job.status,
                "coaches_found": job.coaches_found,
                "urls_completed": job.urls_completed,
                "urls_failed": job.urls_failed,
            }
            for job in session.query(CrawlJob).order_by(CrawlJob.id.desc()).limit(10).all()
        ]

        return {
            "schools": {
                "total": total_schools,
                "crawled": crawled_schools,
                "pending": pending_schools,
                "failed": failed_schools,
            },
            "coaches": {
                "total": total_coaches,
                "unique_emails": unique_emails,
                "verified": verified,
            },
            "by_level": by_level,
            "by_sub_level": by_sub_level,
            "by_state": by_state,
            "by_sport": by_sport,
            "recent_crawls": recent_crawls,
        }
    finally:
        session.close()
