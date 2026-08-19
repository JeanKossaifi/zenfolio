"""Page-level SEO context, template rendering, and safe file writing."""

import mimetypes
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .errors import ZenFolioBuildError
from .models.site_config import AuthorConfig
from .output_manager import is_relative_to
from .serialization import as_dict
from .utils import is_external_url, normalize_route, route_to_output_path


class PageRenderer:
    """Render complete pages while tracking public routes and sitemap data."""

    def __init__(
        self,
        config: Any,
        identity: Any,
        site_type: str,
        theme: Any,
        resolve_path: Callable[[str], str],
        resolve_item_paths: Callable[[Dict[str, Any]], None],
        set_page_context: Callable[[str], str],
    ):
        self.config = config
        self.identity = identity
        self.site_type = site_type
        self.theme = theme
        self.resolve_path = resolve_path
        self.resolve_item_paths = resolve_item_paths
        self.set_page_context = set_page_context
        self.output_dir = Path(".")
        self.navigation: List[Dict[str, Any]] = []
        self.built_pages: List[Tuple[str, str]] = []
        self.seo_pages: List[Dict[str, str]] = []
        self.generated_routes: Set[str] = set()

    def configure(
        self,
        output_dir: Path,
        navigation: List[Dict[str, Any]],
        built_pages: List[Tuple[str, str]],
        seo_pages: List[Dict[str, str]],
        generated_routes: Set[str],
    ) -> None:
        self.output_dir = output_dir
        self.navigation = navigation
        self.built_pages = built_pages
        self.seo_pages = seo_pages
        self.generated_routes = generated_routes

    def render_and_write(
        self,
        filename: str,
        content: str,
        page_title: str = "",
        seo_generator: Optional[Any] = None,
        page_type: str = "page",
        item_data: Optional[Dict[str, Any]] = None,
        structured_data_list: Optional[str] = None,
        **context: Any,
    ) -> None:
        route = normalize_route(filename)
        if route in self.generated_routes:
            raise ZenFolioBuildError(
                f"Multiple pages resolve to the same public route: {route}"
            )
        self.generated_routes.add(route)
        page_base_url = self.set_page_context(route)
        item_data = item_data or {}
        current_page = context.pop(
            "current_page",
            next(
                (
                    item["key"]
                    for item in self.navigation
                    if not item["external"] and item["route"] == route
                ),
                route.strip("/").split("/")[0] or "home",
            ),
        )

        identity_data = as_dict(self.identity)
        self.resolve_item_paths(identity_data)
        author_data = (
            as_dict(self.identity)
            if isinstance(self.identity, AuthorConfig)
            else {}
        )

        seo_context: Dict[str, Any] = {
            "canonical_url": None,
            "og_image": None,
            "og_image_width": None,
            "og_image_height": None,
            "og_image_type": None,
            "og_image_alt": None,
            "meta_description": self.config.site.description,
            "structured_data": structured_data_list,
        }
        if seo_generator:
            if not any(page["route"] == route for page in self.seo_pages):
                sitemap_entry = {"route": route}
                if page_type == "blog_post":
                    modified = item_data.get("updated") or item_data.get("date")
                    if modified:
                        sitemap_entry["lastmod"] = (
                            modified.strftime("%Y-%m-%d")
                            if hasattr(modified, "strftime")
                            else str(modified)[:10]
                        )
                self.seo_pages.append(sitemap_entry)

            seo_context["meta_description"] = (
                seo_generator.generate_meta_description(page_type, item_data)
            )
            if seo_generator.has_absolute_base_url:
                seo_context["canonical_url"] = seo_generator._build_url(
                    route.lstrip("/")
                )

            content_image = item_data.get("image")
            image = (
                item_data.get("social_image")
                or content_image
                or self.config.site.social_image
                or self.config.site.seo.custom_og_image
                or getattr(self.identity, "logo", None)
                or getattr(self.identity, "image", None)
                or getattr(self.identity, "photo_path", None)
            )
            if image:
                image_width = (
                    item_data.get("social_image_width")
                    or item_data.get("image_width")
                )
                image_height = (
                    item_data.get("social_image_height")
                    or item_data.get("image_height")
                )
                if image == self.config.site.social_image:
                    image_width = (
                        image_width or self.config.site.social_image_width
                    )
                    image_height = (
                        image_height or self.config.site.social_image_height
                    )
                    seo_context["og_image_alt"] = (
                        item_data.get("social_image_alt")
                        or self.config.site.social_image_alt
                    )
                identity_image = (
                    getattr(self.identity, "logo", None)
                    or getattr(self.identity, "image", None)
                    or getattr(self.identity, "photo_path", None)
                )
                if image == identity_image:
                    image_width = (
                        image_width
                        or getattr(self.identity, "photo_width", None)
                    )
                    image_height = (
                        image_height
                        or getattr(self.identity, "photo_height", None)
                    )
                if is_external_url(image):
                    seo_context["og_image"] = image
                elif seo_generator.has_absolute_base_url:
                    seo_context["og_image"] = seo_generator._build_url(
                        f"static/{self.resolve_path(image)}"
                    )
                else:
                    seo_context["og_image"] = self.theme.asset_url(image)
                seo_context["og_image_width"] = image_width
                seo_context["og_image_height"] = image_height
                seo_context["og_image_type"] = mimetypes.guess_type(
                    str(image)
                )[0]
                seo_context["og_image_alt"] = (
                    seo_context["og_image_alt"]
                    or item_data.get("social_image_alt")
                    or item_data.get("image_alt")
                )

            if not seo_context["structured_data"]:
                if page_type == "homepage":
                    people = (
                        self.config.people.items
                        if self.config.people
                        else None
                    )
                    seo_context["structured_data"] = (
                        seo_generator.generate_identity_schema(people)
                    )
                elif page_type == "blog_post":
                    item_data["route"] = route
                    seo_context["structured_data"] = (
                        seo_generator.generate_blog_posting_schema(item_data)
                    )

        html = self.theme.render_page(
            content=content,
            page_title=page_title,
            social_title=(
                item_data.get("social_title")
                or (
                    self.config.site.social_title
                    if page_type == "homepage"
                    else page_title
                )
            ),
            social_description=(
                item_data.get("social_description")
                or (
                    self.config.site.social_description
                    if page_type == "homepage"
                    else seo_context["meta_description"]
                )
                or seo_context["meta_description"]
            ),
            author_name=self.identity.name,
            site_description=self.config.site.description,
            base_url=page_base_url,
            current_page=current_page,
            current_route=route,
            author=author_data,
            identity=identity_data,
            site_type=self.site_type,
            navigation=self.navigation,
            built_pages=self.built_pages,
            site=self.config.site,
            site_seo=self.config.site.seo,
            mathjax_config=(
                self.config.mathjax
                if self.theme.content_requires_math(content)
                else None
            ),
            robots_meta=self.config.site.seo.robots_meta,
            **seo_context,
            **context,
        )
        output_path = self.output_dir / route_to_output_path(route)
        resolved_output = output_path.resolve()
        if not is_relative_to(resolved_output, self.output_dir.resolve()):
            raise ZenFolioBuildError(
                f"Generated route escapes the output directory: {route}"
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
