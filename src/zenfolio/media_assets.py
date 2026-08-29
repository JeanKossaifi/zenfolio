"""Build-time preparation of cached remote media assets."""

from pathlib import Path
import re
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


ThumbnailFetcher = Callable[[str, float], bytes]


def youtube_video_id(url: str) -> Optional[str]:
    """Return a YouTube video id from common public URL forms."""
    if not url:
        return None

    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]

    candidate = ""
    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif host in {"youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [""])[0]
        else:
            match = re.match(r"^/(?:embed|shorts|live)/([^/?#]+)", parsed.path)
            if match:
                candidate = match.group(1)

    return candidate if re.fullmatch(r"[A-Za-z0-9_-]{6,}", candidate) else None


def _download_thumbnail(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": "ZenFolio/0.1"})
    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise OSError(f"HTTP {status}")
        data = response.read()
    if not data.startswith(b"\xff\xd8"):
        raise OSError("response was not a JPEG image")
    return data


def _get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _set(item: Any, key: str, value: Any) -> None:
    if isinstance(item, dict):
        item[key] = value
    else:
        setattr(item, key, value)


def prepare_talk_thumbnails(
    content_dir: Path,
    talks_config: Any,
    *,
    fetcher: ThumbnailFetcher = _download_thumbnail,
    timeout: float = 10.0,
) -> None:
    """Resolve cached thumbnails and optionally fetch missing YouTube images.

    The cache lives in the site's source ``static/images/talks`` directory,
    so subsequent and offline builds reuse it. Download failures are warnings:
    the rendered theme can then use its image-free fallback without emitting a
    broken ``img`` element.
    """
    if not talks_config:
        return

    items = _get(talks_config, "items", []) or []
    fetch_missing = bool(
        _get(talks_config, "cache_video_thumbnails", False)
    )
    static_dir = Path(content_dir) / "static"

    for talk in items:
        explicit = _get(talk, "thumbnail")
        if explicit:
            continue

        video_id = youtube_video_id(_get(talk, "video", "") or "")
        if not video_id:
            continue

        relative_path = Path("images") / "talks" / f"{video_id}.jpg"
        target = static_dir / relative_path
        if target.is_file() and target.stat().st_size:
            _set(talk, "thumbnail", relative_path.as_posix())
            continue

        if not fetch_missing:
            continue

        url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        try:
            data = fetcher(url, timeout)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".jpg.tmp")
            temporary.write_bytes(data)
            temporary.replace(target)
            _set(talk, "thumbnail", relative_path.as_posix())
            print(
                "🖼️  Cached talk thumbnail "
                f"{relative_path.as_posix()} ({len(data)} bytes)"
            )
        except Exception as error:
            print(
                f"⚠️  Warning: Could not cache talk thumbnail {url}: {error}. "
                "Using the theme fallback."
            )
