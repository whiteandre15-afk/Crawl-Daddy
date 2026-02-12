import pytest
from coach_crawler.extractors.role_extractor import RoleExtractor


@pytest.fixture
def extractor():
    return RoleExtractor()


class TestRoleExtractor:
    def test_head_coach(self, extractor):
        assert extractor.classify("Head Coach") == "head_coach"
        assert extractor.classify("HEAD COACH - Football") == "head_coach"

    def test_assistant_coach(self, extractor):
        assert extractor.classify("Assistant Coach") == "assistant_coach"
        assert extractor.classify("Asst. Coach - Baseball") == "assistant_coach"

    def test_coordinator(self, extractor):
        assert extractor.classify("Offensive Coordinator") == "coordinator"
        assert extractor.classify("Defensive Coordinator") == "coordinator"

    def test_athletic_director(self, extractor):
        assert extractor.classify("Athletic Director") == "athletic_director"
        assert extractor.classify("Director of Athletics") == "athletic_director"

    def test_support_staff(self, extractor):
        assert extractor.classify("Strength and Conditioning Coach") == "support_staff"
        assert extractor.classify("Sports Information Director") == "support_staff"

    def test_none_input(self, extractor):
        assert extractor.classify(None) is None

    def test_unknown_title(self, extractor):
        assert extractor.classify("Groundskeeper") is None
