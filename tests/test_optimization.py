"""Tests for optimization modules."""

from __future__ import annotations

import pytest

from clipforge.media_ranker import CachedMediaRanker, MediaRanker, MediaScore
from clipforge.subtitle_engine import AdvancedSubtitleEngine
from clipforge.duration_optimizer import SceneDurationOptimizer
from clipforge.analytics_optimizer import PerformanceAnalyzer, VideoMetrics
from datetime import datetime


class TestMediaRanker:
    """Test media ranking system."""

    def test_media_score_calculation(self) -> None:
        """Test media score weighting."""
        score = MediaScore(
            relevance=0.9,
            color_harmony=0.8,
            resolution_fit=0.7,
            popularity=0.6,
        )
        score.calculate(w_relevance=0.4, w_harmony=0.2, w_fit=0.2, w_pop=0.2)

        expected = 0.9 * 0.4 + 0.8 * 0.2 + 0.7 * 0.2 + 0.6 * 0.2
        assert abs(score.final_score - expected) < 0.01

    def test_relevance_scoring(self) -> None:
        """Test keyword relevance scoring."""
        ranker = MediaRanker()

        media = {
            "title": "Technology and AI",
            "description": "Modern computer systems",
        }
        keywords = ["technology", "ai"]

        score = ranker._score_relevance(media, keywords)
        assert score > 0.5  # Should match keywords

    def test_aspect_ratio_scoring(self) -> None:
        """Test aspect ratio fit scoring."""
        ranker = MediaRanker()

        # Perfect fit
        media_perfect = {"width": 1080, "height": 1920}  # 9:16
        score_perfect = ranker._score_aspect_ratio(media_perfect, (9, 16))
        assert score_perfect > 0.9

        # Poor fit
        media_poor = {"width": 1920, "height": 1080}  # 16:9
        score_poor = ranker._score_aspect_ratio(media_poor, (9, 16))
        assert score_poor < 0.5

    def test_color_distance(self) -> None:
        """Test color distance calculation."""
        ranker = MediaRanker()

        # Same color
        dist_same = ranker._color_distance((255, 0, 0), (255, 0, 0))
        assert dist_same == 0.0

        # Different color
        dist_diff = ranker._color_distance((255, 0, 0), (0, 0, 255))
        assert dist_diff > 100

    def test_score_media_ranking(self) -> None:
        """Test full media ranking pipeline."""
        ranker = MediaRanker()

        media_list = [
            {
                "title": "Technology",
                "description": "AI systems",
                "width": 1080,
                "height": 1920,
                "views": 1000000,
            },
            {
                "title": "Random video",
                "description": "No keywords",
                "width": 1920,
                "height": 1080,
                "views": 100,
            },
        ]

        scored = ranker.score_media(media_list, ["technology", "ai"])

        # First should rank higher
        assert scored[0][1].final_score > scored[1][1].final_score


class TestAdvancedSubtitleEngine:
    """Test subtitle animation engine."""

    def test_auto_text_color_detection(self) -> None:
        """Test auto text color selection."""
        engine = AdvancedSubtitleEngine()

        # Light background → black text
        dark_bg = (200, 200, 200)
        text_color = engine.auto_detect_text_color(dark_bg)
        assert text_color == (0, 0, 0)

        # Dark background → white text
        light_bg = (50, 50, 50)
        text_color = engine.auto_detect_text_color(light_bg)
        assert text_color == (255, 255, 255)

    def test_typewriter_frames_generation(self) -> None:
        """Test typewriter animation frame generation."""
        engine = AdvancedSubtitleEngine()

        frames = engine.generate_typewriter_frames(
            text="Hello",
            start_time=0.0,
            duration=2.5,
        )

        assert len(frames) == 5  # One per character
        assert frames[0].text == "H"
        assert frames[-1].text == "Hello"

    def test_word_by_word_frames_generation(self) -> None:
        """Test word-by-word animation frame generation."""
        engine = AdvancedSubtitleEngine()

        frames = engine.generate_word_by_word_frames(
            text="Hello world test",
            start_time=0.0,
            duration=3.0,
        )

        assert len(frames) == 3  # Three words
        assert frames[0].text == "Hello"
        assert frames[1].text == "Hello world"
        assert frames[2].text == "Hello world test"

    def test_font_size_optimization(self) -> None:
        """Test dynamic font size optimization."""
        engine = AdvancedSubtitleEngine()

        # Short text → full size
        size_short = engine.optimize_font_size("Hi", base_size=48)
        assert size_short == 48

        # Medium text → reduced size
        size_medium = engine.optimize_font_size("This is a medium length text string", base_size=48)
        assert size_medium < 48

        # Long text → much reduced
        size_long = engine.optimize_font_size("A" * 60, base_size=48)
        assert size_long < size_medium

    def test_position_optimization(self) -> None:
        """Test optimal subtitle positioning."""
        engine = AdvancedSubtitleEngine()

        # Short impact text
        pos = engine.optimize_position("Wow!")
        assert pos == "center"

        # Long narration
        pos = engine.optimize_position("This is a long narrative about something interesting")
        assert pos == "bottom"


