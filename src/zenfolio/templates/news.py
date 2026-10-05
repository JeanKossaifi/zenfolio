#!/usr/bin/env python3
"""News for your website."""

from zenfolio.models import NewsConfig, NewsEntryConfig

news_config = NewsConfig(
    news=[
        NewsEntryConfig(
            content="**Important news**: your news item here. Use **bold** for emphasis.",
            date="2026-05",
            highlight=True
        ),
        NewsEntryConfig(
            content="Another news item, optionally with a link.",
            date="2026-04",
            website="https://example.com/details",
            highlight=False
        ),
        # Add more news here.
    ]
)
