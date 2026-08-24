#!/usr/bin/env python3
"""Site configuration - Edit this file with your information"""

# HomepageButton and ServiceItem are imported for the commented examples
# below — uncomment those examples to use them.  # noqa: F401
from zenfolio.models import (
    AuthorConfig, Config, HomepageButton, PublicationConfig, ServiceItem, SiteConfig,
)
# Simple strings for paths - ZenFolio handles smart resolution

# Customize your author information
author_config = AuthorConfig(
    name="Your Name",
    title="Your Title",
    affiliation="Your Institution",
    email="your.email@example.com",
    
    # Tagline for the hero section
    tagline="Your research tagline or mission statement",
    
    # Research interests (displayed as tags)
    interests=[
        "Research Area 1",
        "Research Area 2", 
        "Research Area 3"
    ],
    
    # Social links (leave empty to hide)
    github="",
    scholar="",
    linkedin="",
    twitter="",
    
    photo_path="profile.jpg",  # Place in static/ folder
    
    # Optional: Add the path to your CV here to make the button appear
    cv_path=None,  # e.g., "Your_Name_CV.pdf" or "https://example.com/cv.pdf"
    
    # Homepage action buttons - customize your main call-to-action buttons
    # Available styles: "primary" (dark), "secondary" (light), "accent" (teal)
    # Leave empty to use default buttons (View Publications, Get in Touch)
    homepage_buttons=[
        # HomepageButton(text="View My Work", url="projects.html", style="primary"),
        # HomepageButton(text="Contact Me", url="mailto:your.email@example.com", style="secondary"),
        # HomepageButton(text="Download CV", url="Your_CV.pdf", style="accent"),
    ],
    
    # Academic service
    # Option 1: Add ServiceItem entries directly here
    # service=[
    #     ServiceItem(description="Program Committee Member", date="2024", url="https://example.com"),
    #     ServiceItem(description="Reviewer", date="2023"),
    # ]
    # Option 2: Import from separate service.py file (recommended for longer lists)
    service=[]
)

# Site settings
site_config = SiteConfig(
    title="Your Name - Academic Website",
    description="Personal academic website",
    base_url="https://yourdomain.com",
    # Uncomment to customize markdown extensions (defaults: fenced_code, codehilite, tables, admonition, def_list, attr_list)
    # markdown_extensions=['fenced_code', 'codehilite', 'tables', 'admonition', 'def_list', 'attr_list', 'toc']
)

# Publication settings
publication_config = PublicationConfig(
    bib_path="publications.bib",
    highlight_author="Your Name"
)

# Content imports: news.py, projects.py, and talks.py were created next to
# this file by `zenfolio init`. To enable a section, uncomment BOTH its
# import here and the matching argument in Config below.
# from news import news_config
# from projects import projects_config
# from talks import talks_config

config = Config(
    author=author_config,
    site=site_config,
    publications=publication_config,
    theme="tailwind",
    # news=news_config,
    # projects=projects_config,
    # talks=talks_config,
) 