import logging

logger = logging.getLogger(__name__)


API_CHANGE_KEYWORDS: dict[str, list[str]] = {
    "DEPRECATION": [
        "deprecated",
        "deprecating",
        "deprecation",
        "sunset",
        "end of life",
        "eol",
        "discontinued",
    ],

    "VERSION_CHANGE": [
        "new api version",
        "api v2",
        "api v3",
        "api v4",
        "migrate",
        "migration",
        "upgrade api",
    ],

    "BREAKING_CHANGE": [
        "breaking change",
        "breaking changes",
        "no longer supported",
        "will stop working",
        "will no longer be available",
    ],

    "AUTH_CHANGE": [
        "oauth",
        "oauth2",
        "authentication",
        "authorization",
        "api key",
        "access token",
        "scope",
    ],

    "ENDPOINT_CHANGE": [
        "endpoint",
        "base url",
        "api url",
        "route",
    ],

    "RATE_LIMIT_CHANGE": [
        "rate limit",
        "rate limits",
        "requests per minute",
        "requests per second",
    ],
}


def detect_changes(
    subject: str,
    body: str,
) -> list[str]:
    text = f"{subject} {body}".lower()

    detected: list[str] = []

    for change_type, keywords in API_CHANGE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            detected.append(change_type)

    logger.info(
        "Rule detector found change types: %s",
        detected,
    )

    return detected