"""Test seed discovery spiders."""

import pytest
from coach_crawler.scrapy_project.spiders.base_seed_spider import BaseSeedSpider
from coach_crawler.scrapy_project.spiders.maxpreps_seed_spider import MaxPrepsSeedSpider
from coach_crawler.scrapy_project.spiders.state_athletic_assoc_spider import StateAthleticAssocSeedSpider
from coach_crawler.scrapy_project.spiders.youth_seed_spiders import (
    USClubSoccerSeedSpider,
    AAUSeedSpider,
    PopWarnerSeedSpider,
    LittleLeagueSeedSpider,
    YMCASeedSpider,
    USASwimmingSeedSpider,
)
from coach_crawler.scrapy_project.items import SchoolItem


class TestBaseSeedSpider:
    def test_uses_school_seed_pipeline(self):
        pipelines = BaseSeedSpider.custom_settings.get("ITEM_PIPELINES", {})
        assert "coach_crawler.scrapy_project.pipelines.SchoolSeedPipeline" in pipelines

    def test_polite_rate_limits(self):
        assert BaseSeedSpider.custom_settings["DOWNLOAD_DELAY"] == 3.0
        assert BaseSeedSpider.custom_settings["CONCURRENT_REQUESTS_PER_DOMAIN"] == 1

    def test_make_school_item(self):
        # Use a concrete spider since Scrapy requires a name
        spider = MaxPrepsSeedSpider()
        item = spider.make_school_item(
            name="Test School",
            level="high_school",
            sub_level="high_school",
            state="TX",
            city="Austin",
        )
        assert isinstance(item, SchoolItem)
        assert item["name"] == "Test School"
        assert item["level"] == "high_school"
        assert item["sub_level"] == "high_school"
        assert item["state"] == "TX"
        assert "tx" in item["slug"]

    def test_make_school_item_respects_limit(self):
        spider = MaxPrepsSeedSpider(limit="2")
        item1 = spider.make_school_item(name="School 1", level="youth", sub_level="club_team", state="TX")
        item2 = spider.make_school_item(name="School 2", level="youth", sub_level="club_team", state="TX")
        item3 = spider.make_school_item(name="School 3", level="youth", sub_level="club_team", state="TX")
        assert item1 is not None
        assert item2 is not None
        assert item3 is None

    def test_slug_includes_state(self):
        spider = MaxPrepsSeedSpider()
        item = spider.make_school_item(
            name="Central High School",
            level="high_school",
            sub_level="high_school",
            state="OH",
        )
        assert item["slug"] == "central-high-school-oh"


class TestMaxPrepsSeedSpider:
    def test_spider_name(self):
        assert MaxPrepsSeedSpider.name == "maxpreps_seed"

    def test_slow_rate_limit(self):
        assert MaxPrepsSeedSpider.custom_settings["DOWNLOAD_DELAY"] == 5.0


class TestStateAthleticAssocSeedSpider:
    def test_spider_name(self):
        assert StateAthleticAssocSeedSpider.name == "state_athletic_assoc_seed"

    def test_has_state_configs(self):
        from coach_crawler.scrapy_project.spiders.state_athletic_assoc_spider import STATE_CONFIGS
        assert len(STATE_CONFIGS) >= 10
        assert "TX" in STATE_CONFIGS
        assert "CA" in STATE_CONFIGS


class TestYouthSeedSpiders:
    def test_us_club_soccer_name(self):
        assert USClubSoccerSeedSpider.name == "us_club_soccer_seed"

    def test_aau_name(self):
        assert AAUSeedSpider.name == "aau_seed"

    def test_pop_warner_name(self):
        assert PopWarnerSeedSpider.name == "pop_warner_seed"

    def test_little_league_name(self):
        assert LittleLeagueSeedSpider.name == "little_league_seed"

    def test_ymca_name(self):
        assert YMCASeedSpider.name == "ymca_seed"

    def test_usa_swimming_name(self):
        assert USASwimmingSeedSpider.name == "usa_swimming_seed"
