from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Coach(Base):
    __tablename__ = "coaches"
    __table_args__ = (
        UniqueConstraint("email_hash", "school_id", name="uq_coach_email_school"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    role_category: Mapped[str | None] = mapped_column(String(50), index=True)  # head_coach, assistant_coach, coordinator, support_staff
    sport: Mapped[str | None] = mapped_column(String(100))
    sport_normalized: Mapped[str | None] = mapped_column(String(100), index=True)
    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(50), index=True)  # denormalized from school
    sub_level: Mapped[str | None] = mapped_column(String(50), index=True)  # denormalized from school
    state: Mapped[str] = mapped_column(String(2), index=True)  # denormalized from school
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school: Mapped["School"] = relationship(back_populates="coaches")

    def __repr__(self):
        return f"<Coach {self.full_name} ({self.email})>"
