"""
Site configuration models for the academic website generator
"""

from typing import Any, Dict, List, Literal, Optional, Union

from zencfg import ConfigBase

from .content_models import (
    NewsConfig,
    PeopleConfig,
    ProjectsConfig,
    ResearchAreasConfig,
    TalksConfig,
)


class ServiceItem(ConfigBase):
    """Academic service entry for personal sites."""

    description: str = ""
    date: str = ""
    url: Optional[str] = None
    category: str = "standard"
    subtitle: Optional[str] = None
    venue: Optional[str] = None
    highlight: Optional[str] = None


class HomepageButton(ConfigBase):
    """Legacy personal-homepage action."""

    text: str = ""
    url: str = ""
    style: str = "primary"


class HomepageAction(ConfigBase):
    """Action rendered in a configured homepage section."""

    label: str = ""
    route: str = ""
    style: str = "primary"


class HomepageStep(ConfigBase):
    """A connected process step or compact method pillar."""

    title: str = ""
    description: str = ""
    # Set to "scholar" to compose the description from scholar_stats instead of
    # hardcoding figures that then drift out of date.
    source: str = ""


class HomepageSection(ConfigBase):
    """Typed, ordered homepage section configuration."""

    id: str = ""
    type: str = "card_grid"
    source: Optional[str] = None
    eyebrow: str = ""
    title: str = ""
    headline: str = ""
    body: str = ""
    layout: str = "grid"
    limit: Optional[int] = None
    featured_only: bool = False
    columns: int = 1
    background: bool = False
    steps: List[HomepageStep] = []
    actions: List[HomepageAction] = []
    view_all_label: Optional[str] = None
    view_all_route: Optional[str] = None
    template_name: Optional[str] = None
    show_research_interests: bool = False


class NavItem(ConfigBase):
    """An ordered navigation destination."""

    label: str = ""
    route: str = ""
    key: Optional[str] = None
    visible: bool = True


class IdentityConfig(ConfigBase):
    """Fields shared by people and research groups."""

    name: str = ""
    short_name: Optional[str] = None
    description: str = ""
    image: Optional[str] = None
    email: Optional[str] = None


class OrganizationRef(ConfigBase):
    """One authoritative reference to an organization."""

    name: str = ""
    url: Optional[str] = None


class AuthorConfig(IdentityConfig):
    """Personal-site identity. Existing fields remain source compatible."""

    name: str = "Your Name"
    title: str = "Your Title"
    affiliation: Union[str, OrganizationRef] = "Your Institution"
    employer: Optional[Union[str, OrganizationRef]] = None
    alumni_of: List[OrganizationRef] = []
    email: Optional[str] = "your.email@example.com"
    tagline: str = "Your research focus and mission statement"
    interests: List[str] = [
        "Research Area 1",
        "Research Area 2",
        "Research Area 3",
    ]
    # Social links: empty by default so placeholder URLs never leak
    # into rendered pages or JSON-LD sameAs entries.
    github: str = ""
    scholar: str = ""
    linkedin: str = ""
    twitter: str = ""
    same_as: List[str] = []
    orcid: Optional[str] = None
    photo_path: str = "profile.jpg"
    photo_width: Optional[int] = None
    photo_height: Optional[int] = None
    cv_path: Optional[str] = None
    homepage_buttons: List[HomepageButton] = []
    service: List[ServiceItem] = []


class GroupConfig(IdentityConfig):
    """Research-group identity, kept separate from personal author data."""

    name: str = "Your Research Group"
    short_name: Optional[str] = None
    parent_name: str = ""
    parent_url: Optional[str] = None
    eyebrow: str = ""
    tagline: str = ""
    description: str = ""
    logo: Optional[str] = None
    hero_media: Optional[str] = None
    hero_media_alt: str = ""
    hero_media_caption: str = ""
    hero_media_source: str = ""
    hero_media_approved: bool = False
    hero_diagram_approved: bool = False
    hero_diagram_caption: str = ""
    hero_diagram_source: str = ""
    leader: Optional[str] = None
    research_areas: List[str] = []


class PublicationConfig(ConfigBase):
    """Publication source and list-page settings."""

    bib_path: str = "publications.bib"
    highlight_author: Optional[Union[str, List[str]]] = None
    title: str = "Publications"
    description: str = ""
    meta_description: str = ""
    route: Optional[str] = None
    direction_filters: List[str] = []


class MathJaxConfig(ConfigBase):
    """MathJax configuration for LaTeX math rendering."""

    version: Literal["2", "3"] = "3"
    cdn_url: Optional[str] = None
    inline_math: List[List[str]] = [["$", "$"], ["\\(", "\\)"]]
    display_math: List[List[str]] = [["$$", "$$"], ["\\[", "\\]"]]
    process_escapes: bool = True
    process_environments: bool = True
    extensions: List[str] = ["ams"]
    skip_html_tags: List[str] = [
        "script",
        "noscript",
        "style",
        "textarea",
        "pre",
        "code",
    ]
    ignore_html_class: str = "tex2jax_ignore"
    process_html_class: str = "tex2jax_process"


class SEOConfig(ConfigBase):
    """Advanced crawler and structured-data controls."""

    twitter_card_type: str = "summary_large_image"
    disable_structured_data: bool = False
    robots_meta: str = "index, follow"


class SiteConfig(ConfigBase):
    """Site-wide metadata and collection labels."""

    # Preferred web-search result title and snippet. Search engines can rewrite
    # either for a specific query.
    title: str = "Your Name - Your Title"
    description: str = "Personal website of [Your Name]"
    # Canonical public origin used by search engines to consolidate URLs.
    base_url: str = "https://yourdomain.com"
    # Social/link previews default to the search title and description.
    social_title: Optional[str] = None
    social_description: Optional[str] = None
    social_image: Optional[str] = None
    social_image_alt: str = ""
    require_social_image: bool = False
    social_image_width: int = 1200
    social_image_height: int = 630
    google_analytics: str = ""
    markdown_extensions: List[str] = [
        "fenced_code",
        "codehilite",
        "tables",
        "admonition",
        "def_list",
        "attr_list",
        "footnotes",
    ]
    seo: SEOConfig = SEOConfig()
    blog_folder: Optional[str] = "blog"
    blog_label: str = "Blog"
    blog_description: str = ""
    blog_meta_description: str = ""
    blog_route: Optional[str] = None
    homepage_publications_count: Optional[int] = 3
    homepage_news_count: Optional[int] = 3


class Config(ConfigBase):
    """Main ZenFolio configuration."""

    site_type: str = "person"
    identity: Optional[IdentityConfig] = None
    author: AuthorConfig = AuthorConfig()
    site: SiteConfig = SiteConfig()
    publications: PublicationConfig = PublicationConfig()
    mathjax: MathJaxConfig = MathJaxConfig()

    news: Optional[NewsConfig] = NewsConfig()
    projects: Optional[ProjectsConfig] = ProjectsConfig()
    talks: Optional[TalksConfig] = TalksConfig()
    people: Optional[PeopleConfig] = None
    research_areas: Optional[ResearchAreasConfig] = None

    navigation: Optional[List[NavItem]] = None
    homepage_sections: Optional[List[HomepageSection]] = None
    scholar_stats: Optional[Dict[str, Any]] = None

    theme: str = "minimal"
    theme_path: Optional[str] = None
    theme_parent: Optional[str] = None
    output_path: str = "_site"
    static_path: str = "static"