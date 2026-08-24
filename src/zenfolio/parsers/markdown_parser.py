"""
Markdown parser for content files, powered by the python-frontmatter library.
Provides LaTeX math protection so markdown does not mangle equations.
Implements the ContentParser protocol.
"""

from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import frontmatter
import textwrap
import re
from .base_parser import ContentParser
from ..utils import content_date_key


# =============================================================================
# Math Protection Utilities
# =============================================================================
# Standard approach used by Pelican, MkDocs, and other Python-based SSGs
# to prevent Python-Markdown from processing LaTeX syntax

def protect_math_blocks(content: str) -> Tuple[str, List[str]]:
    """
    Extract LaTeX math blocks before markdown processing.
    
    Prevents markdown from converting _ to <em> inside math expressions.
    
    Args:
        content: Markdown content with LaTeX math
        
    Returns:
        Tuple of (protected_content, extracted_math_blocks)
    """
    math_blocks = []

    def save_math(match):
        """Save math block and return placeholder."""
        math_blocks.append(match.group(0))
        # Use HTML comment as placeholder - markdown won't touch it
        return f"<!--MATHBLOCK{len(math_blocks)-1}-->"

    # Shield code fences and inline code spans first: `$$ ... $$` inside a
    # code block is code, not math, and extracting it would leave an
    # unrestorable placeholder in the rendered output.
    code_spans = []

    def save_code(match):
        code_spans.append(match.group(0))
        return f"\x00CODESPAN{len(code_spans)-1}\x00"

    content = re.sub(r'^(`{3,}|~{3,}).*?^\1[ \t]*$', save_code, content,
                     flags=re.DOTALL | re.MULTILINE)
    content = re.sub(r'`[^`\n]+`', save_code, content)

    # Extract math in order: display math first (longer), then inline
    # Use DOTALL to handle multi-line equations
    # In raw strings, r'\(' matches literal backslash-paren in the text
    content = re.sub(r'\\\[.*?\\\]', save_math, content, flags=re.DOTALL)  # Display: \[...\]
    content = re.sub(r'\$\$.*?\$\$', save_math, content, flags=re.DOTALL)   # Display: $$...$$
    content = re.sub(r'\\\(.*?\\\)', save_math, content, flags=re.DOTALL)   # Inline: \(...\)

    # Put code back before markdown runs so fences render normally. A code
    # placeholder can also end up INSIDE a captured math block (e.g. a
    # backtick span between $$ delimiters), so restore those too.
    for i, span in enumerate(code_spans):
        placeholder = f"\x00CODESPAN{i}\x00"
        content = content.replace(placeholder, span)
        math_blocks[:] = [
            block.replace(placeholder, span) for block in math_blocks
        ]

    return content, math_blocks


def restore_math_blocks(content: str, math_blocks: List[str]) -> str:
    """
    Restore LaTeX math blocks after markdown processing.
    
    Args:
        content: HTML content with math placeholders
        math_blocks: List of original math blocks
        
    Returns:
        HTML with math blocks restored (with single backslashes for MathJax)
    """
    for i, math_block in enumerate(math_blocks):
        content = content.replace(f"<!--MATHBLOCK{i}-->", math_block)
    return content

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
        return {'blog_post', 'page', 'bio', 'markdown'}
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions
    
    def get_content_processor(self, content_type: str) -> callable:
        """Return markdown processing function with LaTeX math protection."""
        def process_markdown(content: str, markdown_extensions: List[str]) -> str:
            """
            Process markdown content with LaTeX math protection.
            
            Uses industry-standard approach: extract math blocks before markdown
            processing, then restore them after to prevent markdown from breaking
            LaTeX syntax (e.g., converting _ to <em>).
            """
            import markdown
            
            normalized_content = textwrap.dedent(content).strip()
            
            # Protect LaTeX math from markdown processing
            protected_content, math_blocks = protect_math_blocks(normalized_content)
            
            # Process markdown
            html = markdown.markdown(protected_content, extensions=markdown_extensions)
            
            # Restore math blocks
            html = restore_math_blocks(html, math_blocks)
            
            return html
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
            # utf-8-sig strips a UTF-8 BOM, which would otherwise defeat
            # frontmatter detection and leak the YAML block into the page.
            with open(file_path, 'r', encoding='utf-8-sig') as fh:
                post = frontmatter.load(fh)
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
        items.sort(
            key=lambda x: content_date_key(x['metadata'].get('date', '')),
            reverse=True,
        )
        return items