class TestSceneDurationOptimizer:
    """Test scene duration optimization."""

    def test_sentence_counting(self) -> None:
        """Test sentence counting."""
        optimizer = SceneDurationOptimizer()

        count = optimizer._count_sentences("First. Second! Third?")
        assert count >= 3

    def test_complexity_calculation(self) -> None:
        """Test text complexity scoring."""
        optimizer = SceneDurationOptimizer()

        # Simple text
        simple = "Hello world."
        complexity_simple = optimizer._calculate_complexity(simple)

        # Complex text
        complex_text = "Notwithstanding the aforementioned considerations regarding algorithmic optimization."
        complexity_complex = optimizer._calculate_complexity(complex_text)

        assert complexity_complex > complexity_simple

    def test_base_duration_calculation(self) -> None:
        """Test base duration calculation from metrics."""
        optimizer = SceneDurationOptimizer()

        # 100 words at 2.5 wps + pauses
        duration = optimizer._calculate_base_duration(
            word_count=100, reading_speed=2.5, pause_count=5, sentence_count=5
        )

        assert 30 < duration < 50  # Should be around 40-45 seconds

    def test_analyze_scene(self) -> None:
        """Test full scene analysis."""
        optimizer = SceneDurationOptimizer()

        scene = {
            "text": "Hello world. This is a test. How are you?",
            "keywords": ["greeting", "test"],
            "content_type": "conversational",
        }

        metrics = optimizer.analyze_scene(scene)

        assert metrics.word_count > 0
        assert metrics.reading_speed > 0
        assert metrics.recommended_duration > 0

    def test_music_tempo_sync(self) -> None:
        """Test scene duration syncing with music."""
        optimizer = SceneDurationOptimizer()

        # 120 BPM, 4 beats per measure = 8 beats = 4 seconds
        synced = optimizer.sync_with_music_tempo(
            scene_duration=3.5, music_bpm=120, music_beats_per_measure=4
        )

        # Should snap to nearest musical phrase
        assert 2.0 <= synced <= 15.0


class TestPerformanceAnalyzer:
    """Test analytics and performance optimizer."""

    def test_engagement_rate_calculation(self) -> None:
        """Test engagement rate formula."""
        analyzer = PerformanceAnalyzer()

        metrics = VideoMetrics(
            video_id="test",
            platform="reels",
            upload_time=datetime.now(),
            duration=30.0,
            views=1000,
            likes=50,
            comments=10,
            shares=5,
        )

        engagement = analyzer.calculate_engagement_rate(metrics)
        expected = (50 + 10 * 5 + 5 * 10) / 1000
        assert abs(engagement - expected) < 0.001

    def test_retention_curve_analysis(self) -> None:
        """Test retention curve analysis."""
        analyzer = PerformanceAnalyzer()

        metrics = VideoMetrics(
            video_id="test",
            platform="reels",
            upload_time=datetime.now(),
            duration=30.0,
            retention_curve=[(0.0, 1.0), (0.25, 0.8), (0.5, 0.6), (0.75, 0.4), (1.0, 0.3)],
        )

        analysis = analyzer.analyze_retention_curve(metrics)

        assert "drop_at" in analysis
        assert "final_retention" in analysis
        assert 0.0 <= analysis["final_retention"] <= 1.0

    def test_optimal_duration_recommendation(self) -> None:
        """Test optimal video length recommendation."""
        analyzer = PerformanceAnalyzer()

        metrics_list = [
            VideoMetrics(
                video_id=f"v{i}",
                platform="reels",
                upload_time=datetime.now(),
                duration=15.0 + (i * 5),
                views=1000 + (i * 100),
                likes=max(0, 50 - (i * 2)),  # Engagement decreases with length
            )
            for i in range(5)
        ]

        recommendations = analyzer.recommend_optimal_duration(metrics_list)

        assert "all" in recommendations
        assert "shorts" in recommendations
        assert recommendations["all"] > 0

    def test_publishing_time_recommendation(self) -> None:
        """Test publishing time recommendation."""
        analyzer = PerformanceAnalyzer()

        metrics_list = [
            VideoMetrics(
                video_id=f"v{i}",
                platform="reels",
                upload_time=datetime(2024, 1, 1, 10 + i),  # Different hours
                duration=30.0,
                views=1000,
                likes=50 + (i * 5),
            )
            for i in range(3)
        ]

        recommendation = analyzer.recommend_publishing_time(metrics_list)
        assert ":" in recommendation  # Should have hour:minute format

    def test_ab_test_comparison(self) -> None:
        """Test A/B test comparison."""
        analyzer = PerformanceAnalyzer()

        variant_a = [
            VideoMetrics(
                video_id="a1",
                platform="reels",
                upload_time=datetime.now(),
                duration=30.0,
                views=1000,
                likes=100,
            )
        ]

        variant_b = [
            VideoMetrics(
                video_id="b1",
                platform="reels",
                upload_time=datetime.now(),
                duration=30.0,
                views=1000,
                likes=50,
            )
        ]

        comparison = analyzer.generate_ab_test_comparison(variant_a, variant_b)

        assert "winner" in comparison
        assert comparison["winner"] in ["A", "B", "N/A"]
        assert "confidence" in comparison
