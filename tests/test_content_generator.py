"""Tests for content generation with validation (mocked Gemini)."""

import pytest
from unittest.mock import patch
from src.generation.content_generator import generate_dinosaur_content


class TestGenerateDinosaurContent:
    """Tests for generate_dinosaur_content() validation logic."""

    def _mock_generate(self, content):
        """Return a patcher that makes generate_dinosaur_article return `content`."""
        return patch(
            "src.generation.content_generator.generate_dinosaur_article",
            return_value=content,
        )

    def test_valid_content_passes(self, sample_content):
        with self._mock_generate(sample_content):
            result = generate_dinosaur_content("trex")
            assert result["article"] == sample_content["article"]
            assert result["social_snippet"] == sample_content["social_snippet"]
            assert result["hashtags"] == sample_content["hashtags"]

    def test_missing_article_field_raises(self, sample_content):
        bad = {k: v for k, v in sample_content.items() if k != "article"}
        with self._mock_generate(bad):
            with pytest.raises(AssertionError, match="article"):
                generate_dinosaur_content("trex")

    def test_missing_social_snippet_raises(self, sample_content):
        bad = {k: v for k, v in sample_content.items() if k != "social_snippet"}
        with self._mock_generate(bad):
            with pytest.raises(AssertionError, match="social_snippet"):
                generate_dinosaur_content("trex")

    def test_missing_hashtags_raises(self, sample_content):
        bad = {k: v for k, v in sample_content.items() if k != "hashtags"}
        with self._mock_generate(bad):
            with pytest.raises(AssertionError, match="hashtags"):
                generate_dinosaur_content("trex")

    def test_article_too_short_logs_warning(self, sample_content):
        sample_content["article"] = "A" * 100  # way below 3000
        with self._mock_generate(sample_content):
            result = generate_dinosaur_content("trex")
            assert len(result["article"]) == 100

    def test_article_too_long_logs_warning(self, sample_content):
        sample_content["article"] = "A" * 15000  # above 10000
        with self._mock_generate(sample_content):
            result = generate_dinosaur_content("trex")
            assert len(result["article"]) == 15000

    def test_snippet_too_short_logs_warning(self, sample_content):
        sample_content["social_snippet"] = "B" * 10  # below 100
        with self._mock_generate(sample_content):
            result = generate_dinosaur_content("trex")
            assert len(result["social_snippet"]) == 10

    def test_snippet_too_long_truncates(self, sample_content):
        sample_content["social_snippet"] = "B" * 300  # above 250
        with self._mock_generate(sample_content):
            result = generate_dinosaur_content("trex")
            assert len(result["social_snippet"]) == 250
            assert result["social_snippet"].endswith("...")

    def test_too_few_hashtags_passes(self, sample_content):
        sample_content["hashtags"] = ["#one", "#two"]
        with self._mock_generate(sample_content):
            result = generate_dinosaur_content("trex")
            assert len(result["hashtags"]) == 2

    def test_too_many_hashtags_truncates(self, sample_content):
        sample_content["hashtags"] = [f"#tag{i}" for i in range(15)]  # above 10
        with self._mock_generate(sample_content):
            result = generate_dinosaur_content("trex")
            assert len(result["hashtags"]) == 10

    def test_hashtags_not_list_parses(self, sample_content):
        sample_content["hashtags"] = "#dino #trex"  # string, not list
        with self._mock_generate(sample_content):
            result = generate_dinosaur_content("trex")
            assert result["hashtags"] == ["#dino", "#trex"]
