BOT_NAME = "coach_crawler"
SPIDER_MODULES = ["coach_crawler.scrapy_project.spiders"]
NEWSPIDER_MODULE = "coach_crawler.scrapy_project.spiders"

# Polite crawling defaults
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1.0
RANDOMIZE_DOWNLOAD_DELAY = True

# Respect robots.txt
ROBOTSTXT_OBEY = True

# AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Retry
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# User agent
USER_AGENT = "CoachCrawler/1.0 (Educational Research; contact@coachcrawler.dev)"

# Pipelines (order matters)
ITEM_PIPELINES = {
    "coach_crawler.scrapy_project.pipelines.EmailValidationPipeline": 100,
    "coach_crawler.scrapy_project.pipelines.DeduplicationPipeline": 200,
    "coach_crawler.scrapy_project.pipelines.DatabasePipeline": 300,
}

# Middlewares
DOWNLOADER_MIDDLEWARES = {
    "coach_crawler.scrapy_project.middlewares.ProxyRotationMiddleware": 350,
    "coach_crawler.scrapy_project.middlewares.UserAgentRotationMiddleware": 400,
}

# Playwright (for JS-rendered sites)
DOWNLOAD_HANDLERS = {
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

# Per-domain overrides
DOMAIN_RATE_LIMITS = {
    "ncaa.org": {"delay": 3.0, "concurrent": 1},
    "maxpreps.com": {"delay": 5.0, "concurrent": 1},
    "naia.org": {"delay": 3.0, "concurrent": 1},
    "nces.ed.gov": {"delay": 5.0, "concurrent": 1},
    # Youth — existing sources
    "usclubsoccer.org": {"delay": 3.0, "concurrent": 1},
    "aauathletics.org": {"delay": 3.0, "concurrent": 1},
    "aausports.org": {"delay": 3.0, "concurrent": 1},
    "popwarner.com": {"delay": 3.0, "concurrent": 1},
    "littleleague.org": {"delay": 3.0, "concurrent": 1},
    "ymca.org": {"delay": 3.0, "concurrent": 1},
    "usaswimming.org": {"delay": 3.0, "concurrent": 1},
    # Youth — platforms
    "sportsengine.com": {"delay": 2.0, "concurrent": 2},
    "leagueapps.com": {"delay": 2.0, "concurrent": 2},
    # Youth — national organizations
    "ayso.org": {"delay": 3.0, "concurrent": 1},
    "usyouthsoccer.org": {"delay": 3.0, "concurrent": 1},
    "usafootball.com": {"delay": 3.0, "concurrent": 1},
    "usabaseball.com": {"delay": 3.0, "concurrent": 1},
    "usssa.com": {"delay": 3.0, "concurrent": 1},
    "i9sports.com": {"delay": 3.0, "concurrent": 1},
    "upward.org": {"delay": 3.0, "concurrent": 1},
    "uslacrosse.org": {"delay": 3.0, "concurrent": 1},
    "usahockey.com": {"delay": 3.0, "concurrent": 1},
    "baberuthleague.org": {"delay": 3.0, "concurrent": 1},
    "ripkenbaseball.com": {"delay": 3.0, "concurrent": 1},
    "pony.org": {"delay": 3.0, "concurrent": 1},
    "usavolleyball.org": {"delay": 3.0, "concurrent": 1},
    "usawrestling.org": {"delay": 3.0, "concurrent": 1},
    "usatf.org": {"delay": 3.0, "concurrent": 1},
}
