"""
Content parsers for the academic website generator
"""

from .base_parser import parser_registry
from .markdown_parser import MarkdownParser
from .jupyter_parser import JupyterParser
from .bibtex_parser import BibtexParser

# Register all the default parsers
parser_registry.register(MarkdownParser())
parser_registry.register(JupyterParser())
parser_registry.register(BibtexParser())

__all__ = ['ContentParser', 'ParserRegistry', 'parser_registry', 'MarkdownParser', 'BibtexParser', 'JupyterParser'] 