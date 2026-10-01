"""Frontmatter-aware parser for HTML page fragments."""

from pathlib import Path
import re
from typing import Any, Dict, List, Set

import frontmatter

from ..errors import ZenFolioBuildError
from .base_parser import ContentParser


_DOCUMENT_MARKUP = re.compile(
    r"<!doctype\b|<\s*(?:html|head|body)\b",
    flags=re.IGNORECASE,
)


class HtmlParser(ContentParser):
    """Parse trusted HTML fragments that are rendered by the site theme."""

    @property
    def supported_extensions(self) -> Set[str]:
        return {".html", ".htm"}

    @property
    def content_types(self) -> Set[str]:
        return {"html", "page"}

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {}

        try:
            with open(file_path, "r", encoding="utf-8-sig") as handle:
                parsed = frontmatter.load(handle)
        except Exception as error:
            raise ZenFolioBuildError(
                f"Could not parse HTML page fragment '{file_path}': {error}"
            ) from error

        content = parsed.content
        if _DOCUMENT_MARKUP.search(content):
            raise ZenFolioBuildError(
                f"HTML page '{file_path}' must contain a body fragment, not "
                "a complete document. Remove doctype, html, head, and body "
                "elements; the active theme supplies them."
            )

        return {
            "metadata": parsed.metadata.copy() if parsed.metadata else {},
            "content": content,
            "content_type": "html",
        }

    def parse_directory(
        self,
        directory_path: Path,
        content_type: str = None,  # noqa: ARG002 - protocol compatibility
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        if not directory_path.exists():
            return items

        for file_path in sorted(directory_path.iterdir()):
            if (
                file_path.is_file()
                and not file_path.name.startswith(("_", "."))
                and self.can_parse(file_path)
            ):
                parsed = self.parse_file(file_path)
                if parsed:
                    parsed["metadata"]["slug"] = parsed["metadata"].get(
                        "slug", file_path.stem
                    )
                    items.append(parsed)
        return items

    def get_content_processor(self, content_type: str):
        if content_type != "html":
            return None

        def preserve_html(
            content: str,
            markdown_extensions: List[str],  # noqa: ARG001
        ) -> str:
            return content.strip()

        return preserve_html
