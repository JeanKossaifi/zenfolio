"""Filesystem-backed themes for private or site-specific designs."""

from datetime import datetime
import hashlib
from pathlib import Path
import shutil
from typing import Optional

from .base_theme import BaseTheme


class LocalTheme(BaseTheme):
    """Load a complete theme from a content repository.

    A local theme is built directly on :class:`BaseTheme`. An optional parent
    directory only supplies template and asset fallbacks; Python subclassing is
    deliberately unnecessary.
    """

    def __init__(
        self,
        theme_dir: Path,
        debug: bool = False,
        parent_theme_dir: Optional[Path] = None,
        shared_template_dir: Optional[Path] = None,
    ):
        self.theme_dir = Path(theme_dir).resolve()
        self.parent_theme_dir = (
            Path(parent_theme_dir).resolve() if parent_theme_dir else None
        )
        self.template_dir = self.theme_dir / "templates"
        if not self.template_dir.is_dir():
            raise FileNotFoundError(
                f"Local theme template directory not found: {self.template_dir}"
            )

        super().__init__(
            template_dirs=[self.template_dir],
            parent_template_dir=(
                self.parent_theme_dir / "templates"
                if self.parent_theme_dir
                else None
            ),
            shared_template_dir=shared_template_dir,
            debug=debug,
        )

    def _register_templates(self):
        loaded = self.register_file_templates()
        required = {
            "base_layout",
            "navbar",
            "footer",
            "landing_page",
            "section",
            "page_layout",
            "page",
            "mathjax",
        }
        missing = required - loaded
        if missing:
            raise RuntimeError(
                f"Local theme is missing required templates: {sorted(missing)}"
            )
        self.base_layout_template = self.env.get_template("base_layout.html.j2")

    @staticmethod
    def _copy_asset_tree(theme_dir: Path, output_dir: Path) -> None:
        static_dir = output_dir / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        css_path = theme_dir / "css" / "theme.css"
        if css_path.exists():
            shutil.copy2(css_path, static_dir / "theme.css")

        js_path = theme_dir / "js" / "theme.js"
        if js_path.exists():
            shutil.copy2(js_path, static_dir / "theme.js")

        assets_path = theme_dir / "assets"
        if assets_path.is_dir():
            shutil.copytree(
                assets_path,
                static_dir / "theme",
                dirs_exist_ok=True,
            )

    def write_css_file(self, output_dir: Path):
        if self.parent_theme_dir:
            self._copy_asset_tree(self.parent_theme_dir, output_dir)
        self._copy_asset_tree(self.theme_dir, output_dir)

        compiled_css = self.theme_dir / "css" / "theme.css"
        if not compiled_css.exists():
            raise FileNotFoundError(
                f"Pre-built theme CSS is required at {compiled_css}. "
                "Run 'npm run build' in the local theme directory."
            )
        source_css = self.theme_dir / "css" / "input.css"
        if source_css.exists():
            hash_path = self.theme_dir / "css" / ".input.sha256"
            current_hash = hashlib.sha256(source_css.read_bytes()).hexdigest()
            recorded_hash = (
                hash_path.read_text(encoding="utf-8").strip()
                if hash_path.exists()
                else ""
            )
            if recorded_hash != current_hash:
                raise RuntimeError(
                    f"Compiled theme CSS is stale: {compiled_css}. "
                    "Run 'npm run build' in the local theme directory."
                )

    def write_js_file(self, output_dir: Path):
        # CSS writing copies the complete deterministic asset overlay.
        return None

    def render_page(
        self,
        content: str,
        page_title: str = "",
        author_name: str = "",
        site_description: str = "",
        base_url: str = "",
        **context,
    ) -> str:
        self.set_render_context(base_url)
        navbar_html = self.render_component(
            "navbar",
            author_name=author_name,
            **context,
        )
        footer_html = self.render_component(
            "footer",
            author_name=author_name,
            current_year=datetime.now().year,
            **context,
        )
        mathjax_config = context.get("mathjax_config")
        mathjax_html = (
            self.render_component("mathjax", mathjax_config=mathjax_config)
            if mathjax_config
            else ""
        )
        return self.base_layout_template.render(
            content=content,
            navbar=navbar_html,
            footer=footer_html,
            mathjax_html=mathjax_html,
            page_title=page_title,
            author_name=author_name,
            site_description=site_description,
            base_url=base_url,
            **context,
        )
