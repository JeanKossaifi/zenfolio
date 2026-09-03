#!/usr/bin/env python3
"""ZenFolio site configuration."""

from zenfolio.models import (
    AuthorConfig, Config, OrganizationRef, PublicationConfig, SiteConfig,
)

author_config = AuthorConfig(
    name="Your Name",
    title="Your Title",
    affiliation=OrganizationRef(
        name="Your Institution",
        url="https://institution.example/",
    ),
    email="your.email@example.com",
    tagline="Your research tagline or mission statement",
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
    # Search preview; search engines may rewrite it for a query.
    title="Your Name - Academic Website",
    description="Personal academic website",
    base_url="https://yourdomain.com",

    # Optional social override; otherwise title and description are reused.
    # social_image="social-card.png",
)

publication_config = PublicationConfig(
    bib_path="publications.bib",
    highlight_author="Your Name"
)

# Uncomment an import and its matching Config field to enable a section.
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