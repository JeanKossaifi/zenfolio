"""
Shared utilities for ZenFolio - Common functions used across modules
"""

import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit


def build_url(base_url: str, path: str) -> str:
    """
    Build URLs that work for both debugging (relative) and deployment (absolute)
    
    Args:
        base_url: Base URL - can be empty (""), relative ("./"), or absolute ("https://example.com/")
        path: Path to append (e.g., "index.html", "static/style.css")
    
    Returns:
        Properly constructed URL
    """
    raw_path = str(path)
    if is_external_url(raw_path):
        return raw_path
    if raw_path.startswith(("#", "?")):
        return raw_path

    clean_path = raw_path.lstrip("/")
    
    # Handle absolute URLs (deployment)
    if base_url.startswith(('http://', 'https://')):
        # For absolute URLs, use urljoin for proper handling
        return urljoin(base_url.rstrip('/') + '/', clean_path)
    
    # Handle relative URLs (debugging/local)
    if not base_url:
        return clean_path

    # URL joining must preserve explicit directory slashes, queries, and
    # fragments; pathlib intentionally normalizes those away.
    return f"{base_url.rstrip('/')}/{clean_path}"


def normalize_route(route: str, directory_default: bool = True) -> str:
    """Normalize an internal public route while preserving external URLs."""

    raw_route = (route or "/").strip()
    if is_external_url(raw_route):
        return raw_route
    if raw_route.startswith(("#", "?")):
        return raw_route
    if "\\" in raw_route:
        raise ValueError(f"Backslashes are not valid in routes: {route}")

    parsed = urlsplit(raw_route)
    decoded_path = unquote(parsed.path)
    if "\\" in decoded_path:
        raise ValueError(f"Encoded backslashes are not valid in routes: {route}")
    segments = [segment for segment in decoded_path.split("/") if segment]
    if any(segment in {".", ".."} for segment in segments):
        raise ValueError(f"Route traversal is not allowed: {route}")

    # Rebuild from non-empty segments so '/a//b' and '/a/b' normalize to the
    # same route (they map to the same output file, and the duplicate-route
    # guard compares normalized strings).
    path = "/" + "/".join(segment for segment in parsed.path.split("/") if segment)
    if path == "/":
        normalized_path = "/"
    else:
        final_segment = path.rsplit("/", 1)[-1]
        normalized_path = path
        if directory_default and "." not in final_segment:
            normalized_path += "/"
        elif parsed.path.endswith("/") and not normalized_path.endswith("/"):
            normalized_path += "/"
    return urlunsplit(("", "", normalized_path, parsed.query, parsed.fragment))


def route_to_output_path(route: str) -> Path:
    """Map a clean public route to its generated HTML path."""

    normalized = normalize_route(route)
    if is_external_url(normalized):
        raise ValueError(f"External route cannot be generated: {route}")
    parsed = urlsplit(normalized)
    if parsed.query or parsed.fragment:
        raise ValueError(
            f"Generated routes cannot contain a query or fragment: {route}"
        )
    if parsed.path == "/":
        return Path("index.html")

    clean = parsed.path.lstrip("/")
    if parsed.path.endswith("/"):
        return Path(clean) / "index.html"
    return Path(clean)


def route_depth(route: str) -> int:
    """Return the output-directory depth for a route."""

    output_path = route_to_output_path(route)
    return len(output_path.parent.parts) if output_path.parent != Path(".") else 0


def join_route(collection_route: str, slug: str) -> str:
    """Join a collection route and slug as a directory-style route."""

    base = normalize_route(collection_route)
    if is_external_url(base):
        raise ValueError("Cannot append a slug to an external collection route")
    return normalize_route(f"{base.rstrip('/')}/{slug}/")


def resolve_directory_path(path_str: str, base_dir: Path) -> Path:
    """Resolve a directory path string relative to base directory"""
    if Path(path_str).is_absolute():
        return Path(path_str)
    else:
        return base_dir / path_str


def is_external_url(path: str) -> bool:
    """Check if a path is an external URL"""
    return str(path).startswith(
        ("http://", "https://", "//", "mailto:", "tel:", "data:")
    )


def get_theme_directory(theme_file: str) -> Path:
    """Get the directory containing a theme file"""
    return Path(theme_file).parent


# Default extensions shared by every markdown rendering path so notebook and
# markdown content render consistently. SiteConfig.markdown_extensions can
# override this for theme-driven rendering.
DEFAULT_MARKDOWN_EXTENSIONS = [
    "fenced_code",
    "codehilite",
    "tables",
    "admonition",
    "def_list",
    "attr_list",
    "footnotes",
]


def content_date_key(value):
    """Sort key that tolerates mixed date types in frontmatter.

    YAML parses unquoted dates into date/datetime objects while quoted ones
    stay strings, so naive comparison raises TypeError and silently disables
    sorting. Normalize everything to (comparable-bucket, iso-string).
    """
    from datetime import date, datetime

    if isinstance(value, datetime):
        return (1, value.date().isoformat())
    if isinstance(value, date):
        return (1, value.isoformat())
    text = str(value or "").strip()
    if re.fullmatch(r"\d{4}", text):
        text = f"{text}-01-01"
    elif re.fullmatch(r"\d{4}-\d{2}", text):
        text = f"{text}-01"
    try:
        normalized = (
            datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
        )
        return (1, normalized)
    except ValueError:
        return (0, str(value or "").strip())
