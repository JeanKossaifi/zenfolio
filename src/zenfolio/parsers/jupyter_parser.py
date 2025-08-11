"""
Jupyter notebook parser for ZenFolio.
Implements ContentParser protocol for parsing .ipynb files.
"""

from pathlib import Path
from typing import Dict, List, Any, Set
import json
import nbformat
import frontmatter
from nbconvert import HTMLExporter
from .base_parser import ContentParser


class JupyterParser(ContentParser):
    """
    Parser for Jupyter notebook files (.ipynb).
    
    Extracts metadata from the first markdown cell (if formatted as frontmatter)
    and returns the raw notebook content for further processing.
    """
    
    @property
    def supported_extensions(self) -> Set[str]:
        """Jupyter notebook file extensions."""
        return {'.ipynb'}
    
    @property
    def content_types(self) -> Set[str]:
        """Content types this parser can produce."""
        return {'blog_post', 'page', 'notebook'}
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        if file_path.suffix.lower() != '.ipynb':
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return isinstance(data, dict) and 'cells' in data
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
            return False
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Jupyter notebook file.
        
        Returns:
            Dictionary with 'metadata' and 'content' keys, where content is the raw notebook
            node that can be processed by nbconvert later.
        """
        if not file_path.exists():
            return {}
        
        try:
            # Read the notebook
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook_node = nbformat.read(f, as_version=4)

            # Default metadata
            metadata = {'title': file_path.stem.replace('_', ' ').title()}
            
            # Check for frontmatter in the first markdown cell
            if notebook_node.cells and notebook_node.cells[0].cell_type == 'markdown':
                source = notebook_node.cells[0].source
                if source.strip().startswith('---'):
                    try:
                        fm = frontmatter.loads(source)
                        metadata.update(fm.metadata)
                        # Remove the frontmatter cell before converting
                        notebook_node.cells.pop(0)
                    except Exception:
                        pass  # Not valid frontmatter, treat as normal markdown
            
            # Add content type to metadata
            metadata['content_type'] = 'notebook'
            
            # Use our custom template for clean, semantic HTML
            html_exporter = HTMLExporter()
            template_path = Path(__file__).parent.parent / 'themes' / 'tailwind' / 'templates'
            html_exporter.template_paths.insert(0, str(template_path))
            html_exporter.template_file = 'notebook.html.j2'
            html_exporter.exclude_input = False
            
            # Add missing filters to the nbconvert environment
            def markdown_filter(text: str) -> str:
                """Render markdown text to HTML."""
                import markdown
                return markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables', 'admonition', 'def_list', 'attr_list', 'footnotes'])
            
            def strip_files_prefix_filter(text: str) -> str:
                """Remove files/ prefix from paths."""
                return text.replace("files/", "")
            
            # Register filters with nbconvert's Jinja environment
            html_exporter.environment.filters['markdown'] = markdown_filter
            html_exporter.environment.filters['strip_files_prefix'] = strip_files_prefix_filter
            
            # Convert notebook to HTML
            (body, resources) = html_exporter.from_notebook_node(notebook_node)
            
            # Clean up the HTML content
            body = self._clean_notebook_html(body)
            
            # Return the HTML content
            return {
                "metadata": metadata,
                "content": body
            }
            
        except Exception as e:
            print(f"❌ Error parsing notebook {file_path}: {e}")
            return {}
    
    def _clean_notebook_html(self, html_content: str) -> str:
        """
        Clean up notebook HTML content by removing unwanted elements.
        """
        import re
        
        # Remove pilcrow anchor links (¶ symbols)
        html_content = re.sub(r'<a\s+class="anchor-link"\s+href="[^"]*">¶</a>', '', html_content)
        
        # Remove empty anchor links
        html_content = re.sub(r'<a\s+class="anchor-link"[^>]*></a>', '', html_content)
        
        # Clean up any remaining anchor-link references
        html_content = re.sub(r'<a[^>]*class="anchor-link"[^>]*>.*?</a>', '', html_content, flags=re.DOTALL)
        
        return html_content
    
    def parse_directory(self, directory_path: Path, content_type: str = None) -> List[Dict[str, Any]]:
        """
        Parse all Jupyter notebooks in a directory.
        """
        items = []
        if not directory_path.exists():
            return items
        
        for file_path in directory_path.iterdir():
            if file_path.is_file() and self.can_parse(file_path):
                if file_path.name.startswith(('_', '.', 'Untitled')):
                    continue
                
                parsed_data = self.parse_file(file_path)
                if parsed_data:
                    parsed_data['metadata']['slug'] = parsed_data['metadata'].get('slug', file_path.stem)
                    parsed_data['metadata']['content_type'] = 'notebook'
                    items.append(parsed_data)
        
        try:
            items.sort(key=lambda x: x['metadata'].get('date', ''), reverse=True)
        except TypeError:
            pass
        
        return items
    
    def get_content_processor(self, content_type: str) -> callable:
        """
        Notebook content is pre-rendered HTML, so no further processing is needed.
        """
        if content_type == 'notebook':
            return lambda content, markdown_extensions: content
        return None