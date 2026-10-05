#!/usr/bin/env python3
"""Talks for your website."""

from zenfolio.models import TalksConfig, TalkConfig

# Local file paths are relative to the static/ directory.

talks_config = TalksConfig(
    # Cache missing YouTube thumbnails during `zenfolio build`.
    cache_video_thumbnails=True,
    talks=[
        TalkConfig(
            title="Your Talk Title",
            # Use YYYY, YYYY-MM, or YYYY-MM-DD for dates.
            date="2026-05-05",
            venue="Conference/Workshop Name",
            type="Keynote",  # e.g., "Keynote", "Tutorial", "Panel", "Invited Talk"
            description="Brief description of your talk.",
            # Links can be URLs or local files in static/ directory
            slides="talks/keynote_slides.pdf",         # Local PDF in static/talks/
            video="https://youtube.com/watch?v=example", # YouTube URL
            materials="talks/supplementary.zip",       # Local materials
            code="https://github.com/username/talk-code", # GitHub repo
        ),
        TalkConfig(
            title="Another Talk",
            date="2025-11",
            venue="Workshop Name",
            type="Invited Talk",
            description="Description of another presentation.",
            slides="https://speakerdeck.com/username/slides", # External slides
            demo="demos/interactive_demo.html",        # Local demo file
        ),
        # Add more talks here.
    ]
)
