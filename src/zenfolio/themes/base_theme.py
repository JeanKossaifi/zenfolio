"""
Base Theme Class for ZenFolio
Provides common Jinja2 setup and rendering functionality
"""

from datetime import datetime
import re
from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PrefixLoader,
    StrictUndefined,
    select_autoescape,
)
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Iterable, Optional

import markdown

from ..utils import build_url, is_external_url, normalize_route


class ThemeRenderError(RuntimeError):
    """Raised when a required theme template cannot be loaded or rendered."""


class BaseTheme(ABC):
    """Base class for all ZenFolio themes with common Jinja2 functionality"""

    MARKDOWN_EXTENSIONS = [
        "fenced_code",
        "codehilite",
        "tables",
        "admonition",
        "def_list",
        "attr_list",
        "footnotes",
    ]
    
    def __init__(
        self,
        template_dir: Path = None,
        debug: bool = False,
        template_dirs: Optional[Iterable[Path]] = None,
        parent_template_dir: Optional[Path] = None,
        shared_template_dir: Optional[Path] = None,
    ):
        directories = [Path(path) for path in (template_dirs or [])]
        if template_dir is not None and not directories:
            directories.append(Path(template_dir))

        loaders = [FileSystemLoader(str(path)) for path in directories]
        if parent_template_dir is not None:
            parent_loader = FileSystemLoader(str(parent_template_dir))
            loaders.append(parent_loader)
            loaders.append(PrefixLoader({"parent": parent_loader}))
        if shared_template_dir is not None:
            loaders.append(FileSystemLoader(str(shared_template_dir)))

        loader = ChoiceLoader(loaders) if loaders else None
        self.env = Environment(
            loader=loader,
            trim_blocks=True, 
            lstrip_blocks=True,
            undefined=StrictUndefined,
            autoescape=select_autoescape(
                enabled_extensions=("html", "html.j2", "xml"),
                default_for_string=False,
            ),
        )
        self.debug = debug
        self.template_dirs = directories
        self.template_dir = directories[0] if directories else template_dir
        self.base_url = ""

        self.env.globals["theme"] = self
        self.env.globals["url_for"] = self.url_for
        self.env.globals["asset"] = self.asset_url
        self.env.globals["file"] = self.asset_url
        self.env.globals["render_component"] = self.render_component
        
        # Register all custom filters
        self.env.filters['strip_files_prefix'] = self._strip_files_prefix_filter
        self.env.filters['markdown'] = self._markdown_filter
        self.env.filters['highlight_code'] = self._highlight_code_filter

        self._register_templates()

    def set_render_context(self, base_url: str = "") -> None:
        """Set URL context before rendering components for a page."""

        self.base_url = base_url or ""
        self.env.globals["base_url"] = self.base_url

    @staticmethod
    def content_requires_math(content: str) -> bool:
        """Return whether rendered content contains supported math syntax."""

        if any(
            marker in content
            for marker in ("$$", "\\(", "\\[", "<math", 'class="math')
        ):
            return True
        return bool(
            re.search(
                r"(?<!\\)\$(?!\$)(?=\S)[^$\n]+(?<=\S)\$",
                content,
            )
        )

    def url_for(self, path: str) -> str:
        """Resolve a public route against the current render context."""

        raw_path = str(path)
        if is_external_url(raw_path):
            return raw_path
        route = normalize_route(raw_path)
        if route == "/":
            if self.base_url.startswith(("http://", "https://")):
                return build_url(self.base_url, "")
            return self.base_url or "./"
        if route.startswith("/#"):
            home_url = build_url(self.base_url, "") or "./"
            return f"{home_url}{route[1:]}"
        return build_url(self.base_url, route.lstrip("/"))

    def asset_url(self, path: str) -> str:
        """Resolve a theme/content asset against the current render context."""

        raw_path = str(path or "")
        if not raw_path:
            return ""
        if is_external_url(raw_path):
            return raw_path
        clean_path = raw_path.lstrip("/")
        if clean_path.startswith("static/"):
            clean_path = clean_path[len("static/"):]
        return build_url(self.base_url, f"static/{clean_path}")

    def register_file_templates(self, template_names=None) -> set:
        """Register loader-visible component templates by filename."""

        if self.env.loader is None:
            return set()

        available = set(self.env.list_templates())
        if template_names is None:
            template_names = [
                name
                for name in available
                if name.endswith(".html.j2") and "/" not in name
            ]

        loaded = set()
        for template_name in template_names:
            if template_name.startswith("parent/"):
                continue
            component_name = Path(template_name).stem.replace(".html", "")
            try:
                self.env.globals[component_name] = self.env.get_template(template_name)
            except Exception as exc:
                raise ThemeRenderError(
                    f"Failed to load template '{template_name}': {exc}"
                ) from exc
            loaded.add(component_name)
        return loaded

    def _highlight_code_filter(self, code: str, **kwargs) -> str:
        """A placeholder for syntax highlighting."""
        return f'<pre><code>{code}</code></pre>'

    def _markdown_filter(self, text: str) -> str:
        """Render markdown text to HTML."""
        return markdown.markdown(
            text, extensions=self.MARKDOWN_EXTENSIONS
        )

    def _strip_files_prefix_filter(self, text: str) -> str:
        """A simple placeholder filter."""
        # In nbconvert, HTML output can sometimes have "files/" prefixed to image paths.
        return text.replace("files/", "")
    

    
    def _build_relative_url(self, base_url: str, depth: int = 1) -> str:
        """
        Build a base URL for nested pages (e.g., blog posts, pages)
        
        Args:
            base_url: Original base URL
            depth: How many levels deep (1 for "blog/", "pages/")
        
        Returns:
            Adjusted base URL for the nested page
        """
        # Handle absolute URLs - they don't need adjustment
        if base_url.startswith(('http://', 'https://')):
            return base_url
        
        # For relative URLs, go up the appropriate number of levels
        if not base_url or base_url in ['', './']:
            return '../' * depth
        
        # Handle custom relative paths
        return str(Path('../' * depth) / base_url).replace('\\', '/')
    
    @abstractmethod
    def _register_templates(self):
        """Register theme-specific templates - must be implemented by subclasses"""
        pass
    
    def render_component(self, component_name: str, **kwargs) -> str:
        """Render a required component or fail the build."""

        template = self.env.globals.get(component_name)
        if template is None:
            available = sorted(
                key for key in self.env.globals if not key.startswith("_")
            )
            raise ThemeRenderError(
                f"Missing required template '{component_name}'. "
                f"Available components: {', '.join(available)}"
            )
        try:
            return template.render(**kwargs)
        except Exception as exc:
            if self.debug:
                import traceback

                traceback.print_exc()
            raise ThemeRenderError(
                f"Template rendering failed for '{component_name}': {exc}"
            ) from exc
    
    @abstractmethod
    def write_css_file(self, output_dir: Path):
        """Write theme-specific CSS file - must be implemented by subclasses"""
        pass
    
    def write_js_file(self, output_dir: Path):
        """Write theme-specific JavaScript file - optional, default implementation does nothing"""
        pass
    
    def render_page(self, content: str, page_title: str = "", author_name: str = "",
                    site_description: str = "", base_url: str = "", include_navbar: bool = True, **context) -> str:
        """Render a complete page using the base layout template"""
        self.set_render_context(base_url)
        
        template = self.env.from_string(self.BASE_LAYOUT_TEMPLATE)
        
        # Render modular components
        navbar_html = ""
        footer_html = ""
        if include_navbar:
            navbar_html = self.render_component('navbar', 
                author_name=author_name, 
                **context)
            footer_html = self.render_component('footer', 
                author_name=author_name, 
                current_year=datetime.now().year,
                **context)
        
        return template.render(
            content=content,
            page_title=page_title,
            author_name=author_name,
            site_description=site_description,
            base_url=base_url,
            include_navbar=include_navbar,
            navbar=navbar_html,
            footer=footer_html,
            current_year=datetime.now().year,
            **context
        )
    
    def render_standalone_page(self, content: str, page_title: str = "", author_name: str = "",
                              site_description: str = "", base_url: str = "", **context) -> str:
        """Render a standalone page without navbar/footer"""
        return self.render_page(
            content=content,
            page_title=page_title,
            author_name=author_name,
            site_description=site_description,
            base_url=base_url,
            include_navbar=False,
            **context
        )
    
    # Subclasses must define BASE_LAYOUT_TEMPLATE
    BASE_LAYOUT_TEMPLATE = None