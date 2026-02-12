import re
import logging
import dns.resolver

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

# Known disposable email domains
DISPOSABLE_DOMAINS = frozenset({
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "yopmail.com", "sharklasers.com", "guerrillamailblock.com", "grr.la",
    "dispostable.com", "trashmail.com", "10minutemail.com",
})


def validate_email_format(email: str) -> bool:
    """Check if email matches basic RFC format."""
    return bool(_EMAIL_RE.match(email))


def is_disposable(email: str) -> bool:
    """Check if email uses a known disposable domain."""
    _, _, domain = email.partition("@")
    return domain.lower() in DISPOSABLE_DOMAINS


def check_mx_record(email: str) -> bool:
    """Verify that the email domain has valid MX records."""
    _, _, domain = email.partition("@")
    try:
        records = dns.resolver.resolve(domain, "MX")
        return len(records) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False
    except Exception:
        logger.warning(f"MX lookup failed for {domain}")
        return False


def validate_email(email: str, check_mx: bool = False) -> dict:
    """Full email validation.

    Returns: {valid, reason, is_disposable, has_mx}
    """
    result = {"valid": True, "reason": None, "is_disposable": False, "has_mx": None}

    if not validate_email_format(email):
        result["valid"] = False
        result["reason"] = "invalid_format"
        return result

    if is_disposable(email):
        result["is_disposable"] = True
        result["reason"] = "disposable_domain"

    if check_mx:
        result["has_mx"] = check_mx_record(email)
        if not result["has_mx"]:
            result["valid"] = False
            result["reason"] = "no_mx_record"

    return result
