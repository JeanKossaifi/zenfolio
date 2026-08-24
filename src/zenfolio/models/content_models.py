"""
Content models for academic websites
"""

from zencfg import ConfigBase
from typing import Any, List, Optional
# Paths handled as strings, resolved during rendering


class Link(ConfigBase):
    """A labeled internal route or external URL."""

    label: str = ""
    url: str = ""


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
    # Schema.org type for machine-readable project metadata.
    schema_type: str = "SoftwareSourceCode"
    # Optional image for visual card display
    image: Optional[str] = None  # Path to image in static folder (e.g., "projects/screenshot.png")
    # Optional category for tagging (e.g., "Open Source", "Industry Impact")
    category: Optional[str] = None
    # Optional collaborators
    collaborators: List[str] = []
    # Machine-readable metadata consumed by the SoftwareSourceCode schema
    programming_language: Optional[str] = None  # e.g. "Python"
    license: Optional[str] = None  # e.g. "MIT" or a license URL
    # Backward-compatible legacy feature flag.
    highlight: bool = False
    # Ordered feature placement shared by the homepage and Projects page.
    # Zero means regular project; positive values determine feature order.
    featured_order: int = 0
    # Constrained Projects-page span for featured projects.
    featured_size: str = "wide"  # standard, wide, or full
    # Visual treatment for the supplied image.
    image_style: str = "logo"  # logo or media
    # Optional links as direct attributes - can be local files or URLs
    github: Optional[str] = None       # e.g., "https://github.com/user/repo"
    documentation: Optional[str] = None # e.g., "docs/manual.pdf" or "https://docs.example.com"
    paper: Optional[str] = None        # e.g., "papers/paper.pdf" or "https://arxiv.org/abs/..."
    website: Optional[str] = None      # e.g., "https://project-site.com"
    demo: Optional[str] = None         # e.g., "https://demo.com" or "demos/interactive.html"
    code: Optional[str] = None         # e.g., "https://github.com/user/code"
    label: Optional[str] = None
    image_alt: str = ""
    image_caption: str = ""
    image_source: str = ""
    attribution: str = ""
    links: List[Link] = []
    
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
    link: Optional[str] = None      # e.g., "https://conference.com/talk" - event/talk page link
    website: Optional[str] = None   # Backward-compatible event website alias
    archive_url: Optional[str] = None  # Preserved copy of a retired event page
    
    template_name: str = "talk_item"


class TeamCategory(ConfigBase):
    """Ordered heading used to keep team groups distinct."""

    key: str = ""
    title: str = ""
    description: str = ""


class TeamMember(ConfigBase):
    """A member of a research group."""

    name: str = ""
    role: str = ""
    category: str = "core"
    years: str = ""
    affiliation: str = ""
    bio: str = ""
    research_interests: List[str] = []
    photo: Optional[str] = None
    photo_alt: str = ""
    profile: Optional[str] = None
    links: List[Link] = []
    highlight: bool = False
    template_name: str = "person_item"
    content_type: str = "markdown"


class PersonItem(TeamMember):
    """Backward-compatible name for the generic person-card model."""


class ResearchAreaItem(ConfigBase):
    """A structured research direction."""

    title: str = ""
    description: str = ""
    slug: str = ""
    image: Optional[str] = None
    image_alt: str = ""
    image_caption: str = ""
    image_source: str = ""
    highlight: bool = False
    tags: List[str] = []
    links: List[Link] = []
    template_name: str = "research_area_item"
    content_type: str = "markdown"



# Content Config Classes
class NewsConfig(ConfigBase):
    """News content configuration"""
    items: List[NewsItem] = []
    title: str = "News"
    # One-line tagline shown beside the page title, like the other sections.
    description: str = ""
    # Merge talks into this archive and present one Updates navigation entry.
    merge_talks: bool = False


class ProjectsConfig(ConfigBase):
    """Projects content configuration"""
    items: List[ProjectItem] = []
    title: str = "Projects"
    description: str = ""
    route: Optional[str] = None


class TalksConfig(ConfigBase):
    """Talks content configuration"""
    items: List[TalkItem] = []
    title: str = "Talks"
    description: str = ""
    route: Optional[str] = None


class PeopleConfig(ConfigBase):
    """Team-page configuration."""

    items: List[TeamMember] = []
    categories: List[TeamCategory] = []
    title: str = "Team"
    description: str = ""
    meta_description: str = ""
    route: Optional[str] = None


class ResearchAreasConfig(ConfigBase):
    """Research-direction card configuration."""

    items: List[ResearchAreaItem] = []
    title: str = "Research"
    description: str = ""
    route: Optional[str] = None


class BlogPost(ConfigBase):
    """Blog post with ZenCFG validation and defaults"""
    title: str = "Untitled"
    slug: str = ""
    date: Any = ""  # date/datetime objects or ISO strings; normalized when sorting
    updated: Any = ""  # last-modified date, used for sitemap lastmod
    excerpt: str = ""
    tags: List[str] = []  # ZenCFG handles mutable defaults
    image: str = ""  # Hero image for blog post and social media preview
    image_alt: str = ""
    image_caption: str = ""
    image_source: str = ""
    image_width: Optional[int] = None  # og:image dimensions for social previews
    image_height: Optional[int] = None
    social_image_width: Optional[int] = None
    social_image_height: Optional[int] = None
    social_image_alt: str = ""
    subtitle: str = ""
    category: str = ""
    description: str = ""
    social_title: str = ""
    social_description: str = ""
    social_image: str = ""
    actions: List[Link] = []
    route: str = ""
    content: str = ""
    content_raw: str = ""
    content_type: str = "markdown"  # Type of content: markdown or notebook
    template_name: str = "blog_post_item"
    



class Page(ConfigBase):
    """Standalone page parsed from markdown with frontmatter"""
    title: str = ""
    slug: str = ""
    route: str = ""
    eyebrow: str = ""
    description: str = ""
    social_title: str = ""
    social_description: str = ""
    social_image: str = ""
    content: str = ""
    content_type: str = "markdown"  # markdown or notebook, set by the parser

    template_name: str = "page"
    



class Bio(ConfigBase):
    """Bio information from index.md"""
    bio: str = ""
    title: str = ""  # page/frontmatter title, also used by config fallbacks
    affiliation: str = ""
    tagline: str = ""
    interests: List[str] = []



 
