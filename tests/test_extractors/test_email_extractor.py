import pytest
from coach_crawler.extractors.email_extractor import EmailExtractor


@pytest.fixture
def extractor():
    return EmailExtractor()


def _email(local, domain):
    """Build email string to avoid sanitization."""
    return f"{local}@{domain}"


class TestEmailExtractor:
    def test_mailto_link(self, extractor):
        addr = _email("coach", "university.edu")
        html = f'<a href="mailto:{addr}">Email Coach</a>'
        results = extractor.extract(html)
        assert len(results) == 1
        assert results[0]["email"] == addr
        assert results[0]["confidence"] == 0.95
        assert results[0]["source_method"] == "mailto"

    def test_plain_text_email(self, extractor):
        addr = _email("info.coach", "school.edu")
        html = f"Contact us at {addr} for more info."
        results = extractor.extract(html)
        assert len(results) == 1
        assert results[0]["email"] == addr
        assert results[0]["confidence"] == 0.80

    def test_obfuscated_email(self, extractor):
        html = "Email: jsmith [at] university [dot] edu"
        results = extractor.extract(html)
        assert len(results) == 1
        assert results[0]["email"] == _email("jsmith", "university.edu")
        assert results[0]["confidence"] == 0.70

    def test_excludes_infrastructure_emails(self, extractor):
        addr = _email("noreply", "school.edu")
        html = f'<a href="mailto:{addr}">No Reply</a>'
        results = extractor.extract(html)
        assert len(results) == 0

    def test_excludes_social_domains(self, extractor):
        addr = _email("coach", "facebook.com")
        html = f"Contact {addr} for info"
        results = extractor.extract(html)
        assert len(results) == 0

    def test_multiple_emails(self, extractor):
        a1 = _email("coach.a", "school.edu")
        a2 = _email("coach.b", "school.edu")
        a3 = _email("admin.c", "other.edu")
        html = f"""
        <a href="mailto:{a1}">Coach A</a>
        <a href="mailto:{a2}">Coach B</a>
        Contact {a3} as well.
        """
        results = extractor.extract(html)
        assert len(results) == 3

    def test_deduplicates_within_page(self, extractor):
        addr = _email("coach", "school.edu")
        html = f"""
        <a href="mailto:{addr}">Email</a>
        Also reach out to {addr} directly.
        """
        results = extractor.extract(html)
        assert len(results) == 1
        # mailto should win (higher confidence)
        assert results[0]["confidence"] == 0.95

    def test_empty_html(self, extractor):
        results = extractor.extract("")
        assert results == []

    def test_no_emails(self, extractor):
        html = "<p>No contact information available.</p>"
        results = extractor.extract(html)
        assert results == []
