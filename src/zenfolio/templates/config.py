#!/usr/bin/env python3
"""ZenFolio site configuration."""

from zenfolio.models import (
    AuthorConfig, ZenFolioConfig, OrganizationConfig, PublicationsConfig, SiteConfig,
)

identity = AuthorConfig(
    name="Your Name",
    title="Your Title",
    affiliation=OrganizationConfig(
        name="Your Institution",
        url="https://institution.example/",
    ),
    email="your.email@example.com",
    tagline="A short description of your research",
    interests=[
        "Research Area 1",
        "Research Area 2",
        "Research Area 3",
    ],
    github="",
    scholar="",
    linkedin="",
    twitter="",
    same_as=[],
    photo_path="profile.jpg",
)

site_config = SiteConfig(
    # Title and description for search results.
    title="Your Name - Academic Website",
    description="Personal academic website",
    base_url="https://yourdomain.com",

    # Optional image shown when someone shares a link to your site.
    # social_image="social-card.png",

    # Optional Google tag measurement ID.
    # google_analytics_id="G-XXXXXXXXXX",

    # Other analytics scripts to include on every page.
    # analytics_scripts=["https://analytics.example/script.js"],
)

publications_config = PublicationsConfig(
    bib_path="publications.bib",
    highlight_author="Your Name"
)

# Uncomment an import and its matching ZenFolioConfig field to enable a section.
# from news import news_config
# from projects import projects_config
# from talks import talks_config

config = ZenFolioConfig(
    identity=identity,
    site=site_config,
    publications=publications_config,
    theme="tailwind",
    # news=news_config,
    # projects=projects_config,
    # talks=talks_config,
)
