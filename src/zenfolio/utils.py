"""
Shared utilities for ZenFolio - Common functions used across modules
"""

from pathlib import Path
from urllib.parse import urljoin


def build_url(base_url: str, path: str) -> str:
    """
    Build URLs that work for both debugging (relative) and deployment (absolute)
    
    Args:
        base_url: Base URL - can be empty (""), relative ("./"), or absolute ("https://example.com/")
        path: Path to append (e.g., "index.html", "static/style.css")
    
    Returns:
        Properly constructed URL
    """
    # Clean the path
    clean_path = str(path).lstrip('/')
    
    # Handle absolute URLs (deployment)
    if base_url.startswith(('http://', 'https://')):
        # For absolute URLs, use urljoin for proper handling
        return urljoin(base_url.rstrip('/') + '/', clean_path)
    
    # Handle relative URLs (debugging/local)
    if not base_url or base_url in ['', './']:
        # Simple relative path
        return clean_path
    
    # Handle custom relative base (e.g., "../" for nested pages)
    # Use pathlib for proper path joining, then convert to forward slashes for URLs
    result_path = Path(base_url) / clean_path
    # Convert to forward slashes for web URLs (works on all platforms)
    return str(result_path).replace('\\', '/')


def resolve_directory_path(path_str: str, base_dir: Path) -> Path:
    """Resolve a directory path string relative to base directory"""
    if Path(path_str).is_absolute():
        return Path(path_str)
    else:
        return base_dir / path_str


def is_external_url(path: str) -> bool:
    """Check if a path is an external URL"""
    return path.startswith(('http://', 'https://', 'mailto:', 'tel:'))


def get_theme_directory(theme_file: str) -> Path:
    """Get the directory containing a theme file"""
    return Path(theme_file).parent
