#!/usr/bin/env python3
"""
Talks content for your academic website
"""

from zenfolio.models import TalksConfig, TalkItem
# Simple strings for paths - ZenFolio handles smart resolution

talks_config = TalksConfig(
    items=[
        TalkItem(
            title="Your Talk Title",
            date="Month YYYY",
            venue="Conference/Workshop Name",
            type="Keynote",  # e.g., "Keynote", "Tutorial", "Panel", "Invited Talk"
            description="Brief description of your talk.",
            # Links can be URLs or local files in static/ directory
            slides="talks/keynote_slides.pdf",         # Local PDF in static/talks/
            video="https://youtube.com/watch?v=example", # YouTube URL
            materials="talks/supplementary.zip",       # Local materials
            code="https://github.com/username/talk-code", # GitHub repo
        ),
        TalkItem(
            title="Another Talk",
            date="Earlier Month YYYY",
            venue="Workshop Name",
            type="Invited Talk",
            description="Description of another presentation.",
            # Example with different types of links
            slides="https://speakerdeck.com/username/slides", # External slides
            demo="demos/interactive_demo.html",        # Local demo file
        ),
        # Add more talks here...
    ]
)