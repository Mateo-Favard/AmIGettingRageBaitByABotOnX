from fastapi import APIRouter, Depends, Request

from app.api.v1.schemas.analyze import (
    AnalyzeRequest,
    AnalyzeResponse,
    ProfileSummary,
    ScoreBreakdown,
)
from app.core.security import limiter
from app.dependencies import get_analysis_service
from app.domain.services.analysis import AnalysisService

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_account(
    request: Request,
    body: AnalyzeRequest,
    force: bool = False,
    service: AnalysisService = Depends(get_analysis_service),  # noqa: B008
) -> AnalyzeResponse:
    handle = body.handle
    result, cached = await service.analyze(handle, force=force)

    profile = await service._twitter.fetch_profile(handle)

    return AnalyzeResponse(
        handle=result.handle,
        composite_score=result.composite_score,
        scores=ScoreBreakdown(
            ai_content_score=result.ai_content_score,
            behavioral_score=result.behavioral_score,
            sentiment_score=result.sentiment_score,
            opportunism_score=result.opportunism_score,
        ),
        profile=ProfileSummary(
            handle=profile.handle,
            display_name=profile.display_name,
            bio=profile.bio,
            followers_count=profile.followers_count,
            following_count=profile.following_count,
            tweets_count=profile.tweets_count,
            profile_image_url=profile.profile_image_url,
            account_created_at=profile.account_created_at,
        ),
        analyzed_at=result.analyzed_at,
        cached=cached,
    )
