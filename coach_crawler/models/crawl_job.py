from datetime import datetime

from sqlalchemy import String, Integer, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    spider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="running")  # running, completed, failed, paused
    urls_total: Mapped[int] = mapped_column(Integer, default=0)
    urls_completed: Mapped[int] = mapped_column(Integer, default=0)
    urls_failed: Mapped[int] = mapped_column(Integer, default=0)
    coaches_found: Mapped[int] = mapped_column(Integer, default=0)
    config_snapshot: Mapped[dict | None] = mapped_column(JSON)

    def __repr__(self):
        return f"<CrawlJob {self.spider_name} ({self.status})>"
