"""
Unified Configuration Models for ZenFolio
Single import point for all configuration needs
"""

# Content models
from .content_models import (
    NewsItem, ProjectItem, TalkItem, BlogPost, Page, Bio,
    NewsConfig, ProjectsConfig, TalksConfig
)

# Site configuration models  
from .site_config import (
    Config, AuthorConfig, PublicationConfig, SiteConfig, ServiceItem, 
    HomepageButton, MathJaxConfig, SEOConfig
)

# Convenience imports for common use cases
def create_basic_config(name: str, email: str, affiliation: str = "Your Institution") -> Config:
    """Create a basic configuration with minimal setup"""
    return Config(
        author=AuthorConfig(
            name=name,
            email=email,
            affiliation=affiliation
        )
    )

__all__ = [
    # Content models
    'NewsItem', 'ProjectItem', 'TalkItem', 'BlogPost', 'Page', 'Bio',
    'NewsConfig', 'ProjectsConfig', 'TalksConfig',
    
    # Site models
    'Config', 'AuthorConfig', 'PublicationConfig', 'SiteConfig', 'ServiceItem',
    'HomepageButton', 'MathJaxConfig', 'SEOConfig',
    
    # Helper functions
    'create_basic_config'
] 