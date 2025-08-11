"""
Markdown parser for content files, powered by the python-frontmatter library.
v3.0 - Implements ContentParser protocol for extensible parsing system.
"""

from pathlib import Path
from typing import Dict, List, Any, Set
import frontmatter
import textwrap
from .base_parser import ContentParser

class MarkdownParser(ContentParser):
    """
    Parser for markdown content files with YAML frontmatter.
    This class is responsible for reading files and returning structured, raw data.
    """
    
    @property
    def supported_extensions(self) -> Set[str]:
        """Markdown file extensions this parser can handle."""
        return {'.md', '.markdown', '.mdown', '.mkd'}
    
    @property
    def content_types(self) -> Set[str]:
        """Content types this parser can produce."""
        return {'blog_post', 'page', 'bio'}
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions
    
    def get_content_processor(self, content_type: str) -> callable:
        """Return markdown processing function for content types."""
        def process_markdown(content: str, markdown_extensions: List[str]) -> str:
            """Process markdown content with normalization."""
            import markdown
            normalized_content = textwrap.dedent(content).strip()
            return markdown.markdown(normalized_content, extensions=markdown_extensions)
        return process_markdown
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parses a single markdown file with frontmatter into its metadata and content.
        
        Returns:
            A dictionary with 'metadata' (from frontmatter) and 'content' (raw markdown),
            or an empty dictionary if the file doesn't exist or fails to parse.
        """
        if not file_path.exists():
            return {}
        
        try:
            post = frontmatter.load(file_path)
            metadata = post.metadata.copy() if post.metadata else {}
            
            # For all files, return standard format
            return {
                "metadata": metadata,
                "content": post.content
            }
        except Exception as e:
            print(f"⚠️  Error parsing file {file_path}: {e}")
            return {}

    def parse_directory(self, directory_path: Path, content_type: str = None) -> List[Dict[str, Any]]:
        """
        Parses all markdown files in a directory, adding the slug.
        
        Returns:
            A list of dictionaries, each representing a parsed file.
        """
        items = []
        if not directory_path.exists():
            return items
            
        # Scan for all supported file types
        for file_path in directory_path.iterdir():
            if file_path.is_file() and self.can_parse(file_path):
                if file_path.name.startswith(('_', '.')):
                    continue
                
                parsed_data = self.parse_file(file_path)
                if parsed_data:
                    # Add the filename stem as the default slug, which can be overridden in frontmatter
                    parsed_data['metadata']['slug'] = parsed_data['metadata'].get('slug', file_path.stem)
                    items.append(parsed_data)
        
        # Sort by date if available, descending
        try:
            items.sort(key=lambda x: x['metadata'].get('date', ''), reverse=True)
        except TypeError:
            pass # Handle cases where dates might not be comparable
            
        return items