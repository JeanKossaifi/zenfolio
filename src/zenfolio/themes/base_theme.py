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
    Template,
    select_autoescape,
)
from markupsafe import Markup
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Iterable, Optional

import markdown

from ..utils import (
    DEFAULT_MARKDOWN_EXTENSIONS,
    build_url,
    is_external_url,
    normalize_route,
)


class ThemeRenderError(RuntimeError):
    """Raised when a required theme template cannot be loaded or rendered."""


class BaseTheme(ABC):
    """Base class for all ZenFolio themes with common Jinja2 functionality"""

    MARKDOWN_EXTENSIONS = DEFAULT_MARKDOWN_EXTENSIONS
    
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
                # Inline (from_string) templates must escape too: publication
                # titles and venues routinely contain &, <, and quotes.
                # Intentional raw-HTML slots are marked with `| safe`.
                default_for_string=True,
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
        self.env.filters['markdown'] = self._markdown_filter

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

    def _markdown_filter(self, text: str) -> Markup:
        """Render markdown text to HTML."""
        return Markup(
            markdown.markdown(text, extensions=self.MARKDOWN_EXTENSIONS)
        )

    @abstractmethod
    def _register_templates(self):
        """Register theme-specific templates - must be implemented by subclasses"""
        pass
    
    def has_component(self, component_name: str) -> bool:
        """Return whether a component template is registered."""

        return isinstance(self.env.globals.get(component_name), Template)

    def render_component(self, component_name: str, **kwargs) -> Markup:
        """Render a required component or fail the build.

        Returns Markup so nested `theme.render_component(...)` calls inside
        autoescaped templates are not double-escaped.
        """

        template = self.env.globals.get(component_name)
        if template is None:
            available = sorted(
                key
                for key, value in self.env.globals.items()
                if isinstance(value, Template)
            )
            raise ThemeRenderError(
                f"Missing required template '{component_name}'. "
                f"Available components: {', '.join(available)}"
            )
        try:
            return Markup(template.render(**kwargs))
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

        if self.BASE_LAYOUT_TEMPLATE is None:
            raise ThemeRenderError(
                f"{type(self).__name__} must define BASE_LAYOUT_TEMPLATE "
                "or override render_page()."
            )
        if self._compiled_base_layout is None:
            self._compiled_base_layout = self.env.from_string(
                self.BASE_LAYOUT_TEMPLATE
            )
        template = self._compiled_base_layout
        
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
    
    # Subclasses must define BASE_LAYOUT_TEMPLATE or override render_page().
    BASE_LAYOUT_TEMPLATE = None
    _compiled_base_layout = None