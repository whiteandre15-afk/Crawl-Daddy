import logging

from sqlalchemy import func

from coach_crawler.models import SessionLocal, Coach

logger = logging.getLogger(__name__)


def deduplicate_coaches(dry_run: bool = True) -> dict:
    """Find and optionally remove duplicate coaches (same email across schools).

    Keeps the most recent record per email.
    Returns stats: {total_dupes, removed}
    """
    session = SessionLocal()
    try:
        # Find emails that appear more than once
        dupes = (
            session.query(Coach.email, func.count(Coach.id).label("cnt"))
            .group_by(Coach.email)
            .having(func.count(Coach.id) > 1)
            .all()
        )

        total_dupes = 0
        removed = 0

        for email, count in dupes:
            total_dupes += count - 1
            # Keep the most recently crawled record
            records = (
                session.query(Coach)
                .filter(Coach.email == email)
                .order_by(Coach.crawled_at.desc())
                .all()
            )

            # Mark all but the first (most recent) for deletion
            for record in records[1:]:
                if not dry_run:
                    session.delete(record)
                    removed += 1
                else:
                    removed += 1

        if not dry_run:
            session.commit()

        logger.info(f"Dedup: {total_dupes} duplicates found, {removed} {'would be' if dry_run else ''} removed")
        return {"total_dupes": total_dupes, "removed": removed}
    finally:
        session.close()
