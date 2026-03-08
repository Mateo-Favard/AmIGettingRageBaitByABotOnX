from app.core.exceptions import (
    AnalysisError,
    AppError,
    ExternalServiceError,
    MLPipelineError,
    NotFoundError,
    RateLimitError,
    TwitterAPIError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_validation_error(self) -> None:
        exc = ValidationError("bad input")
        assert exc.status_code == 400
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.message == "bad input"

    def test_not_found_error(self) -> None:
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"

    def test_rate_limit_error(self) -> None:
        exc = RateLimitError()
        assert exc.status_code == 429

    def test_external_service_error(self) -> None:
        exc = ExternalServiceError("timeout")
        assert exc.status_code == 502

    def test_twitter_api_error_inherits(self) -> None:
        exc = TwitterAPIError("rate limited by Twitter")
        assert isinstance(exc, ExternalServiceError)
        assert isinstance(exc, AppError)
        assert exc.status_code == 502

    def test_ml_pipeline_error_inherits(self) -> None:
        exc = MLPipelineError("model crashed")
        assert isinstance(exc, AnalysisError)
        assert isinstance(exc, AppError)
        assert exc.status_code == 500

    def test_default_messages(self) -> None:
        assert ValidationError().message == "Invalid input"
        assert NotFoundError().message == "Resource not found"
        assert RateLimitError().message == "Too many requests"

    def test_custom_details(self) -> None:
        exc = ValidationError("bad url", field="url", value="not-a-url")
        assert exc.details == {"field": "url", "value": "not-a-url"}
