"""
Elysian Theme - Sophisticated Academic Design System
v5.5 - Final. Implemented timeline, perfected hero section and homepage flow.
"""

from datetime import datetime
from pathlib import Path
from ..base_theme import BaseTheme
from ...utils import get_theme_directory

class TailwindTheme(BaseTheme):
    """Elysian academic theme - loads all templates from the /templates directory."""
    
    def __init__(self, debug=False):
        self.theme_dir = get_theme_directory(__file__)
        self.template_dir = self.theme_dir / "templates"
        super().__init__(template_dir=self.template_dir, debug=debug)
        self.env.globals['render_component'] = self.render_component
        # Ensure base_layout_template is loaded
        if not hasattr(self, 'base_layout_template') or self.base_layout_template is None:
            self.base_layout_template = self.env.get_template("base_layout.html.j2")
    
    def _register_templates(self):
        """Load all component templates with shared template fallback."""
        # The base layout is the foundation
        try:
            self.base_layout_template = self.env.get_template("base_layout.html.j2")
        except Exception as e:
            raise RuntimeError(f"❌ Critical: base_layout.html.j2 template missing or invalid: {e}")

        # Define required templates for robust operation
        required_templates = {
            'news_item', 'blog_post_item', 'project_item', 'service_item', 
            'publication_item', 'section', 'profile_hero'
        }
        
        loaded_templates = set()

        # Load all Tailwind templates
        for template_path in self.template_dir.glob("*.html.j2"):
            if template_path.name != "base_layout.html.j2":
                component_name = template_path.stem.replace(".html", "")
                try:
                    self.env.globals[component_name] = self.env.get_template(template_path.name)
                    loaded_templates.add(component_name)
                    if self.debug:
                        print(f"✅ Loaded template: {component_name}")
                except Exception as e:
                    print(f"⚠️ Failed to load template '{component_name}': {e}")
        
        # For missing templates, try to load from shared Minimal templates
        minimal_template_dir = get_theme_directory(__file__).parent / "minimal" / "templates"
        for template_path in minimal_template_dir.glob("*.html.j2"):
            component_name = template_path.stem.replace(".html", "")
            if component_name not in loaded_templates:
                try:
                    # Load the shared template directly
                    template_content = template_path.read_text()
                    self.env.globals[component_name] = self.env.from_string(template_content)
                    loaded_templates.add(component_name)
                    if self.debug:
                        print(f"✅ Loaded shared template: {component_name}")
                except Exception as e:
                    if self.debug:
                        print(f"⚠️ Failed to load shared template '{component_name}': {e}")
        
        # Validate critical templates are present
        missing_required = required_templates - loaded_templates
        if missing_required:
            error_msg = f"❌ Missing required templates: {missing_required}"
            print(error_msg)
            if self.debug:
                print(f"💡 Available templates: {loaded_templates}")
                print(f"💡 Template directory: {self.template_dir}")
            # Don't fail the build, but warn loudly
            print("⚠️ This may cause sections to render as empty!")
        elif self.debug:
            print(f"✅ All {len(loaded_templates)} templates loaded successfully")
    
    def write_css_file(self, output_dir: Path):
        """Copies the pre-built theme.css file to the output directory."""
        import shutil
        
        static_dir = output_dir / "static"
        static_dir.mkdir(exist_ok=True)
        
        theme_css_path = self.theme_dir / "css" / "theme.css"
        output_css_path = static_dir / "theme.css"
        
        if theme_css_path.exists():
            shutil.copy2(theme_css_path, output_css_path)
            if self.debug:
                print(f"✅ Copied CSS to {output_css_path}")
        else:
            print(f"⚠️ Warning: Pre-built theme.css not found at {theme_css_path}")
            print("💡 You may need to run 'npm run build' in the theme directory.")
    
    def write_js_file(self, output_dir: Path):
        """Copies the theme's JavaScript file to the output directory."""
        static_dir = output_dir / "static"
        static_dir.mkdir(exist_ok=True)
        
        theme_js_path = self.theme_dir / "js" / "theme.js"
        output_js_path = static_dir / "theme.js"
        
        if theme_js_path.exists():
            import shutil
            shutil.copy2(theme_js_path, output_js_path)
    
    def render_component(self, component_name: str, **kwargs) -> str:
        """Render a component template with given context, providing defaults for base_layout requirements."""
        template = self.env.globals.get(component_name)
        if template:
            # For templates that extend base_layout, provide default values for required variables
            if component_name in ['page_layout', 'section'] and 'mathjax_html' not in kwargs:
                # Render MathJax configuration if config is available
                mathjax_config = kwargs.get('mathjax_config')
                kwargs['mathjax_html'] = self.render_component('mathjax', mathjax_config=mathjax_config) if mathjax_config else ""
            
            return template.render(**kwargs)
        return ""
    
    def render_page(self, content: str, page_title: str = "", author_name: str = "",
                    site_description: str = "", base_url: str = "", **context) -> str:
        """Renders a complete page using the base layout template."""
        # Make base_url available to the url_for and file global functions
        self.env.globals['base_url'] = base_url
        
        # Pre-render modular components
        navbar_html = self.render_component('navbar', author_name=author_name, base_url=base_url, **context)
        footer_html = self.render_component('footer', author=context.get('author'), author_name=author_name, current_year=datetime.now().year)
        seo_head_html = self.render_component('seo_head', page_title=page_title, author_name=author_name, site_description=site_description, **context)
        
        # Render MathJax configuration
        mathjax_config = context.get('mathjax_config')
        mathjax_html = self.render_component('mathjax', mathjax_config=mathjax_config) if mathjax_config else ""
        
        return self.base_layout_template.render(
            content=content,
            navbar=navbar_html,
            footer=footer_html,
            seo_head=seo_head_html,
            mathjax_html=mathjax_html,
            page_title=page_title,
            author_name=author_name,
            site_description=site_description,
            base_url=base_url,
            **context
        )



