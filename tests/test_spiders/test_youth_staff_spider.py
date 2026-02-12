"""Test youth staff spider."""

import pytest
from coach_crawler.scrapy_project.spiders.youth_staff_spider import YouthStaffSpider


class TestYouthStaffSpider:
    def test_spider_name(self):
        assert YouthStaffSpider.name == "youth_staff"

    def test_depth_limit(self):
        assert YouthStaffSpider.custom_settings.get("DEPTH_LIMIT") == 3

    def test_accepts_sub_level_param(self):
        spider = YouthStaffSpider(level="youth", sub_level="club_team", state="TX")
        assert spider.sub_level == "club_team"
        assert spider.level == "youth"
        assert spider.state == "TX"

    def test_accepts_limit_param(self):
        spider = YouthStaffSpider(limit="100")
        assert spider.limit == 100
