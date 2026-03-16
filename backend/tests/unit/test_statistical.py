"""Tests for the statistical AI detection strategy (pure Python, no mocks)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.models.twitter import TweetData
from app.infrastructure.ml.analyzers.ai_content.statistical import StatisticalStrategy


def _make_tweets(texts: list[str]) -> list[TweetData]:
    return [
        TweetData(
            twitter_id=str(i),
            content=text,
            posted_at=datetime(2024, 6, 1, tzinfo=UTC) + timedelta(hours=i),
        )
        for i, text in enumerate(texts)
    ]


@pytest.fixture
def strategy():
    return StatisticalStrategy()


class TestStatisticalStrategy:
    async def test_name(self, strategy):
        assert strategy.name == "statistical"

    async def test_health_check(self, strategy):
        assert await strategy.health_check() is True

    async def test_empty_texts(self, strategy):
        result = await strategy.detect([], [])
        assert result.score == 0.0
        assert result.confidence == 0.1

    async def test_insufficient_tokens(self, strategy):
        texts = ["Bonjour"]
        tweets = _make_tweets(texts)
        result = await strategy.detect(texts, tweets)
        assert result.score == 0.0
        assert result.details["reason"] == "insufficient_tokens"

    async def test_returns_valid_result(self, strategy):
        texts = [
            "Ceci est un tweet normal avec du texte en français.",
            "Un autre tweet qui parle de quelque chose d'intéressant.",
            "Le troisième tweet pour avoir assez de données.",
            "Encore un tweet pour le quatrième signal.",
            "Et un cinquième tweet pour bonne mesure.",
        ]
        tweets = _make_tweets(texts)
        result = await strategy.detect(texts, tweets)

        assert 0 <= result.score <= 1
        assert 0 <= result.confidence <= 1
        assert "ttr" in result.details
        assert "sentence_uniformity" in result.details
        assert "punctuation_density" in result.details
        assert "burstiness" in result.details
        assert "char_entropy" in result.details

    async def test_confidence_low_for_few_tweets(self, strategy):
        texts = [
            "Tweet un avec du texte en français pour le test.",
            "Tweet deux avec du texte aussi pour tester.",
        ]
        tweets = _make_tweets(texts)
        result = await strategy.detect(texts, tweets)
        assert result.confidence == 0.15

    async def test_confidence_medium_for_moderate_tweets(self, strategy):
        texts = [f"Tweet numéro {i} avec du texte en français." for i in range(7)]
        tweets = _make_tweets(texts)
        result = await strategy.detect(texts, tweets)
        assert result.confidence == 0.5

    async def test_confidence_high_for_many_tweets(self, strategy):
        texts = [f"Tweet numéro {i} avec du texte en français." for i in range(15)]
        tweets = _make_tweets(texts)
        result = await strategy.detect(texts, tweets)
        assert result.confidence == 0.7


class TestTypeTokenRatio:
    def test_high_diversity(self):
        # All unique words → high TTR
        tokens = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
        score = StatisticalStrategy._type_token_ratio(tokens)
        assert score > 0.5

    def test_low_diversity(self):
        # Many repeated words → low TTR
        tokens = ["le", "le", "le", "le", "le", "le", "le", "le", "le", "le"]
        score = StatisticalStrategy._type_token_ratio(tokens)
        assert score < 0.3

    def test_empty(self):
        assert StatisticalStrategy._type_token_ratio([]) == 0.0


class TestSentenceUniformity:
    def test_uniform_lengths(self):
        # All sentences have similar word count → high uniformity → AI-like
        texts = [
            "Ceci est une phrase courte. Voici une autre phrase ici.",
            "Encore une phrase simple. Et une dernière aussi.",
        ]
        score = StatisticalStrategy._sentence_uniformity(texts)
        assert score > 0.3

    def test_varied_lengths(self):
        # Very different sentence lengths → low uniformity → human-like
        texts = [
            "Oui. "
            "Ceci est un paragraphe beaucoup plus long avec de nombreux mots "
            "qui forment une phrase complexe et détaillée.",
            "Non.",
        ]
        score = StatisticalStrategy._sentence_uniformity(texts)
        assert score < 0.7

    def test_too_few_sentences(self):
        texts = ["Un seul mot"]
        assert StatisticalStrategy._sentence_uniformity(texts) == 0.0


class TestPunctuationDensity:
    def test_empty(self):
        assert StatisticalStrategy._punctuation_density("") == 0.0

    def test_moderate_punctuation(self):
        # Normal text with moderate punctuation
        text = "Bonjour, comment allez-vous? Je vais bien, merci."
        score = StatisticalStrategy._punctuation_density(text)
        assert 0 <= score <= 1

    def test_no_punctuation(self):
        text = "Bonjour comment allez vous je vais bien merci"
        score = StatisticalStrategy._punctuation_density(text)
        assert score < 0.5


class TestBurstiness:
    def test_uniform_frequencies(self):
        # Each word appears same number of times → low burstiness → AI-like
        tokens = ["a", "b", "c", "d", "e"] * 4
        score = StatisticalStrategy._burstiness(tokens)
        assert score > 0.5

    def test_too_few_tokens(self):
        tokens = ["a", "b", "c"]
        assert StatisticalStrategy._burstiness(tokens) == 0.0


class TestCharEntropy:
    def test_empty(self):
        assert StatisticalStrategy._char_entropy("") == 0.0

    def test_single_char(self):
        # Single repeated character → zero entropy
        assert StatisticalStrategy._char_entropy("aaaaaaaaaa") == 0.0

    def test_normal_text(self):
        text = "Ceci est un texte normal en français avec des caractères variés."
        score = StatisticalStrategy._char_entropy(text)
        assert 0 <= score <= 1
