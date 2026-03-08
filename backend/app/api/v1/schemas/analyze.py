import re
from datetime import datetime

from pydantic import BaseModel, field_validator

_TWITTER_URL_RE = re.compile(r"^https?://(twitter\.com|x\.com)/([a-zA-Z0-9_]{1,15})/?$")


def extract_handle(url: str) -> str:
    """Extract and lowercase the Twitter handle from a URL."""
    match = _TWITTER_URL_RE.match(url.strip())
    if not match:
        msg = (
            "Invalid Twitter/X URL. "
            "Expected format: https://x.com/username or https://twitter.com/username"
        )
        raise ValueError(msg)
    return match.group(2).lower()


class AnalyzeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_twitter_url(cls, v: str) -> str:
        v = v.strip()
        extract_handle(v)  # raises ValueError if invalid
        return v

    @property
    def handle(self) -> str:
        return extract_handle(self.url)


class ScoreBreakdown(BaseModel):
    ai_content_score: float | None = None
    behavioral_score: float | None = None
    sentiment_score: float | None = None
    opportunism_score: float | None = None


class ProfileSummary(BaseModel):
    handle: str
    display_name: str
    bio: str
    followers_count: int
    following_count: int
    tweets_count: int
    profile_image_url: str = ""
    account_created_at: datetime | None = None


class AnalyzeResponse(BaseModel):
    handle: str
    composite_score: float
    scores: ScoreBreakdown
    profile: ProfileSummary
    analyzed_at: datetime
    cached: bool
