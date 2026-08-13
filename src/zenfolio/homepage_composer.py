"""Configured homepage section resolution and composition."""

from typing import Any, Dict, List, Optional, Protocol, Sequence

import markdown

from .models.site_config import AuthorConfig
from .serialization import as_dict
from .utils import join_route


SECTION_COMPONENTS = {
    "process": "process_section",
    "why_aie": "why_aie_section",
    "statement": "statement_section",
    "methods": "methods_section",
    "research_directions": "research_directions_section",
    "featured_work": "featured_work_section",
    "publication_preview": "publication_preview_section",
    "team_preview": "team_preview_section",
    "updates_preview": "updates_section",
}


class HomepageHost(Protocol):
    config: Any
    content: Any
    identity: Any
    site_type: str
    theme: Any
    effective_base_url: str

    def _route_for(self, key: str) -> str: ...
    def _set_page_context(self, route: str) -> str: ...
    def _resolve_item_paths(self, item: Dict[str, Any]) -> None: ...
    def _process_content_field(
        self, content: str, content_type: str, field_name: str
    ) -> str: ...
    def _process_items(
        self, items: List[Any], item_type: str, seo_generator: Any = None
    ) -> List[Dict[str, Any]]: ...
    def _process_service_items(
        self, items: List[Any], seo_generator: Any = None
    ) -> Dict[str, Any]: ...
    def _render_and_write_page(
        self, filename: str, content: str, **kwargs: Any
    ) -> None: ...


