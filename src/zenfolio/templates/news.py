#!/usr/bin/env python3
"""
News content for your academic website
"""

from zenfolio.models import NewsConfig
from zenfolio.templates import news
# Simple strings for paths - ZenFolio handles smart resolution

news_config = NewsConfig(
    items=[
        news(
            content="**Important news**: your news item here. Use **bold** for emphasis.",
            date="Month YYYY",
            highlight=True
        ),
        news(
            content="Another news item, optionally with a link.",
            date="Earlier Month YYYY",
            url="https://example.com/details",
            highlight=False
        ),
        # Add more news items using the news() helper...
    ]
)
