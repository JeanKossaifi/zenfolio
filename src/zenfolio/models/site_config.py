"""
Site configuration models for the academic website generator
"""

from zencfg import ConfigBase
from typing import List, Optional, Union
from pathlib import Path
from .content_models import NewsConfig, ProjectsConfig, TalksConfig
# Path types handled as strings in ZenCFG, resolved in ZenFolio core

class ServiceItem(ConfigBase):
    """Academic service entry"""
    description: str  # The service role/position
    date: str         # Year or year range (e.g., "2024" or "2021-2023")
    url: Optional[str] = None  # Optional link to more details
    category: str = "standard"  # Category: "featured", "area_chair", "reviewer", "editorial", "standard"
    subtitle: Optional[str] = None  # Optional subtitle/context for featured items
    venue: Optional[str] = None  # Venue/organization for grouping (e.g., "NeurIPS", "ICML")
    highlight: Optional[str] = None  # Highlight type: "outstanding", "award", etc.

class HomepageButton(ConfigBase):
    """Homepage button configuration"""
    text: str  # Button text/label
    url: str   # Button URL/link
    style: str = "primary"  # Button style: "primary", "secondary", or "accent"

class AuthorConfig(ConfigBase):
    """Author information"""
    name: str = "Your Name"
    title: str = "Your Title"
    affiliation: str = "Your Institution"
    email: str = "your.email@example.com"
    
    # Tagline for the hero section
    tagline: str = "Your research focus and mission statement"
    
    # Research interests (displayed as tags)
    interests: List[str] = [
        "Research Area 1",
        "Research Area 2", 
        "Research Area 3"
    ]
    
    # Social links
    github: str = "https://github.com/yourusername"
    scholar: str = "https://scholar.google.com/citations?user=YOUR_ID"
    linkedin: str = "https://linkedin.com/in/yourusername"
    twitter: str = "https://twitter.com/yourusername"
    
    photo_path: str = "profile.jpg"  # Path to profile photo in static folder
    
    # Optional: CV file path (can be local file or URL)  
    cv_path: Optional[str] = None  # e.g., "documents/cv.pdf" or "https://example.com/cv.pdf"
    
    # Homepage action buttons
    homepage_buttons: List[HomepageButton] = []
    
    # Academic service
    service: List[ServiceItem] = []


class PublicationConfig(ConfigBase):
    """Publication settings"""
    bib_path: str = "publications.bib"  # Path to BibTeX file in content folder
    highlight_author: Optional[Union[str, List[str]]] = None  # Author name(s) to highlight


class MathJaxConfig(ConfigBase):
    """MathJax configuration for LaTeX math rendering"""
    # MathJax version and CDN
    version: str = "3"  # "2" or "3"
    cdn_url: Optional[str] = None  # Custom CDN URL, defaults to official CDN
    
    # Math delimiters
    inline_math: List[List[str]] = [['$', '$'], ['\\(', '\\)']]
    display_math: List[List[str]] = [['$$', '$$'], ['\\[', '\\]']]
    
    # Processing options
    process_escapes: bool = True
    process_environments: bool = True
    
    # Extensions (for MathJax v2/v3)
    extensions: List[str] = ["ams"]  # Common: ["ams", "boldsymbol", "color"]
    
    # Advanced options
    skip_html_tags: List[str] = ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
    ignore_html_class: str = 'tex2jax_ignore'
    process_html_class: str = 'tex2jax_process'


class SEOConfig(ConfigBase):
    """SEO and structured data configuration - smart defaults with override options"""
    
    # Educational background (can't be auto-detected)
    alumni_of: Optional[str] = None  # e.g., "Imperial College London"
    
    # Override auto-detected values (optional)
    custom_og_image: Optional[str] = None  # Override default author photo for OG image
    custom_knowledge_areas: Optional[List[str]] = None  # Override author.interests for structured data
    custom_publisher_name: Optional[str] = None  # Override author.name for blog publisher
    custom_publisher_logo: Optional[str] = None  # Override author.photo_path for blog publisher logo
    
    # Social media settings
    twitter_card_type: str = "summary_large_image"  # "summary" or "summary_large_image"
    
    # Advanced control (for power users)
    disable_structured_data: bool = False  # Disable all JSON-LD schemas
    robots_meta: str = "index, follow"  # Custom robots directive


class SiteConfig(ConfigBase):
    """Site settings"""
    title: str = "Your Name - Your Title"
    description: str = "Personal website of [Your Name], [brief description of your work]"
    base_url: str = "https://yourdomain.com"  # Used as base_url for production builds
    google_analytics: str = ""
    markdown_extensions: List[str] = ['fenced_code', 'codehilite', 'tables', 'admonition', 'def_list', 'attr_list', 'footnotes']  # Markdown extensions for content rendering
    
    # SEO configuration
    seo: SEOConfig = SEOConfig()
    
    # Blog configuration
    blog_folder: Optional[str] = "blog"  # Blog directory name (None = disable blog completely, "blog" = default)
    
    # Homepage display settings
    homepage_publications_count: Optional[int] = 3  # Number of publications to show on homepage (None = show all highlighted)
    homepage_news_count: Optional[int] = 3         # Number of news items to show on homepage (None = show all)


class Config(ConfigBase):
    """Main configuration"""
    author: AuthorConfig = AuthorConfig()
    site: SiteConfig = SiteConfig()
    publications: PublicationConfig = PublicationConfig()
    
    # Math rendering configuration
    mathjax: MathJaxConfig = MathJaxConfig()
    
    # Content structure - populated by user's content files (optional)
    news: Optional[NewsConfig] = NewsConfig()
    projects: Optional[ProjectsConfig] = ProjectsConfig()
    talks: Optional[TalksConfig] = TalksConfig()
    
    # Build settings
    theme: str = "minimal"
    output_path: str = "_site"   # Output directory for generated site
    static_path: str = "static"  # Static files directory 