"""Advanced analytics framework for performance optimization.

Tracks:
- Engagement metrics
- Retention curves
- Optimal video length
- Publishing time recommendations
- A/B test comparisons
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VideoMetrics:
    """Performance metrics for a published video."""

    video_id: str
    platform: str
    upload_time: datetime
    duration: float
    topics: list[str] = field(default_factory=list)
    
    # Engagement
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    
    # Retention
    average_watch_percentage: float = 0.0
    retention_curve: list[tuple[float, float]] = field(
        default_factory=list
    )  # [(time%, watch%)]
    
    # Derived
    engagement_rate: float = 0.0
    ctr: float = 0.0  # Click-through rate if applicable


@dataclass
class InsightCluster:
    """Grouped insight from multiple videos."""

    name: str
    metrics: list[VideoMetrics] = field(default_factory=list)
    average_engagement: float = 0.0
    average_retention: float = 0.0
    optimal_duration: float = 0.0
    recommendations: list[str] = field(default_factory=list)


class PerformanceAnalyzer:
    """Analyze video performance and generate insights."""

    def __init__(self, cache_dir: str | Path = "data/analytics") -> None:
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def calculate_engagement_rate(self, metrics: VideoMetrics) -> float:
        """Calculate engagement rate (0-1).

        (likes + comments + shares) / views
        """
        if metrics.views == 0:
            return 0.0

        engagement = metrics.likes + metrics.comments * 5 + metrics.shares * 10
        return engagement / metrics.views

    def analyze_retention_curve(self, metrics: VideoMetrics) -> dict[str, Any]:
        """Analyze retention pattern from curve.

        Returns:
            {
                "drop_at": float (0-1),  # Where biggest drop occurs
                "final_retention": float,
                "consistency": float,  # How smooth the curve is
                "drop_severity": float,  # How steep the biggest drop
            }
        """
        if not metrics.retention_curve or len(metrics.retention_curve) < 2:
            return {
                "drop_at": 0.0,
                "final_retention": 0.0,
                "consistency": 1.0,
                "drop_severity": 0.0,
            }

        curve = sorted(metrics.retention_curve)
        time_points = [t for t, _ in curve]
        watch_points = [w for _, w in curve]

        # Find biggest drop
        max_drop = 0.0
        max_drop_at = 0.0

        for i in range(len(watch_points) - 1):
            drop = watch_points[i] - watch_points[i + 1]
            if drop > max_drop:
                max_drop = drop
                max_drop_at = time_points[i]

        # Calculate consistency (variance in retention)
        avg_watch = sum(watch_points) / len(watch_points)
        variance = sum((w - avg_watch) ** 2 for w in watch_points) / len(watch_points)
        consistency = max(0.0, 1.0 - (variance / avg_watch if avg_watch > 0 else 0))

        return {
            "drop_at": max_drop_at,
            "final_retention": watch_points[-1],
            "consistency": min(1.0, consistency),
            "drop_severity": max_drop,
        }

    def cluster_by_topic(self, metrics_list: list[VideoMetrics]) -> dict[str, InsightCluster]:
        """Group videos by topic and analyze patterns."""
        clusters: dict[str, InsightCluster] = {}

        for metrics in metrics_list:
            for topic in metrics.topics:
                if topic not in clusters:
                    clusters[topic] = InsightCluster(name=topic)

                clusters[topic].metrics.append(metrics)

        # Compute cluster statistics
        for cluster in clusters.values():
            self._compute_cluster_stats(cluster)

        return clusters

    def recommend_optimal_duration(self, metrics_list: list[VideoMetrics]) -> dict[str, float]:
        """Recommend optimal video lengths by topic/platform.

        Returns:
            {
                "all": optimal_length,
                "shorts": optimal_shorts_length,
                "long_form": optimal_long_form,
                "by_topic": {"topic_name": optimal_length, ...}
            }
        """
        if not metrics_list:
            return {"all": 30.0, "shorts": 15.0, "long_form": 300.0}

        # Group by duration quartiles and measure engagement
        sorted_by_duration = sorted(metrics_list, key=lambda m: m.duration)
        quartile_size = max(1, len(sorted_by_duration) // 4)

        best_engagement = 0.0
        optimal_duration = 30.0

        for i in range(4):
            start_idx = i * quartile_size
            end_idx = start_idx + quartile_size
            quartile = sorted_by_duration[start_idx:end_idx]

            if not quartile:
                continue

            avg_engagement = sum(
                self.calculate_engagement_rate(m) for m in quartile
            ) / len(quartile)

            if avg_engagement > best_engagement:
                best_engagement = avg_engagement
                # Use middle of quartile as optimal
                optimal_duration = sum(m.duration for m in quartile) / len(quartile)

        # Platform-specific recommendations
        shorts = [m for m in metrics_list if m.platform in ["reels", "tiktok", "shorts"]]
        long_form = [m for m in metrics_list if m.platform in ["youtube"]]

        return {
            "all": optimal_duration,
            "shorts": self._quartile_optimal(shorts) if shorts else 15.0,
            "long_form": self._quartile_optimal(long_form) if long_form else 300.0,
        }

    def recommend_publishing_time(self, metrics_list: list[VideoMetrics]) -> str:
        """Recommend best time to publish based on historical data.

        Simplified: returns day and hour with best performance.
        """
        if not metrics_list:
            return "Wednesday 10:00 AM UTC"

        # Group by day-of-week and hour
        hour_performance: dict[int, list[float]] = {}

        for metrics in metrics_list:
            hour = metrics.upload_time.hour
            engagement = self.calculate_engagement_rate(metrics)

            if hour not in hour_performance:
                hour_performance[hour] = []

            hour_performance[hour].append(engagement)

        # Find best hour
        best_hour = 10  # Default
        best_avg = 0.0

        for hour, engagements in hour_performance.items():
            avg = sum(engagements) / len(engagements)
            if avg > best_avg:
                best_avg = avg
                best_hour = hour

        # Simplified day recommendation (in production: analyze day patterns)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        best_day = days[2]  # Wednesday often good for engagement

        return f"{best_day} {best_hour:02d}:00 UTC"

    def generate_ab_test_comparison(
        self,
        variant_a: list[VideoMetrics],
        variant_b: list[VideoMetrics],
    ) -> dict[str, Any]:
        """Compare performance between two variants (e.g., different thumbnails).

        Returns:
            {
                "winner": "A" | "B",
                "confidence": 0.0-1.0,
                "engagement_diff": float,
                "retention_diff": float,
                "statistical_significance": bool,
            }
        """
        if not variant_a or not variant_b:
            return {
                "winner": "N/A",
                "confidence": 0.0,
                "engagement_diff": 0.0,
                "retention_diff": 0.0,
            }

        avg_engagement_a = sum(
            self.calculate_engagement_rate(m) for m in variant_a
        ) / len(variant_a)
        avg_engagement_b = sum(
            self.calculate_engagement_rate(m) for m in variant_b
        ) / len(variant_b)

        avg_retention_a = sum(m.average_watch_percentage for m in variant_a) / len(variant_a)
        avg_retention_b = sum(m.average_watch_percentage for m in variant_b) / len(variant_b)

        engagement_diff = avg_engagement_a - avg_engagement_b
        retention_diff = avg_retention_a - avg_retention_b

        winner = "A" if engagement_diff > 0 else "B"

        # Simplified significance test (in production: use Chi-square or T-test)
        diff_magnitude = abs(engagement_diff)
        confidence = min(1.0, diff_magnitude * 100)

        return {
            "winner": winner,
            "confidence": confidence,
            "engagement_diff": engagement_diff,
            "retention_diff": retention_diff,
            "variant_a_engagement": avg_engagement_a,
            "variant_b_engagement": avg_engagement_b,
            "statistical_significance": confidence > 0.8,
        }

    # =====================================================================
    # Private helpers
    # =====================================================================

    def _compute_cluster_stats(self, cluster: InsightCluster) -> None:
        """Compute aggregated statistics for a cluster."""
        if not cluster.metrics:
            return

        engagements = [self.calculate_engagement_rate(m) for m in cluster.metrics]
        retentions = [m.average_watch_percentage for m in cluster.metrics]

        cluster.average_engagement = sum(engagements) / len(engagements) if engagements else 0.0
        cluster.average_retention = sum(retentions) / len(retentions) if retentions else 0.0

        durations = [m.duration for m in cluster.metrics]
        cluster.optimal_duration = sum(durations) / len(durations) if durations else 30.0

        # Generate recommendations
        self._generate_cluster_recommendations(cluster)

    def _generate_cluster_recommendations(self, cluster: InsightCluster) -> None:
        """Generate insights and recommendations for a cluster."""
        cluster.recommendations = []

        if cluster.average_engagement < 0.01:
            cluster.recommendations.append(
                f"Low engagement for {cluster.name}. Consider different hook or thumbnail."
            )

        if cluster.average_retention < 0.3:
            cluster.recommendations.append(
                f"Watch retention drops fast. Improve pacing or add visual variety."
            )

        if cluster.optimal_duration > 60:
            cluster.recommendations.append(
                f"Videos in {cluster.name} perform best at ~{cluster.optimal_duration:.0f}s. "
                "Consider breaking longer content into series."
            )

        if cluster.average_engagement > 0.05:
            cluster.recommendations.append(
                f"Strong engagement in {cluster.name}! Keep creating this type of content."
            )

    @staticmethod
    def _quartile_optimal(metrics_list: list[VideoMetrics]) -> float:
        """Find optimal duration using quartile method."""
        if not metrics_list:
            return 30.0

        sorted_by_duration = sorted(metrics_list, key=lambda m: m.duration)
        quartile_size = max(1, len(sorted_by_duration) // 4)

        best_engagement = 0.0
        optimal_duration = 30.0

        for i in range(4):
            start_idx = i * quartile_size
            end_idx = start_idx + quartile_size
            quartile = sorted_by_duration[start_idx:end_idx]

            if not quartile:
                continue

            # Calculate engagement rate for each video in quartile
            engagements = []
            for m in quartile:
                if m.views > 0:
                    engagement = (m.likes + m.comments + m.shares) / m.views
                    engagements.append(engagement)
            
            if not engagements:
                continue

            avg_engagement = sum(engagements) / len(engagements)

            if avg_engagement > best_engagement:
                best_engagement = avg_engagement
                optimal_duration = sum(m.duration for m in quartile) / len(quartile)

        return optimal_duration
