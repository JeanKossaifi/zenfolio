"""
Base parser protocol for ZenFolio content parsers.
Defines the standard interface that all parsers must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Set


class ContentParser(ABC):
    """
    Abstract base class for all content parsers.
    
    Each parser is responsible for:
    1. Declaring which file extensions it can handle
    2. Parsing individual files into structured data
    3. Processing directories of content
    4. Declaring what content types it produces
    """
    
    @property
    @abstractmethod
    def supported_extensions(self) -> Set[str]:
        """
        Return the set of file extensions this parser can handle.
        Example: {'.md', '.markdown'}
        """
        pass
    
    @property
    @abstractmethod
    def content_types(self) -> Set[str]:
        """
        Return the set of content types this parser can produce.
        Example: {'blog_post', 'page', 'bio'}
        """
        pass
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this parser can handle the file, False otherwise
        """
        pass
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a single file into structured data.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dictionary with 'metadata' and 'content' keys, or empty dict if parsing fails
        """
        pass
    
    @abstractmethod
    def parse_directory(self, directory_path: Path, content_type: str = None) -> List[Dict[str, Any]]:
        """
        Parse all supported files in a directory.
        
        Args:
            directory_path: Path to the directory to scan
            content_type: Optional content type filter
            
        Returns:
            List of parsed content dictionaries
        """
        pass
    
    def get_content_processor(self, content_type: str) -> callable:
        """
        Get a content processor function for the given content type.
        Default implementation returns None (no special processing).
        
        Args:
            content_type: Type of content to process
            
        Returns:
            Function that takes (content_string) -> processed_content_string, or None
        """
        return None


class ParserRegistry:
    """
    Registry for managing content parsers.
    Allows dynamic registration and discovery of parsers by file type.
    """
    
    def __init__(self):
        self._parsers: List[ContentParser] = []
        self._extension_map: Dict[str, List[ContentParser]] = {}
    
    def register(self, parser: ContentParser):
        """Register a parser with the registry."""
        if parser not in self._parsers:
            self._parsers.append(parser)
            
            # Update extension mapping
            for ext in parser.supported_extensions:
                if ext not in self._extension_map:
                    self._extension_map[ext] = []
                if parser not in self._extension_map[ext]:
                    self._extension_map[ext].append(parser)
    
    def get_parser_for_file(self, file_path: Path) -> ContentParser:
        """
        Get the best parser for a given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Parser instance that can handle the file, or None if no parser found
        """
        extension = file_path.suffix.lower()
        
        # Check extension-based parsers first
        if extension in self._extension_map:
            for parser in self._extension_map[extension]:
                if parser.can_parse(file_path):
                    return parser
        
        # Fallback: check all parsers
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser
                
        return None
    
    def get_parsers_for_content_type(self, content_type: str) -> List[ContentParser]:
        """Get all parsers that can produce the given content type."""
        return [p for p in self._parsers if content_type in p.content_types]
    
    def get_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions across all parsers."""
        return set(self._extension_map.keys())


# Global parser registry instance
parser_registry = ParserRegistry()