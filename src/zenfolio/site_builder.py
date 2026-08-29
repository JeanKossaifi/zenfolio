"""Top-level build orchestration for ZenFolio."""

from typing import Any, Protocol

from .media_assets import prepare_talk_thumbnails
from .models.site_config import AuthorConfig
from .seo_utils import SEOGenerator


class SiteBuildHost(Protocol):
    config: Any
    identity: Any
    site_type: str
    content: Any
    theme: Any
    content_dir: Any
    output_dir: Any
    output_manager: Any
    generated_routes: set
    seo_pages: list
    effective_base_url: str

    def _configure_navigation(self) -> None: ...
    def _sync_output_manager(self) -> None: ...
    def _route_for(self, key: str) -> str: ...
    def _is_requested_page(self, *keys: str) -> bool: ...
    def _standalone_page_route(self, page: dict) -> str: ...
    def _prepare_blog_routes(self) -> None: ...
    def _build_home_page(self, *args: Any, **kwargs: Any) -> None: ...
    def _build_list_page(self, *args: Any, **kwargs: Any) -> None: ...
    def _build_team_page(self, *args: Any, **kwargs: Any) -> None: ...
    def _build_blog_post_pages(
        self, *args: Any, **kwargs: Any
    ) -> None: ...
    def _build_pages(self, *args: Any, **kwargs: Any) -> None: ...
    def _generate_sitemap(self, *args: Any, **kwargs: Any) -> None: ...


class SiteBuilder:
    """Coordinate a complete build through the backward-compatible facade."""

    def __init__(self, host: SiteBuildHost):
        self.host = host

    def build(self, base_url: str = "") -> bool:
        host = self.host
        print("🔨 Building ZenFolio website...")
        host.effective_base_url = (base_url or "").rstrip("/")
        host.generated_routes.clear()
        host.seo_pages.clear()

        host.content.load()
        prepare_talk_thumbnails(host.content_dir, host.config.talks)
        host._configure_navigation()
        host._sync_output_manager()
        host.output_manager.prepare(host.theme)

        seo_generator = SEOGenerator(
            host.config,
            host.effective_base_url,
            identity=host.identity,
            site_type=host.site_type,
        )
        print("🏗️ Building pages...")
        host._build_home_page(
            host.content.publications,
            host.content.bio,
            host.effective_base_url,
            seo_generator,
        )

        scholar_stats = None
        if isinstance(host.identity, AuthorConfig):
            scholar_stats = dict(
                getattr(host.config, "scholar_stats", None) or {}
            )
            if scholar_stats and host.identity.scholar:
                scholar_stats["scholar_url"] = host.identity.scholar

        if host._is_requested_page("publications"):
            host._build_list_page(
                host.config.publications.title,
                host._route_for("publications"),
                host.content.publications,
                "publication_item",
                1,
                host.effective_base_url,
                group_by="year",
                has_search=True,
                seo_generator=seo_generator,
                scholar_stats=scholar_stats,
                page_type="publications",
                intro=host.config.publications.description,
                meta_description=(
                    host.config.publications.meta_description
                    or host.config.publications.description
                ),
                filter_directions=(
                    host.config.publications.direction_filters
                ),
            )

        if (
            host.config.projects
            and host.config.projects.items
            and host._is_requested_page("projects")
        ):
            host._build_list_page(
                host.config.projects.title,
                host._route_for("projects"),
                host.config.projects.items,
                "project_item",
                2,
                host.effective_base_url,
                seo_generator=seo_generator,
                page_type="projects",
                intro=host.config.projects.description,
            )

        if (
            host.config.talks
            and host.config.talks.items
            and not (
                host.config.news
                and host.config.news.merge_talks
            )
            and host._is_requested_page("talks")
        ):
            host._build_list_page(
                host.config.talks.title,
                host._route_for("talks"),
                host.config.talks.items,
                "talk_item",
                1,
                host.effective_base_url,
                seo_generator=seo_generator,
                page_type="talks",
                intro=host.config.talks.description,
            )

        if (
            host.config.news
            and host.config.news.items
            and host._is_requested_page("news")
        ):
            host._build_list_page(
                host.config.news.title,
                host._route_for("news"),
                host.config.news.items,
                "news_item",
                1,
                host.effective_base_url,
                layout="timeline",
                seo_generator=seo_generator,
                page_type="news",
                intro=host.config.news.description,
                related_collections=(
                    {
                        "talk_items": (
                            host.config.talks.items,
                            "updates_talk_item",
                        )
                    }
                    if (
                        host.config.news.merge_talks
                        and host.config.talks
                        and host.config.talks.items
                    )
                    else None
                ),
            )

        if (
            host.config.people
            and host.config.people.items
            and host._is_requested_page("team", "people")
        ):
            host._build_team_page(seo_generator)

        research_route = host._route_for("research")
        has_research_markdown = any(
            page.get("slug") == "research"
            and host._standalone_page_route(page) == research_route
            for page in host.content.pages
        )
        if (
            host.config.research_areas
            and host.config.research_areas.items
            and host._is_requested_page("research")
            and not has_research_markdown
        ):
            host._build_list_page(
                host.config.research_areas.title,
                research_route,
                host.config.research_areas.items,
                "research_area_item",
                3,
                host.effective_base_url,
                seo_generator=seo_generator,
                page_type="research",
                intro=host.config.research_areas.description,
            )

        # Homepage sections sourced from the blog link to individual posts,
        # so post pages must exist even when navigation omits the blog.
        homepage_links_posts = any(
            getattr(section, "source", None) in {"blog", "updates"}
            for section in (host.config.homepage_sections or [])
        )
        if host.content.blog_posts and host.config.site.blog_folder:
            blog_in_nav = host._is_requested_page("blog", "updates")
            if blog_in_nav or homepage_links_posts:
                host._prepare_blog_routes()
            if blog_in_nav:
                host._build_list_page(
                    host.config.site.blog_label,
                    host._route_for("blog"),
                    host.content.blog_posts,
                    "blog_post_item",
                    2,
                    host.effective_base_url,
                    seo_generator=seo_generator,
                    page_type=(
                        "updates" if host.site_type == "group" else "blog"
                    ),
                    intro=host.config.site.blog_description,
                    meta_description=(
                        host.config.site.blog_meta_description
                        or host.config.site.blog_description
                    ),
                )
            if blog_in_nav or homepage_links_posts:
                host._build_blog_post_pages(
                    host.content.blog_posts,
                    host.effective_base_url,
                    seo_generator,
                )

        host._build_pages(host.effective_base_url, seo_generator)
        print("🗺️ Generating sitemap...")
        host._generate_sitemap(seo_generator)
        print(f"✅ Site built successfully in {host.output_dir}/")
        return True