class HomepageComposer:
    """Build configured group homepages while preserving the facade API."""

    def __init__(self, host: HomepageHost):
        self.host = host

    @staticmethod
    def selected_publications(
        publications: Sequence[Dict[str, Any]],
        limit: Optional[int],
    ) -> List[Dict[str, Any]]:
        highlighted = sorted(
            [item for item in publications if item.get("highlight")],
            key=lambda item: (
                item.get("homepage_order") is None,
                item.get("homepage_order") or 0,
            ),
        )
        recent = [item for item in publications if not item.get("highlight")]
        if limit is None:
            return highlighted
        selected = highlighted[:limit]
        selected.extend(recent[: max(0, limit - len(selected))])
        return selected

    def prepare_blog_routes(self) -> None:
        host = self.host
        collection_route = host._route_for("blog")
        for post in host.content.blog_posts:
            if post.get("route"):
                continue
            if collection_route.endswith(".html"):
                folder = collection_route.rsplit("/", 1)[-1][:-5]
                post["route"] = f"/{folder}/{post['slug']}.html"
            else:
                post["route"] = join_route(collection_route, post["slug"])

    def group_people(
        self, people: Sequence[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        host = self.host
        configured = (
            getattr(host.config.people, "categories", [])
            if host.config.people
            else []
        ) or []
        category_titles = {
            category.key: category.title for category in configured
        }
        order = [category.key for category in configured]
        for person in people:
            category = person.get("category", "core")
            if category not in order:
                order.append(category)
        default_titles = {
            "lead": "Group lead",
            "group_lead": "Group lead",
            "core": "Core research team",
            "intern": "Interns",
            "interns": "Interns",
        }
        return [
            {
                "key": key,
                "title": category_titles.get(
                    key,
                    default_titles.get(
                        key, key.replace("_", " ").title()
                    ),
                ),
                "items": [
                    person
                    for person in people
                    if person.get("category", "core") == key
                ],
            }
            for key in order
            if any(
                person.get("category", "core") == key
                for person in people
            )
        ]

    def resolve_section(
        self,
        section_config: Any,
        publications: Sequence[Dict[str, Any]],
        seo_generator: Optional[Any],
    ) -> Dict[str, Any]:
        host = self.host
        section = as_dict(section_config)
        section_type = section.get("type", "card_grid")
        source = section.get("source")
        section["section_id"] = (
            section.get("id") or source or section_type
        )
        section["grid_cols"] = section.get("columns", 1)
        section["content"] = (
            host._process_content_field(section["body"], "markdown", "body")
            if section.get("body")
            else ""
        )

        items: Sequence[Any] = []
        item_type = None
        if source == "research_areas":
            items = getattr(host.config.research_areas, "items", []) or []
            item_type = "research_area_item"
        elif source == "projects":
            items = getattr(host.config.projects, "items", []) or []
            item_type = "project_item"
        elif source == "publications":
            items = sorted(
                publications,
                key=lambda item: (
                    item.get("homepage_order") is None,
                    item.get("homepage_order") or 0,
                ),
            )
            item_type = "publication_item"
        elif source in {"people", "team"}:
            items = getattr(host.config.people, "items", []) or []
            item_type = "person_item"
        elif source in {"updates", "blog"}:
            self.prepare_blog_routes()
            items = host.content.blog_posts
            item_type = "blog_post_item"
        elif source == "news":
            items = getattr(host.config.news, "items", []) or []
            item_type = "news_item"
        elif source == "about":
            section["content"] = host._process_content_field(
                host.content.bio.get("bio", ""), "markdown", "bio"
            )
        elif source == "service" and isinstance(
            host.identity, AuthorConfig
        ):
            section["items"] = host._process_service_items(
                host.identity.service, seo_generator
            )

        if item_type:
            if section.get("featured_only"):
                items = [
                    item
                    for item in items
                    if (
                        item.get("highlight", False)
                        if isinstance(item, dict)
                        else getattr(item, "highlight", False)
                    )
                ]
            limit = section.get("limit")
            if limit is not None:
                items = list(items)[: int(limit)]
            section["items"] = host._process_items(
                list(items), item_type, seo_generator
            )
            if source in {"people", "team"}:
                section["grouped_items"] = self.group_people(
                    section["items"]
                )

        if section.get("view_all_route"):
            section["view_all_link"] = {
                "url": section["view_all_route"],
                "text": section.get("view_all_label") or "View all",
            }
        return section

    def build_configured(
        self,
        publications: List[Dict[str, Any]],
        base_url: str,
        seo_generator: Optional[Any],
    ) -> None:
        host = self.host
        host._set_page_context("/")
        hero_data = as_dict(host.identity)
        host._resolve_item_paths(hero_data)
        hero_data["photo"] = (
            hero_data.get("image") or hero_data.get("photo_path")
        )
        hero_data["publications_route"] = host._route_for("publications")

        rendered_sections = []
        for configured_section in host.config.homepage_sections:
            raw_section = as_dict(configured_section)
            section_type = raw_section.get("type", "card_grid")
            if section_type == "hero":
                for key in (
                    "eyebrow",
                    "title",
                    "headline",
                    "body",
                    "steps",
                    "actions",
                    "template_name",
                ):
                    value = raw_section.get(key)
                    if value not in (None, "", []):
                        hero_data[key] = value
                continue

            section = self.resolve_section(
                configured_section, publications, seo_generator
            )
            section["preview_mode"] = not host.effective_base_url.startswith(
                ("http://", "https://")
            )
            if not (
                section.get("content")
                or section.get("items")
                or section.get("steps")
                or section.get("grouped_items")
            ):
                continue
            component = (
                section.get("template_name")
                or SECTION_COMPONENTS.get(section_type, "section")
            )
            if component not in host.theme.env.globals:
                component = "section"
            section["rendered_html"] = host.theme.render_component(
                component, section=section, **section
            )
            rendered_sections.append(section)

        content = host.theme.render_component(
            "landing_page",
            hero=hero_data,
            hero_component=(
                "group_hero"
                if host.site_type == "group"
                else "profile_hero"
            ),
            sections=rendered_sections,
            site_type=host.site_type,
        )
        host._render_and_write_page(
            "/",
            content,
            page_title=host.config.site.title,
            base_url=base_url,
            seo_generator=seo_generator,
            page_type="homepage",
            item_data={
                "description": host.config.site.description,
                "social_description": (
                    host.config.site.social_description
                    or host.config.site.description
                ),
                "social_image": host.config.site.social_image or "",
                "social_title": (
                    host.config.site.social_title
                    or host.config.site.title
                ),
            },
        )

    def build_legacy(
        self,
        publications: List[Dict[str, Any]],
        bio_data: Dict[str, Any],
        base_url: str,
        seo_generator: Optional[Any],
    ) -> None:
        host = self.host
        host._set_page_context("/")
        hero_data = as_dict(host.identity)
        host._resolve_item_paths(hero_data)
        hero_data["publications_route"] = host._route_for("publications")
        hero_data.update(
            {
                "photo": (
                    hero_data.get("photo_path") or hero_data.get("image")
                ),
                "actions": [
                    {
                        "text": button.text,
                        "url": button.url,
                        "style": (
                            "bg-gray-900 dark:bg-white text-white "
                            "dark:text-gray-900"
                            if button.style == "primary"
                            else "bg-gray-50 dark:bg-gray-800 border "
                            "border-gray-200 dark:border-gray-700 "
                            "text-gray-900 dark:text-white"
                        ),
                        "external": button.url.startswith("http"),
                    }
                    for button in (
                        getattr(host.identity, "homepage_buttons", []) or []
                    )
                ],
                "social_links": [
                    {
                        "url": hero_data.get("github"),
                        "icon": "fab fa-github",
                        "label": "GitHub",
                    },
                    {
                        "url": hero_data.get("scholar"),
                        "icon": "fas fa-graduation-cap",
                        "label": "Google Scholar",
                    },
                    {
                        "url": hero_data.get("linkedin"),
                        "icon": "fab fa-linkedin",
                        "label": "LinkedIn",
                    },
                    {
                        "url": hero_data.get("twitter"),
                        "icon": "fab fa-twitter",
                        "label": "Twitter",
                    },
                ],
            }
        )
        hero_data["social_links"] = [
            link for link in hero_data["social_links"] if link["url"]
        ]

        highlighted = [
            publication
            for publication in publications
            if publication.get("highlight", False)
        ]
        recent = [
            publication
            for publication in publications
            if not publication.get("highlight", False)
        ]
        publication_count = host.config.site.homepage_publications_count
        if publication_count is None:
            homepage_publications = highlighted
        else:
            homepage_publications = highlighted[:publication_count]
            homepage_publications.extend(
                recent[
                    : max(
                        0,
                        publication_count - len(homepage_publications),
                    )
                ]
            )

        projects = [
            item
            for item in (getattr(host.config.projects, "items", []) or [])
            if getattr(item, "highlight", False)
        ]
        news = getattr(host.config.news, "items", []) or []
        news_count = host.config.site.homepage_news_count
        sections = [
            {
                "id": "bio",
                "data": {
                    "title": "About",
                    "layout": "bio",
                    "content": markdown.markdown(
                        bio_data.get("bio", ""),
                        extensions=host.config.site.markdown_extensions,
                    ),
                    "interests": hero_data.get("interests", []),
                },
            },
            {
                "id": "featured_work",
                "data": {
                    "title": "Featured Work",
                    "grid_cols": 2,
                    "background": True,
                    "items": host._process_items(
                        projects, "project_item", seo_generator
                    ),
                    "view_all_link": {
                        "url": host._route_for("projects"),
                        "text": "View all projects",
                    },
                },
            },
            {
                "id": "recent_publications",
                "data": {
                    "title": (
                        "Selected Publications"
                        if highlighted
                        else "Recent Publications"
                    ),
                    "grid_cols": 1,
                    "items": host._process_items(
                        homepage_publications,
                        "publication_item",
                        seo_generator,
                    ),
                    "view_all_link": {
                        "url": host._route_for("publications"),
                        "text": "View all publications",
                    },
                },
            },
            {
                "id": "recent_news",
                "data": {
                    "title": "Recent News",
                    "layout": "timeline",
                    "background": True,
                    "items": host._process_items(
                        news[:news_count] if news_count is not None else news,
                        "news_item",
                        seo_generator,
                    ),
                    "view_all_link": {
                        "url": host._route_for("news"),
                        "text": "View all news",
                    },
                },
            },
            {
                "id": "academic_service",
                "data": {
                    "title": "Academic Service",
                    "layout": "service",
                    "items": host._process_service_items(
                        getattr(host.identity, "service", []),
                        seo_generator,
                    ),
                },
            },
        ]

        rendered_sections = []
        for section in sections:
            section_data = section["data"]
            section_id = section["id"]
            section_data["section_id"] = section_id
            if section_id == "academic_service":
                service_items = section_data.get("items", {})
                has_content = bool(
                    service_items.get("leadership_items")
                    or service_items.get("review_groups")
                )
            else:
                has_content = bool(
                    section_data.get("items")
                    or section_data.get("content")
                )
            if not has_content:
                if host.debug:
                    print(f"⚠️ Skipping empty section: {section_id}")
                continue
            section_html = host.theme.render_component(
                "section", **section_data
            )
            if not section_html or not section_html.strip():
                if host.debug:
                    print(
                        f"⚠️ Section '{section_id}' rendered as empty HTML"
                    )
                continue
            section_data["rendered_html"] = section_html
            rendered_sections.append(section_data)

        if host.debug:
            print(
                f"📊 Homepage sections: {len(sections)} defined, "
                f"{len(rendered_sections)} rendered"
            )
        content = host.theme.render_component(
            "landing_page",
            hero=hero_data,
            sections=rendered_sections,
        )
        host._render_and_write_page(
            "/",
            content,
            page_title=host.config.site.title,
            base_url=base_url,
            seo_generator=seo_generator,
            page_type="homepage",
        )

    def build(
        self,
        publications: List[Dict[str, Any]],
        bio_data: Dict[str, Any],
        base_url: str,
        seo_generator: Optional[Any],
    ) -> None:
        if self.host.config.homepage_sections is not None:
            self.build_configured(
                publications, base_url, seo_generator
            )
        else:
            self.build_legacy(
                publications, bio_data, base_url, seo_generator
            )
