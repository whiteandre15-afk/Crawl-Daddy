from datetime import datetime

from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # college, high_school, youth
    sub_level: Mapped[str | None] = mapped_column(String(50), index=True)  # high_school, middle_school, club_team, rec_league, academy, camp, etc.
    division: Mapped[str | None] = mapped_column(String(50), index=True)  # NCAA_D1_FBS, NCAA_D2, NAIA, NJCAA, etc.
    conference: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(100))
    athletics_url: Mapped[str | None] = mapped_column(String(500))
    staff_directory_url: Mapped[str | None] = mapped_column(String(500))
    website_platform: Mapped[str | None] = mapped_column(String(50))  # sidearm, prestosports, custom
    organization_type: Mapped[str | None] = mapped_column(String(100))  # club_team, rec_league, academy, camp, ymca, pop_warner, little_league, aau
    crawl_status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    coaches: Mapped[list["Coach"]] = relationship(back_populates="school")

    def __repr__(self):
        sub = f"/{self.sub_level}" if self.sub_level else ""
        return f"<School {self.name} ({self.level}{sub}/{self.division})>"
