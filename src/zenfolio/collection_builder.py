"""Aggregate, blog, team, and standalone page builders."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from .utils import join_route, normalize_route


class CollectionHost(Protocol):
    config: Any
    content: Any
    identity: Any
    theme: Any
    site_type: str
    output_dir: Path
    seo_pages: List[Dict[str, str]]
    debug: bool

    def _route_for(self, key: str) -> str: ...
    def _standalone_page_route(
        self, page_data: Dict[str, Any]
    ) -> str: ...
    def _set_page_context(self, route: str) -> str: ...
    def _process_items(
        self, items: List[Any], item_type: str, seo_generator: Any = None
    ) -> List[Dict[str, Any]]: ...
    def _process_content_field(
        self, content: str, content_type: str, field_name: str
    ) -> str: ...
    def _process_static_placeholders(
        self, content: str, base_url: str = ""
    ) -> str: ...
    def _selected_publications(
        self, publications: List[Dict[str, Any]], limit: Optional[int]
    ) -> List[Dict[str, Any]]: ...
    def _group_people(
        self, people: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]: ...
    def _render_and_write_page(
        self, filename: str, content: str, **kwargs: Any
    ) -> None: ...


class CollectionBuilder:
    """Build non-homepage pages from parsed and configured collections."""

    def __init__(self, host: CollectionHost):
        self.host = host

    def build_list_page(
        self,
        title: str,
        filename: str,
        items: List[Any],
        item_type: str,
        columns: int,
        base_url: str,
        layout: str = "grid",
        group_by: Optional[str] = None,
        has_search: bool = False,
        seo_generator: Optional[Any] = None,
        scholar_stats: Optional[dict] = None,
        page_type: str = "page",
        intro: str = "",
        meta_description: str = "",
        filter_directions: Optional[List[str]] = None,
        grouped_items: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        host = self.host
        route = normalize_route(filename)
        host._set_page_context(route)
        processed_items = host._process_items(
            items, item_type, seo_generator
        )
        page_data: Dict[str, Any] = {
            "title": title,
            "identity": host.identity,
            "intro": (
                host._process_content_field(intro, "markdown", "intro")
                if intro
                else ""
            ),
            "columns": columns,
            "grid_cols": columns,
            "layout": layout,
            "items": processed_items,
            "grouped_items": grouped_items,
            "items_html": "",
            "has_search": has_search,
            "scholar_stats": scholar_stats,
            "filter_years": sorted(
                {
                    str(item.get("year"))
                    for item in processed_items
                    if item.get("year")
                },
                reverse=True,
            ),
            "filter_directions": filter_directions
            or sorted(
                {
                    direction
                    for item in processed_items
                    for direction in item.get("directions", [])
                }
            ),
        }

        if group_by and grouped_items is None:
            grouped: Dict[Any, List[Dict[str, Any]]] = {}
            for item in processed_items:
                key = item.get(group_by)
                if key:
                    grouped.setdefault(key, []).append(item)
            try:
                sorted_keys = sorted(grouped, key=int, reverse=True)
            except (ValueError, TypeError):
                sorted_keys = sorted(grouped, reverse=True)
            page_data["grouped_items"] = [
                {"group_name": key, "items": grouped[key]}
                for key in sorted_keys
            ]
        else:
            page_data["items_html"] = "".join(
                item["rendered_html"] for item in processed_items
            )

        content = host.theme.render_component("page_layout", **page_data)
        schemas = [
            item["rendered_schema"]
            for item in processed_items
            if item.get("rendered_schema")
        ]
        combined_schema = f"[{','.join(schemas)}]" if schemas else None
        host._render_and_write_page(
            route,
            content,
            page_title=title,
            base_url=base_url,
            seo_generator=seo_generator,
            page_type=page_type,
            structured_data_list=combined_schema,
            item_data={"description": meta_description or intro},
        )

    def build_team_page(self, seo_generator: Optional[Any] = None) -> None:
        host = self.host
        route = host._route_for("team")
        host._set_page_context(route)
        processed_people = host._process_items(
            host.config.people.items, "person_item", seo_generator
        )
        groups = host._group_people(processed_people)
        page_data = {
            "title": host.config.people.title,
            "identity": host.identity,
            "intro": host._process_content_field(
                host.config.people.description, "markdown", "intro"
            ),
            "columns": 3,
            "grid_cols": 3,
            "layout": "team",
            "items": processed_people,
            "grouped_items": groups,
            "items_html": "",
            "has_search": False,
            "scholar_stats": None,
            "filter_years": [],
            "filter_directions": [],
        }
        content = host.theme.render_component("page_layout", **page_data)
        host._render_and_write_page(
            route,
            content,
            page_title=host.config.people.title,
            seo_generator=seo_generator,
            page_type="team",
            item_data={
                "description": (
                    host.config.people.meta_description
                    or host.config.people.description
                )
            },
        )

    def build_blog_post_pages(
        self,
        blog_posts: List[Dict[str, Any]],
        base_url: str,
        seo_generator: Optional[Any] = None,
    ) -> None:
        host = self.host
        processed_posts = host._process_items(
            blog_posts, "blog_post_item", seo_generator
        )
        for post in processed_posts:
            route = post.get("route") or join_route(
                host._route_for("blog"), post["slug"]
            )
            nested_base_url = host._set_page_context(route)
            content_type = post.get("content_type", "blog_post")
            post["content"] = host._process_content_field(
                post["content_raw"], content_type, "content"
            )
            post["content"] = host._process_static_placeholders(
                post["content"], nested_base_url
            )
            content_html = host.theme.render_component(
                "blog_post_page", item=post
            )
            host._render_and_write_page(
                route,
                content_html,
                page_title=post["title"],
                base_url=nested_base_url,
                current_page=(
                    "updates" if host.site_type == "group" else "blog"
                ),
                seo_generator=seo_generator,
                page_type="blog_post",
                item_data=post,
            )

    def build_standalone_pages(
        self,
        base_url: str = "",
        seo_generator: Optional[Any] = None,
    ) -> None:
        host = self.host
        for page_data in host.content.pages:
            slug = page_data["slug"]
            route = host._standalone_page_route(page_data)
            nested_base_url = host._set_page_context(route)
            content_html = host._process_content_field(
                page_data["content"],
                page_data.get("content_type", "page"),
                "content",
            )
            content_html = host._process_static_placeholders(
                content_html, nested_base_url
            )
            item = dict(page_data)
            item["content"] = content_html

            research_areas: List[Dict[str, Any]] = []
            related_publications: List[Dict[str, Any]] = []
            related_projects: List[Dict[str, Any]] = []
            if slug == "research":
                research_areas = host._process_items(
                    getattr(host.config.research_areas, "items", []) or [],
                    "research_area_item",
                    seo_generator,
                )
                related_publications = host._process_items(
                    host._selected_publications(
                        host.content.publications, 4
                    ),
                    "publication_item",
                    seo_generator,
                )
                related_projects = host._process_items(
                    getattr(host.config.projects, "items", []) or [],
                    "project_item",
                    seo_generator,
                )

            page_content = host.theme.render_component(
                "page",
                item=item,
                identity=host.identity,
                research_areas=research_areas,
                related_publications=related_publications,
                related_projects=related_projects,
            )
            host._render_and_write_page(
                route,
                page_content,
                page_title=page_data["title"],
                base_url=nested_base_url,
                current_page=slug,
                seo_generator=seo_generator,
                page_type="research" if slug == "research" else "page",
                item_data=item,
            )

    def generate_sitemap(self, seo_generator: Any) -> None:
        host = self.host
        if not host.seo_pages:
            if host.debug:
                print("⚠️  Warning: No pages tracked for sitemap generation")
            return
        sitemap_xml = seo_generator.generate_sitemap_xml(host.seo_pages)
        (host.output_dir / "sitemap.xml").write_text(
            sitemap_xml, encoding="utf-8"
        )
        if host.debug:
            print(
                f"✅ Generated sitemap with {len(host.seo_pages)} pages"
            )
