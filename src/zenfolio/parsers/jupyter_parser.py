"""
Jupyter notebook parser for ZenFolio.
Implements ContentParser protocol for parsing .ipynb files.
"""

from pathlib import Path
from typing import Dict, List, Any, Set
import nbformat
import frontmatter
from nbconvert import HTMLExporter
from .base_parser import ContentParser
from .markdown_parser import protect_math_blocks, restore_math_blocks
from ..utils import DEFAULT_MARKDOWN_EXTENSIONS, content_date_key


_MATH_CODE_TOKEN = "\x00zfcode{}\x00"


def _normalise_dollar_math(text: str) -> str:
    """Rewrite ``$...$`` math into the ``\\(...\\)`` form the site configures.

    Notebook authors write ``$x$``, but MathJax here is configured for
    ``\\(...\\)`` only, so the raw LaTeX rendered as literal text. This runs on the
    exported HTML rather than the cell source: markdown treats ``\\(`` as an
    escaped paren and strips the backslash. ``<pre>`` and ``<code>`` are stashed
    first so shell prompts like ``$ pip install`` are left alone.
    """
    import re

    stash: list = []

    def _keep(match):
        stash.append(match.group(0))
        return _MATH_CODE_TOKEN.format(len(stash) - 1)

    text = re.sub(r"<pre\b.*?</pre>", _keep, text, flags=re.S | re.I)
    text = re.sub(r"<code\b.*?</code>", _keep, text, flags=re.S | re.I)
    # Stash remaining tags so attribute values (hrefs with $variables in
    # rich outputs) are never rewritten.
    text = re.sub(r"<[^>]+>", _keep, text)

    text = re.sub(r"\$\$(.+?)\$\$", lambda m: r"\[" + m.group(1) + r"\]", text, flags=re.S)
    # Pandoc-style guards: an escaped \$ is literal; the opening $ must be
    # followed by non-space and the closing $ preceded by non-space and not
    # followed by a digit — so prose like "costs $10k and $2k" is left alone.
    text = re.sub(
        r"(?<![\\$])\$(?![\s$])((?:[^$\n\\]|\\.)+?)(?<![\s\\])\$(?!\d)",
        lambda m: r"\(" + m.group(1) + r"\)",
        text,
    )

    for index, original in enumerate(stash):
        text = text.replace(_MATH_CODE_TOKEN.format(index), original)
    return text


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
        """Check if this parser can handle the given file.

        Peeks at the head of the file instead of parsing the whole JSON:
        can_parse runs for every registry lookup, and notebooks can be large.
        """
        if file_path.suffix.lower() != '.ipynb':
            return False

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                head = f.read(4096).lstrip()
            return head.startswith('{') and '"cells"' in head
        except (OSError, UnicodeDecodeError):
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
            # utf-8-sig tolerates a BOM some editors prepend
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                notebook_node = nbformat.read(f, as_version=4)

            # Default metadata
            metadata = {'title': file_path.stem.replace('_', ' ').title()}
            
            # Check for frontmatter in the first markdown cell
            if notebook_node.cells and notebook_node.cells[0].cell_type == 'markdown':
                source = notebook_node.cells[0].source
                if source.strip().startswith('---'):
                    try:
                        fm = frontmatter.loads(source)
                        # Only treat the cell as frontmatter if it actually
                        # yielded metadata; a markdown cell that merely starts
                        # with a horizontal rule must be kept as content.
                        if fm.metadata:
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
                """Render markdown text to HTML with LaTeX math protection."""
                import markdown
                protected, math_blocks = protect_math_blocks(text)
                html = markdown.markdown(protected, extensions=DEFAULT_MARKDOWN_EXTENSIONS)
                return restore_math_blocks(html, math_blocks)
            
            def strip_files_prefix_filter(text: str) -> str:
                """Remove files/ prefix from paths."""
                return text.replace("files/", "")
            
            # Register filters with nbconvert's Jinja environment
            html_exporter.environment.filters['markdown'] = markdown_filter
            html_exporter.environment.filters['strip_files_prefix'] = strip_files_prefix_filter
            
            # Convert notebook to HTML
            (body, resources) = html_exporter.from_notebook_node(notebook_node)
            
            # Clean up the HTML content
            body = _normalise_dollar_math(body)
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
        
        items.sort(
            key=lambda x: content_date_key(x['metadata'].get('date', '')),
            reverse=True,
        )
        return items
    
    def get_content_processor(self, content_type: str) -> callable:
        """
        Notebook content is pre-rendered HTML, so no further processing is needed.
        """
        if content_type == 'notebook':
            return lambda content, markdown_extensions: content
        return None