"""
Content models for academic websites
"""

from zencfg import ConfigBase
from typing import List, Optional, Union, Any
from datetime import date
# Paths handled as strings, resolved during rendering

class NewsItem(ConfigBase):
    """News entry with optional links as direct attributes"""
    date: str
    content: str
    highlight: bool = False
    # Optional links as direct attributes - can be local files or URLs
    paper: Optional[str] = None
    code: Optional[str] = None
    slides: Optional[str] = None
    video: Optional[str] = None
    website: Optional[str] = None
    demo: Optional[str] = None
    release_notes: Optional[str] = None
    documentation: Optional[str] = None
    tutorial_page: Optional[str] = None
    materials: Optional[str] = None
    project_page: Optional[str] = None
    
    template_name: str = "news_item"


class ProjectItem(ConfigBase):
    """Project entry with optional links as direct attributes"""
    title: str
    description: str
    # Optional image for visual card display
    image: Optional[str] = None  # Path to image in static folder (e.g., "projects/screenshot.png")
    # Optional category for tagging (e.g., "Open Source", "Industry Impact")
    category: Optional[str] = None
    # Optional collaborators
    collaborators: List[str] = []
    # Highlight flag for homepage display
    highlight: bool = False
    # Optional links as direct attributes - can be local files or URLs
    github: Optional[str] = None       # e.g., "https://github.com/user/repo"
    documentation: Optional[str] = None # e.g., "docs/manual.pdf" or "https://docs.example.com"
    paper: Optional[str] = None        # e.g., "papers/paper.pdf" or "https://arxiv.org/abs/..."
    website: Optional[str] = None      # e.g., "https://project-site.com"
    demo: Optional[str] = None         # e.g., "https://demo.com" or "demos/interactive.html"
    code: Optional[str] = None         # e.g., "https://github.com/user/code"
    
    template_name: str = "project_item"


class TalkItem(ConfigBase):
    """Talk/presentation entry with optional links as direct attributes"""
    title: str
    date: str = ""
    venue: str = ""
    type: str = ""  # Keynote, Tutorial, Panel, etc.
    description: str = ""
    # Optional links as direct attributes - can be local files or URLs
    slides: Optional[str] = None    # e.g., "talks/slides.pdf" or "https://slides.com/..."
    video: Optional[str] = None     # e.g., "https://youtube.com/watch?v=..."
    code: Optional[str] = None      # e.g., "https://github.com/user/talk-code"
    materials: Optional[str] = None # e.g., "talks/handouts.pdf"
    demo: Optional[str] = None      # e.g., "https://demo-site.com"
    
    template_name: str = "talk_item"



# Content Config Classes
class NewsConfig(ConfigBase):
    """News content configuration"""
    items: List[NewsItem] = []


class ProjectsConfig(ConfigBase):
    """Projects content configuration"""
    items: List[ProjectItem] = []


class TalksConfig(ConfigBase):
    """Talks content configuration"""
    items: List[TalkItem] = []


class BlogPost(ConfigBase):
    """Blog post with ZenCFG validation and defaults"""
    title: str = "Untitled"
    slug: str = ""
    date: Any = ""  # ZenCFG converts date objects to strings automatically
    excerpt: str = ""
    tags: List[str] = []  # ZenCFG handles mutable defaults
    image: str = ""  # Hero image for blog post and social media preview
    content: str = ""
    content_raw: str = ""
    content_type: str = "markdown"  # Type of content: markdown or notebook
    template_name: str = "blog_post_item"
    



class Page(ConfigBase):
    """Standalone page parsed from markdown with frontmatter"""
    title: str = ""
    slug: str = ""
    content: str = ""
    
    template_name: str = "page"
    



class Bio(ConfigBase):
    """Bio information from index.md"""
    bio: str = ""
    tagline: str = ""
    interests: List[str] = []



 
