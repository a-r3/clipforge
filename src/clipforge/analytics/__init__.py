"""ClipForge analytics package.

Collects, stores, and aggregates performance metrics for published content.

Quick start::

    from clipforge.analytics.models import ContentAnalytics
    from clipforge.analytics.storage import AnalyticsStore
    from clipforge.analytics.factory import AnalyticsCollectorFactory

    store = AnalyticsStore("./analytics_store")
    collector = AnalyticsCollectorFactory.for_platform("youtube")
    record = collector.fetch(manifest)
    store.save(record)

    summary = store.summary()
"""
from clipforge.analytics.models import ContentAnalytics

__all__ = ["ContentAnalytics"]
