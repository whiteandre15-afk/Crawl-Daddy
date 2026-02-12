from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CrawlUrl(Base):
    __tablename__ = "crawl_urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    school_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("schools.id"), index=True)
    url_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # seed_list, athletics_home, staff_directory, staff_profile
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)  # pending, in_progress, completed, failed, skipped
    http_status: Mapped[int | None] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    spider_name: Mapped[str | None] = mapped_column(String(100), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<CrawlUrl {self.url} ({self.status})>"
