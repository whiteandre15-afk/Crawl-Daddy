from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://crawler:crawler_dev@localhost:5432/coach_crawler"
    redis_url: str = "redis://localhost:6379/0"

    # Proxy
    proxy_list_path: str = ""
    proxy_api_url: str = ""

    # Crawl behavior
    concurrent_requests: int = 16
    download_delay: float = 1.0
    robotstxt_obey: bool = True

    # Playwright
    playwright_headless: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
