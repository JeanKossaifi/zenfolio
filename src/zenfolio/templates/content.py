#!/usr/bin/env python3
"""
Personal content for your academic website
This file contains the actual content data, separate from the generic models
"""

from zenfolio.models import NewsItem, ProjectItem, TalkItem, ContentConfig

# Research interests
research_interests = [
    "Your Research Area 1",
    "Your Research Area 2", 
    "Your Research Area 3"
]

# News items
news = [
    NewsItem(
        date="2024-01-15",
        content="Your latest news or publication announcement here.",
        highlight=True
    ),
    NewsItem(
        date="2024-01-10", 
        content="Another news item or update.",
        highlight=False
    )
]

# Projects
projects = [
    ProjectItem(
        title="Your Project Name",
        description="Description of your project and its impact.",
        github="https://github.com/yourusername/project"
    ),
    ProjectItem(
        title="Another Project",
        description="Description of another project.",
        website="https://yourproject.com"
    )
]

# Talks
talks = [
    TalkItem(
        title="Your Talk Title",
        date="2024-01-20",
        venue="Conference Name",
        type="Keynote",
        description="Description of your talk and its key points."
    ),
    TalkItem(
        title="Another Talk",
        date="2024-01-15",
        venue="Workshop Name", 
        type="Invited Talk",
        description="Description of another talk."
    )
]

# Content configuration
content = ContentConfig(
    research_interests=research_interests,
    news=news,
    projects=projects,
    talks=talks
) 