import pytest
from pydantic import ValidationError

from app.api.v1.schemas.analyze import AnalyzeRequest, extract_handle


class TestExtractHandle:
    def test_x_com_url(self) -> None:
        assert extract_handle("https://x.com/testuser") == "testuser"

    def test_twitter_com_url(self) -> None:
        assert extract_handle("https://twitter.com/TestUser") == "testuser"

    def test_http_url(self) -> None:
        assert extract_handle("http://x.com/user123") == "user123"

    def test_trailing_slash(self) -> None:
        assert extract_handle("https://x.com/testuser/") == "testuser"

    def test_handle_lowercased(self) -> None:
        assert extract_handle("https://x.com/MyHandle") == "myhandle"

    def test_underscores_in_handle(self) -> None:
        assert extract_handle("https://x.com/my_user_123") == "my_user_123"

    def test_max_length_handle(self) -> None:
        handle = "a" * 15
        assert extract_handle(f"https://x.com/{handle}") == handle

    def test_invalid_domain(self) -> None:
        with pytest.raises(ValueError, match="Invalid Twitter/X URL"):
            extract_handle("https://facebook.com/user")

    def test_handle_too_long(self) -> None:
        handle = "a" * 16
        with pytest.raises(ValueError, match="Invalid Twitter/X URL"):
            extract_handle(f"https://x.com/{handle}")

    def test_empty_handle(self) -> None:
        with pytest.raises(ValueError, match="Invalid Twitter/X URL"):
            extract_handle("https://x.com/")

    def test_url_with_path(self) -> None:
        with pytest.raises(ValueError, match="Invalid Twitter/X URL"):
            extract_handle("https://x.com/user/status/123")

    def test_not_a_url(self) -> None:
        with pytest.raises(ValueError, match="Invalid Twitter/X URL"):
            extract_handle("not-a-url")

    def test_whitespace_stripped(self) -> None:
        assert extract_handle("  https://x.com/testuser  ") == "testuser"


class TestAnalyzeRequest:
    def test_valid_request(self) -> None:
        req = AnalyzeRequest(url="https://x.com/testuser")
        assert req.handle == "testuser"

    def test_invalid_url_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AnalyzeRequest(url="https://facebook.com/user")

    def test_handle_property(self) -> None:
        req = AnalyzeRequest(url="https://twitter.com/MyUser")
        assert req.handle == "myuser"
