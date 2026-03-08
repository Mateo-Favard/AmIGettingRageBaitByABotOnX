from httpx import AsyncClient


class TestAnalyzeEndpoint:
    async def test_analyze_valid_url(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/analyze",
            json={"url": "https://x.com/devweb_alex"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["handle"] == "devweb_alex"
        assert 0 <= data["composite_score"] <= 100
        assert data["cached"] is False
        assert "scores" in data
        assert "profile" in data

    async def test_analyze_returns_profile(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/analyze",
            json={"url": "https://x.com/devweb_alex"},
        )
        data = response.json()
        profile = data["profile"]
        assert profile["handle"] == "devweb_alex"
        assert profile["display_name"] == "Alex Martin"
        assert profile["followers_count"] == 3_200

    async def test_analyze_suspect_user(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/analyze",
            json={"url": "https://x.com/suspect_bot42"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["handle"] == "suspect_bot42"
        assert data["composite_score"] > 0

    async def test_analyze_invalid_url(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/analyze",
            json={"url": "https://facebook.com/user"},
        )
        assert response.status_code == 422

    async def test_analyze_missing_url(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/analyze", json={})
        assert response.status_code == 422

    async def test_analyze_cached_second_call(self, client: AsyncClient) -> None:
        r1 = await client.post(
            "/api/v1/analyze",
            json={"url": "https://x.com/devweb_alex"},
        )
        assert r1.status_code == 200, r1.json()
        response = await client.post(
            "/api/v1/analyze",
            json={"url": "https://x.com/devweb_alex"},
        )
        assert response.status_code == 200, response.json()
        data = response.json()
        assert data["cached"] is True

    async def test_analyze_force_bypasses_cache(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/analyze",
            json={"url": "https://x.com/devweb_alex"},
        )
        response = await client.post(
            "/api/v1/analyze?force=true",
            json={"url": "https://x.com/devweb_alex"},
        )
        data = response.json()
        assert data["cached"] is False

    async def test_analyze_twitter_com_url(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/analyze",
            json={"url": "https://twitter.com/devweb_alex"},
        )
        assert response.status_code == 200
        assert response.json()["handle"] == "devweb_alex"
