"""Test model schema changes for sub_level and organization_type."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from coach_crawler.models.base import Base
from coach_crawler.models.school import School
from coach_crawler.models.coach import Coach


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestSchoolModel:
    def test_school_has_sub_level_column(self, db_session):
        inspector = inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("schools")}
        assert "sub_level" in columns

    def test_school_has_organization_type_column(self, db_session):
        inspector = inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("schools")}
        assert "organization_type" in columns

    def test_create_college_school(self, db_session):
        school = School(
            name="Test University",
            slug="test-university",
            level="college",
            state="TX",
        )
        db_session.add(school)
        db_session.commit()
        assert school.id is not None
        assert school.sub_level is None

    def test_create_high_school(self, db_session):
        school = School(
            name="Central High School",
            slug="central-high-school-tx",
            level="high_school",
            sub_level="high_school",
            state="TX",
            city="Austin",
        )
        db_session.add(school)
        db_session.commit()
        assert school.sub_level == "high_school"

    def test_create_middle_school(self, db_session):
        school = School(
            name="Central Middle School",
            slug="central-middle-school-tx",
            level="high_school",
            sub_level="middle_school",
            state="TX",
        )
        db_session.add(school)
        db_session.commit()
        assert school.level == "high_school"
        assert school.sub_level == "middle_school"

    def test_create_youth_club(self, db_session):
        school = School(
            name="Texas Soccer Club",
            slug="texas-soccer-club-tx",
            level="youth",
            sub_level="club_team",
            organization_type="club_team",
            state="TX",
        )
        db_session.add(school)
        db_session.commit()
        assert school.level == "youth"
        assert school.sub_level == "club_team"
        assert school.organization_type == "club_team"

    def test_create_youth_rec(self, db_session):
        school = School(
            name="Austin YMCA",
            slug="austin-ymca-tx",
            level="youth",
            sub_level="rec_league",
            organization_type="ymca",
            state="TX",
        )
        db_session.add(school)
        db_session.commit()
        assert school.organization_type == "ymca"

    def test_repr_with_sub_level(self, db_session):
        school = School(
            name="Central MS",
            slug="central-ms-tx",
            level="high_school",
            sub_level="middle_school",
            state="TX",
        )
        assert "middle_school" in repr(school)

    def test_repr_without_sub_level(self, db_session):
        school = School(
            name="MIT",
            slug="mit",
            level="college",
            state="MA",
        )
        assert "college" in repr(school)
        assert "//" not in repr(school)


class TestCoachModel:
    def test_coach_has_sub_level_column(self, db_session):
        inspector = inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("coaches")}
        assert "sub_level" in columns

    def test_create_coach_with_sub_level(self, db_session):
        school = School(name="Test HS", slug="test-hs", level="high_school", sub_level="high_school", state="TX")
        db_session.add(school)
        db_session.commit()

        coach = Coach(
            email="coach@testschool.edu",
            email_hash="abc123",
            school_id=school.id,
            level="high_school",
            sub_level="high_school",
            state="TX",
            source_url="https://example.com",
        )
        db_session.add(coach)
        db_session.commit()
        assert coach.sub_level == "high_school"

    def test_coach_sub_level_nullable(self, db_session):
        school = School(name="College", slug="college-test", level="college", state="MA")
        db_session.add(school)
        db_session.commit()

        coach = Coach(
            email="prof@college.edu",
            email_hash="def456",
            school_id=school.id,
            level="college",
            state="MA",
            source_url="https://example.com",
        )
        db_session.add(coach)
        db_session.commit()
        assert coach.sub_level is None
