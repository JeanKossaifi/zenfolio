"""
Base Theme Class for ZenFolio
Provides common Jinja2 setup and rendering functionality
"""

from datetime import datetime
from jinja2 import Environment, StrictUndefined, DebugUndefined, FileSystemLoader
from pathlib import Path
from abc import ABC, abstractmethod
from ..utils import build_url


class BaseTheme(ABC):
    """Base class for all ZenFolio themes with common Jinja2 functionality"""
    
    def __init__(self, template_dir: Path = None, debug=False):
        # Configure Jinja2 environment with debugging options
        undefined_handler = StrictUndefined if debug else DebugUndefined
        
        loader = FileSystemLoader(template_dir) if template_dir else None
        
        self.env = Environment(
            loader=loader,
            trim_blocks=True, 
            lstrip_blocks=True,
            undefined=undefined_handler
        )
        self.env.globals['theme'] = self
        
        # Add a global url_for function for page links
        def url_for(path: str) -> str:
            base_url = self.env.globals.get('base_url', '')
            return build_url(base_url, path)

        # Add a global file function for static files
        def file(path: str) -> str:
            base_url = self.env.globals.get('base_url', '')
            return build_url(base_url, f'static/{path.lstrip("/")}')

        self.env.globals['url_for'] = url_for
        self.env.globals['file'] = file
        
        # Register all custom filters
        self.env.filters['strip_files_prefix'] = self._strip_files_prefix_filter
        self.env.filters['markdown'] = self._markdown_filter
        self.env.filters['highlight_code'] = self._highlight_code_filter

        self.debug = debug
        self.env.globals['theme'] = self
        
        self._register_templates()

    def _highlight_code_filter(self, code: str, **kwargs) -> str:
        """A placeholder for syntax highlighting."""
        return f'<pre><code>{code}</code></pre>'

    def _markdown_filter(self, text: str) -> str:
        """Render markdown text to HTML."""
        import markdown
        return markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables', 'admonition', 'def_list', 'attr_list', 'footnotes'])

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
        """Render a component template with given context, with robust error handling"""
        template = self.env.globals.get(component_name)
        if template:
            try:
                return template.render(**kwargs)
            except Exception as e:
                error_msg = f"❌ Template rendering failed for '{component_name}': {str(e)}"
                if self.debug:
                    print(error_msg)
                    import traceback
                    traceback.print_exc()
                return f"<!-- {error_msg} -->"
        else:
            # Missing template - this should NOT be silent!
            error_msg = f"❌ Missing template: '{component_name}'"
            if self.debug:
                print(error_msg)
                available_templates = [k for k in self.env.globals.keys() if not k.startswith('_')]
                print(f"💡 Available templates: {available_templates}")
            return f"<!-- {error_msg} -->"
    
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
        # Make base_url available to the url_for global function
        self.env.globals['base_url'] = base_url
        
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
                current_year=datetime.now().year)
        
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