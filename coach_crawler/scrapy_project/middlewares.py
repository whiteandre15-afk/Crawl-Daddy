import random
import logging

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]


class UserAgentRotationMiddleware:
    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(USER_AGENTS)


class ProxyRotationMiddleware:
    def __init__(self):
        self.proxies: list[str] = []
        self.index = 0

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        proxy_path = crawler.settings.get("PROXY_LIST_PATH", "")
        if proxy_path:
            try:
                with open(proxy_path) as f:
                    middleware.proxies = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(middleware.proxies)} proxies")
            except FileNotFoundError:
                logger.warning(f"Proxy list not found: {proxy_path}")
        return middleware

    def process_request(self, request, spider):
        if self.proxies:
            proxy = self.proxies[self.index % len(self.proxies)]
            request.meta["proxy"] = proxy
            self.index += 1
