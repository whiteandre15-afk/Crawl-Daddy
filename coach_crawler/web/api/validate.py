from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func

from coach_crawler.models import SessionLocal, Coach
from coach_crawler.validators.email_validator import validate_email
from coach_crawler.validators.dedup import deduplicate_coaches

router = APIRouter()


class ValidateEmailsRequest(BaseModel):
    check_mx: bool = False
    batch_size: int = 1000


class DedupRequest(BaseModel):
    dry_run: bool = True


@router.get("/validate/status")
def validate_status():
    """Get validation summary stats."""
    session = SessionLocal()
    try:
        total = session.query(func.count(Coach.id)).scalar() or 0
        verified = session.query(func.count(Coach.id)).filter(Coach.is_verified == True).scalar() or 0
        unverified = total - verified

        # Count emails appearing more than once
        dupes = (
            session.query(func.count())
            .select_from(
                session.query(Coach.email)
                .group_by(Coach.email)
                .having(func.count(Coach.id) > 1)
                .subquery()
            )
        ).scalar() or 0

        return {
            "total_coaches": total,
            "verified": verified,
            "unverified": unverified,
            "duplicate_emails": dupes,
        }
    finally:
        session.close()


@router.post("/validate/emails")
def run_validate_emails(req: ValidateEmailsRequest):
    """Validate all unverified email addresses."""
    session = SessionLocal()
    try:
        coaches = session.query(Coach).filter(Coach.is_verified == False).all()
        total_checked = len(coaches)

        valid_count = 0
        invalid_count = 0
        disposable_count = 0

        for coach in coaches:
            result = validate_email(coach.email, check_mx=req.check_mx)

            if result["valid"]:
                coach.is_verified = True
                valid_count += 1
            else:
                invalid_count += 1

            if result.get("is_disposable"):
                disposable_count += 1

        session.commit()

        return {
            "total_checked": total_checked,
            "valid": valid_count,
            "invalid": invalid_count,
            "disposable": disposable_count,
        }
    finally:
        session.close()


@router.post("/validate/dedup")
def run_dedup(req: DedupRequest):
    """Remove duplicate coaching records."""
    result = deduplicate_coaches(dry_run=req.dry_run)
    return {
        "total_dupes": result["total_dupes"],
        "removed": result["removed"],
        "dry_run": req.dry_run,
    }
