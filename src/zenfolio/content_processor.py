"""Template-ready content processing and local/external link resolution."""

import re
import textwrap
from typing import Any, Dict, List, Optional

import markdown

from .serialization import as_dict
from .utils import build_url, is_external_url


class ContentProcessor:
    """Convert parsed/configured items into rendered theme components."""

    def __init__(
        self,
        config: Any,
        theme: Any,
        parser_registry: Any,
        debug: bool = False,
    ):
        self.config = config
        self.theme = theme
        self.parser_registry = parser_registry
        self.debug = debug

    @staticmethod
    def resolve_path(path: str) -> str:
        if is_external_url(path):
            return path
        clean_path = str(path).lstrip("/")
        if clean_path.startswith("static/"):
            clean_path = clean_path[len("static/"):]
        return clean_path

    def process_static_placeholders(
        self, content: str, base_url: str = ""
    ) -> str:
        if "{static}" in content:
            content = content.replace(
                "{static}", build_url(base_url, "static")
            )

        def replace_relative_images(match: Any) -> str:
            current_src = match.group(1)
            if not current_src.startswith(
                ("http://", "https://", "//", "../", "data:", "static/")
            ) and current_src.startswith("images/"):
                return f'src="{build_url(base_url, f"static/{current_src}")}"'
            return match.group(0)

        content = re.sub(
            r'src="([^"]+)"', replace_relative_images, content
        )

        def replace_internal_links(match: Any) -> str:
            href = match.group(1)
            if href.startswith("/") and not href.startswith("//"):
                return f'href="{self.theme.url_for(href)}"'
            return match.group(0)

        return re.sub(r'href="([^"]+)"', replace_internal_links, content)

    def process_items(
        self,
        items: List[Any],
        item_type: str,
        seo_generator: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        if not items:
            return []

        processed: List[Dict[str, Any]] = []
        markdown_keys = ["content", "description", "excerpt", "bio"]
        for item in items:
            if isinstance(item, dict) or hasattr(item, "to_dict"):
                item_dict = as_dict(item)
            else:
                item_dict = dict(item)

            if "content" in item_dict and "content_raw" not in item_dict:
                item_dict["content_raw"] = item_dict["content"]
            self.resolve_item_paths(item_dict)

            content_type = item_dict.get("content_type", item_type)
            skip_content = (
                item_type == "blog_post_item"
                or content_type == "blog_post_item"
            )
            for key in markdown_keys:
                value = item_dict.get(key)
                if not value or not isinstance(value, str):
                    continue
                if skip_content and key == "content":
                    continue
                if item_type == "service_item" and key == "description":
                    continue
                item_dict[key] = self.process_content_field(
                    value, content_type, key
                )

            item_dict["template_type"] = (
                item_dict.get("template_name") or item_type
            )
            if item_dict["template_type"]:
                item_dict["rendered_html"] = self.theme.render_component(
                    item_dict["template_type"],
                    item=item_dict,
                    seo_generator=seo_generator,
                )
            item_dict["rendered_schema"] = ""
            if seo_generator:
                if item_type == "publication_item":
                    item_dict["rendered_schema"] = (
                        seo_generator.generate_scholarly_article_schema(
                            item_dict
                        )
                    )
                elif item_type == "project_item":
                    item_dict["rendered_schema"] = (
                        seo_generator.generate_software_application_schema(
                            item_dict
                        )
                    )
            processed.append(item_dict)
        return processed

    def process_service_items(
        self,
        items: List[Any],
        seo_generator: Optional[Any] = None,
    ) -> Dict[str, Any]:
        leadership = self.process_items(
            [item for item in items if item.category == "leadership"],
            "service_item",
            seo_generator,
        )
        review_items = self.process_items(
            [item for item in items if item.category != "leadership"],
            "service_item",
            seo_generator,
        )
        review_groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in review_items:
            group_name = item.get("description", "Other").strip()
            review_groups.setdefault(group_name, []).append(item)
        return {
            "leadership_items": leadership,
            "review_groups": review_groups,
        }

    def process_content_field(
        self, content: str, content_type: str, field_name: str
    ) -> str:
        parsers = self.parser_registry.get_parsers_for_content_type(
            content_type
        )
        for parser in parsers:
            processor = parser.get_content_processor(content_type)
            if not processor:
                continue
            try:
                return processor(
                    content, self.config.site.markdown_extensions
                )
            except Exception as error:
                if self.debug:
                    print(
                        f"⚠️  Warning: Failed to process {field_name} with "
                        f"{parser.__class__.__name__}: {error}"
                    )

        try:
            normalized = textwrap.dedent(content).strip()
            return markdown.markdown(
                normalized,
                extensions=self.config.site.markdown_extensions,
            )
        except Exception as error:
            if self.debug:
                print(
                    f"⚠️  Warning: Failed to process {field_name} with "
                    f"fallback markdown: {error}"
                )
            return content

    def resolve_item_paths(self, item_dict: Dict[str, Any]) -> None:
        asset_fields = {
            "photo",
            "image",
            "logo",
            "hero_media",
            "social_image",
            "photo_path",
        }
        link_fields = {
            "paper",
            "code",
            "slides",
            "video",
            "website",
            "demo",
            "release_notes",
            "documentation",
            "tutorial_page",
            "materials",
            "project_page",
            "github",
            "cv",
            "cv_path",
            "profile",
            "link",
        }
        for key in asset_fields:
            value = item_dict.get(key)
            if value and isinstance(value, str):
                item_dict[key] = self.resolve_path(value)
        for key in link_fields:
            value = item_dict.get(key)
            if not value or not isinstance(value, str):
                continue
            if is_external_url(value) or value.startswith("#"):
                continue
            if value.startswith("/") or value.endswith("/") or value.endswith(
                ".html"
            ):
                item_dict[key] = self.theme.url_for(value)
            else:
                item_dict[key] = self.theme.asset_url(value)

        for collection_key in ("links", "actions"):
            resolved_links = []
            for link in item_dict.get(collection_key, []) or []:
                link_data = as_dict(link)
                url = link_data.get("url")
                if url and not is_external_url(url):
                    if (
                        url.startswith("/")
                        or url.endswith("/")
                        or url.endswith(".html")
                    ):
                        link_data["url"] = self.theme.url_for(url)
                    else:
                        link_data["url"] = self.theme.asset_url(url)
                resolved_links.append(link_data)
            item_dict[collection_key] = resolved_links
