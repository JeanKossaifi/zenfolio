"""
Template Helpers for ZenFolio
Simple helper functions for common configuration patterns
"""

from typing import List, Optional
from ..models import (
    NewsItem, ProjectItem, ServiceItem, HomepageButton
)


def news(title: str, content: str, date: str, url: Optional[str] = None, highlight: bool = False) -> NewsItem:
    """Quick helper to create news items"""
    return NewsItem(
        title=title,
        content=content, 
        date=date,
        url=url,
        highlight=highlight
    )


def project(title: str, description: str, url: Optional[str] = None, 
           github: Optional[str] = None, tags: Optional[List[str]] = None, 
           highlight: bool = False) -> ProjectItem:
    """Quick helper to create project items"""
    return ProjectItem(
        title=title,
        description=description,
        url=url,
        github=github,
        tags=tags or [],
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