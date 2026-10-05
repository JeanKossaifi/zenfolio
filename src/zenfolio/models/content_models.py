"""
Content models for academic websites
"""

from typing import Annotated, Any, List, Literal, Optional

from pydantic import Field, field_validator
from zencfg import ConfigBase

# Paths handled as strings, resolved during rendering


class LinkConfig(ConfigBase):
    """A labeled internal route or external URL."""

    label: str = ""
    url: str = ""


class NewsEntryConfig(ConfigBase):
    """News entry with optional links as direct attributes"""
    # Prefer ISO precision: YYYY, YYYY-MM, or YYYY-MM-DD.
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


class ProjectConfig(ConfigBase):
    """Project entry with optional links as direct attributes."""
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
    # Mark a project for highlighted presentation.
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
    # Headline outcome and its comparison, e.g. "**19.8%** lower error".
    result: str = ""
    result_note: str = ""
    links: List[LinkConfig] = []
    
    template_name: str = "project_item"


class TalkConfig(ConfigBase):
    """Talk or presentation with optional links as direct attributes."""
    title: str
    # Prefer ISO precision: YYYY, YYYY-MM, or YYYY-MM-DD. Common readable
    # English forms remain accepted by the renderer and collection sorter.
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
    website: Optional[str] = None   # Event website
    archive_url: Optional[str] = None  # Preserved copy of a retired event page
    thumbnail: Optional[str] = None  # Local image, or a build-cached video thumbnail
    
    template_name: str = "talk_item"


class PersonConfig(ConfigBase):
    """A person's profile, independent of their current place on the team.

    Move the complete record between ``TeamConfig`` lists when their role
    changes. Keep known internship years here so that history moves with them.
    """

    name: str
    role: str = ""
    internship_years: List[Annotated[int, Field(strict=True, gt=0)]] = []
    affiliation: str = ""
    bio: str = ""
    research_interests: List[str] = []
    photo: Optional[str] = None
    photo_alt: str = ""
    profile: Optional[str] = None
    links: List[LinkConfig] = []
    highlight: bool = False
    template_name: str = "person_item"
    content_type: str = "markdown"

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("PersonConfig.name must not be blank")
        return value

    def validate_profile(self) -> None:
        """Recheck history after in-place edits to the internship years list."""
        self._validate_name(self.name)
        if any(type(year) is not int or year <= 0 for year in self.internship_years):
            raise ValueError("PersonConfig.internship_years must contain positive integers")


class ResearchAreaConfig(ConfigBase):
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
    links: List[LinkConfig] = []
    template_name: str = "research_area_item"
    content_type: str = "markdown"


# Content Config Classes
class NewsConfig(ConfigBase):
    """News content configuration"""
    news: List[NewsEntryConfig] = []
    title: str = "News"
    # One-line tagline shown beside the page title, like the other sections.
    description: str = ""
    # Merge talks into this archive and present one Updates navigation entry.
    merge_talks: bool = False


class ProjectsConfig(ConfigBase):
    """Projects content configuration"""
    projects: List[ProjectConfig] = []
    title: str = "Projects"
    description: str = ""
    route: Optional[str] = None


class TalksConfig(ConfigBase):
    """Talks content configuration"""
    talks: List[TalkConfig] = []
    title: str = "Talks"
    description: str = ""
    route: Optional[str] = None
    cache_video_thumbnails: bool = False


class TeamConfig(ConfigBase):
    """Team-page settings and explicit lists in their display order.

    Define each person in their current list and retain internship history
    on the person's record. Past interns have no current team appointment.
    """

    members: List[PersonConfig] = []
    interns: List[PersonConfig] = []
    past_interns: List[PersonConfig] = []
    title: str = "Team"
    description: str = ""
    meta_description: str = ""
    route: Optional[str] = None


class ResearchAreasConfig(ConfigBase):
    """Research-direction card configuration."""

    areas: List[ResearchAreaConfig] = []
    title: str = "Research"
    description: str = ""
    route: Optional[str] = None


class BlogPostConfig(ConfigBase):
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
    actions: List[LinkConfig] = []
    route: str = ""
    content: str = ""
    content_raw: str = ""
    content_type: str = "markdown"  # Type of content: markdown or notebook
    template_name: str = "blog_post_item"
    


class PageConfig(ConfigBase):
    """Standalone page rendered inside the active site's document shell."""
    title: str = ""
    slug: str = ""
    route: str = ""
    eyebrow: str = ""
    description: str = ""
    social_title: str = ""
    social_description: str = ""
    social_image: str = ""
    image: str = ""  # Teaser for update cards and social previews
    image_alt: str = ""
    image_caption: str = ""
    image_source: str = ""
    content: str = ""
    content_type: str = "markdown"  # markdown, notebook, or html
    layout: Literal["prose", "wide", "full"] = "prose"
    show_site_header: bool = True
    show_site_footer: bool = True
    stylesheets: List[str] = []
    scripts: List[str] = []
    show_in_updates: bool = False
    date: Any = ""
    og_type: str = ""
    theme_color: str = ""
    navigation_key: str = ""

    template_name: str = "page"
    


class BioConfig(ConfigBase):
    """Bio information from index.md."""
    bio: str = ""
    title: str = ""  # page/frontmatter title, also used by config fallbacks
    affiliation: str = ""
    tagline: str = ""
    interests: List[str] = []
