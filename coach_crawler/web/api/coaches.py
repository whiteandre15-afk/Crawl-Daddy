from fastapi import APIRouter, Query
from sqlalchemy import func, or_

from coach_crawler.models import SessionLocal, Coach, School

router = APIRouter()


@router.get("/coaches")
def list_coaches(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str = Query(None),
    level: str = Query(None),
    sub_level: str = Query(None),
    division: str = Query(None),
    state: str = Query(None),
    sport: str = Query(None),
    role: str = Query(None),
    sort: str = Query("id"),
    order: str = Query("desc"),
):
    session = SessionLocal()
    try:
        query = session.query(Coach, School.name.label("school_name"), School.division).join(
            School, Coach.school_id == School.id
        )

        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    Coach.email.ilike(term),
                    Coach.full_name.ilike(term),
                    Coach.title.ilike(term),
                    School.name.ilike(term),
                )
            )

        if level:
            query = query.filter(Coach.level == level)
        if sub_level:
            query = query.filter(Coach.sub_level == sub_level)
        if division:
            query = query.filter(School.division == division)
        if state:
            query = query.filter(Coach.state == state)
        if sport:
            query = query.filter(Coach.sport_normalized == sport)
        if role:
            query = query.filter(Coach.role_category == role)

        total = query.count()

        # Sorting
        sort_col = getattr(Coach, sort, Coach.id)
        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        # Pagination
        offset = (page - 1) * limit
        results = query.offset(offset).limit(limit).all()

        coaches = []
        for coach, school_name, division_val in results:
            coaches.append({
                "id": coach.id,
                "email": coach.email,
                "full_name": coach.full_name,
                "first_name": coach.first_name,
                "last_name": coach.last_name,
                "title": coach.title,
                "role_category": coach.role_category,
                "sport": coach.sport_normalized,
                "school_name": school_name,
                "level": coach.level,
                "sub_level": coach.sub_level,
                "division": division_val,
                "state": coach.state,
                "source_url": coach.source_url,
                "confidence_score": coach.confidence_score,
                "is_verified": coach.is_verified,
            })

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "coaches": coaches,
        }
    finally:
        session.close()
