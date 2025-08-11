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
            title="Important News",
            date="Month YYYY",
            content="Your news item here. Use **bold** for emphasis.",
            highlight=True
        ),
        news(
            title="Earlier News",
            date="Earlier Month YYYY", 
            content="Another news item with local file links.",
            highlight=False
        ),
        # Add more news items using news() helper...
    ]
)