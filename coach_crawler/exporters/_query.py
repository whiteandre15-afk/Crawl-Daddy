from coach_crawler.models import SessionLocal, Coach, School


def query_coaches(filters: dict) -> list[dict]:
    """Query coaches from DB with optional filters. Returns list of dicts."""
    session = SessionLocal()
    try:
        query = session.query(Coach, School).join(School, Coach.school_id == School.id)

        level = filters.get("level")
        sub_level = filters.get("sub_level")
        division = filters.get("division")
        state = filters.get("state")
        sport = filters.get("sport")
        verified_only = filters.get("verified_only", False)

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
        if verified_only:
            query = query.filter(Coach.is_verified == True)

        results = []
        for coach, school in query.all():
            results.append({
                "email": coach.email,
                "first_name": coach.first_name,
                "last_name": coach.last_name,
                "full_name": coach.full_name,
                "title": coach.title,
                "role_category": coach.role_category,
                "sport": coach.sport_normalized,
                "school_name": school.name,
                "level": coach.level,
                "sub_level": coach.sub_level,
                "division": school.division,
                "state": coach.state,
                "conference": school.conference,
                "source_url": coach.source_url,
                "confidence_score": coach.confidence_score,
                "is_verified": coach.is_verified,
            })

        return results
    finally:
        session.close()
