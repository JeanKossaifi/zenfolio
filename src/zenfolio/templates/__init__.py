"""
Template Helpers for ZenFolio
Simple helper functions for common configuration patterns
"""

from typing import Optional
from ..models import (
    NewsItem, ProjectItem, ServiceItem, HomepageButton
)


def news(content: str, date: str, url: Optional[str] = None, highlight: bool = False) -> NewsItem:
    """Quick helper to create news items; url becomes the item's website link."""
    return NewsItem(
        content=content,
        date=date,
        website=url,
        highlight=highlight
    )


def project(title: str, description: str, url: Optional[str] = None,
           github: Optional[str] = None,
           highlight: bool = False) -> ProjectItem:
    """Quick helper to create project items; url becomes the project website."""
    return ProjectItem(
        title=title,
        description=description,
        website=url,
        github=github,
        highlight=highlight
    )


def service(description: str, date: str, category: str = "reviewer", 
           venue: Optional[str] = None) -> ServiceItem:
    """Quick helper to create service items"""
    return ServiceItem(
        description=description,
        date=date,
        category=category,
        venue=venue
    )


def button(text: str, url: str, style: str = "primary") -> HomepageButton:
    """Quick helper to create homepage buttons"""
    return HomepageButton(text=text, url=url, style=style)


__all__ = ['news', 'project', 'service', 'button']