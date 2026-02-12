import re
from urllib.parse import urlparse, urljoin


def normalize_url(url: str) -> str:
    """Normalize a URL for consistent comparison."""
    parsed = urlparse(url)
    # Ensure scheme
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    # Remove trailing slash from path
    path = parsed.path.rstrip("/") or "/"
    # Remove common tracking parameters
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def get_domain(url: str) -> str:
    """Extract the domain from a URL."""
    return urlparse(url).netloc.lower()


def make_slug(name: str) -> str:
    """Convert a school/organization name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')
