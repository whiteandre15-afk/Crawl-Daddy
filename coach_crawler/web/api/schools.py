from fastapi import APIRouter, Query
from sqlalchemy import func, or_

from coach_crawler.models import SessionLocal, School, Coach

router = APIRouter()


@router.get("/schools")
def list_schools(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str = Query(None),
    level: str = Query(None),
    sub_level: str = Query(None),
    division: str = Query(None),
    state: str = Query(None),
    crawl_status: str = Query(None),
    sort: str = Query("id"),
    order: str = Query("desc"),
):
    session = SessionLocal()
    try:
        query = session.query(
            School,
            func.count(Coach.id).label("coach_count"),
        ).outerjoin(Coach, Coach.school_id == School.id).group_by(School.id)

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    School.name.ilike(term),
                    School.city.ilike(term),
                    School.athletics_url.ilike(term),
                )
            )

        if level:
            query = query.filter(School.level == level)
        if sub_level:
            query = query.filter(School.sub_level == sub_level)
        if division:
            query = query.filter(School.division == division)
        if state:
            query = query.filter(School.state == state)
        if crawl_status:
            query = query.filter(School.crawl_status == crawl_status)

        total = query.count()

        # Sorting
        sort_col = getattr(School, sort, School.id)
        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()

        schools = []
        for school, coach_count in results:
            schools.append({
                "id": school.id,
                "name": school.name,
                "level": school.level,
                "sub_level": school.sub_level,
                "division": school.division,
                "conference": school.conference,
                "state": school.state,
                "city": school.city,
                "athletics_url": school.athletics_url,
                "staff_directory_url": school.staff_directory_url,
                "crawl_status": school.crawl_status,
                "coach_count": coach_count,
            })

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": max(1, (total + limit - 1) // limit),
            "schools": schools,
        }
    finally:
        session.close()
