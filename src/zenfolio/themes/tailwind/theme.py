"""File-backed Tailwind theme."""

from datetime import datetime
from pathlib import Path
import shutil

from ..base_theme import BaseTheme
from ...utils import get_theme_directory


class TailwindTheme(BaseTheme):
    """Load the built-in Tailwind templates and compiled assets."""

    REQUIRED_TEMPLATES = {
        "base_layout",
        "navbar",
        "footer",
        "landing_page",
        "page_layout",
        "page",
        "blog_post_page",
        "news_item",
        "blog_post_item",
        "project_item",
        "service_item",
        "publication_item",
        "section",
        "profile_hero",
    }

    def __init__(self, debug=False):
        self.theme_dir = get_theme_directory(__file__)
        self.template_dir = self.theme_dir / "templates"
        shared_template_dir = self.theme_dir.parent / "minimal" / "templates"
        super().__init__(
            template_dirs=[self.template_dir],
            shared_template_dir=shared_template_dir,
            debug=debug,
        )
    
    def _register_templates(self):
        """Load all component templates with shared template fallback."""
        try:
            self.base_layout_template = self.env.get_template("base_layout.html.j2")
        except Exception as error:
            raise RuntimeError(
                "❌ Critical: base_layout.html.j2 template missing or "
                f"invalid: {error}"
            ) from error

        loaded_templates = self.register_file_templates()
        missing_required = self.REQUIRED_TEMPLATES - loaded_templates
        if missing_required:
            raise RuntimeError(
                f"Missing required Tailwind templates: {sorted(missing_required)}"
            )
        if self.debug:
            print(f"✅ All {len(loaded_templates)} templates loaded successfully")
    
    def write_css_file(self, output_dir: Path):
        """Copies the pre-built theme.css file to the output directory."""
        static_dir = output_dir / "static"
        static_dir.mkdir(exist_ok=True)
        theme_css_path = self.theme_dir / "css" / "theme.css"
        output_css_path = static_dir / "theme.css"

        if not theme_css_path.exists():
            raise FileNotFoundError(
                f"Pre-built theme.css not found at {theme_css_path}. "
                "Run 'npm run build' in the theme directory."
            )
        shutil.copy2(theme_css_path, output_css_path)
        if self.debug:
            print(f"✅ Copied CSS to {output_css_path}")

    def write_js_file(self, output_dir: Path):
        """Copies the theme's JavaScript file to the output directory."""
        static_dir = output_dir / "static"
        static_dir.mkdir(exist_ok=True)
        theme_js_path = self.theme_dir / "js" / "theme.js"
        output_js_path = static_dir / "theme.js"
        if theme_js_path.exists():
            shutil.copy2(theme_js_path, output_js_path)
    
    def render_page(
        self,
        content: str,
        page_title: str = "",
        author_name: str = "",
        site_description: str = "",
        base_url: str = "",
        **context,
    ) -> str:
        """Renders a complete page using the base layout template."""
        self.set_render_context(base_url)

        navbar_html = self.render_component(
            "navbar",
            author_name=author_name,
            base_url=base_url,
            **context,
        )
        footer_html = self.render_component(
            "footer",
            author=context.get("author"),
            identity=context.get("identity"),
            author_name=author_name,
            current_year=datetime.now().year,
            navigation=context.get("navigation", []),
        )
        # base_layout.html.j2 carries its own meta block; the shared
        # seo_head component is only used by the minimal theme.
        mathjax_config = context.get("mathjax_config")
        mathjax_html = (
            self.render_component(
                "mathjax", mathjax_config=mathjax_config
            )
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



