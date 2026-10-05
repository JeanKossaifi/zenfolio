"""Validated, path-resolved context for one ZenFolio build."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from zencfg import load_config_from_file

from .errors import ZenFolioBuildError
from .models.site_config import AuthorConfig, GroupConfig
from .theme_loader import load_theme
from .utils import resolve_directory_path


@dataclass
class BuildContext:
    content_dir: Path
    config: Any
    identity: Any
    site_type: str
    static_dir: Path
    output_dir: Path
    theme: Any
    theme_override: Optional[str]
    debug: bool

    @classmethod
    def create(
        cls,
        content_dir: Path,
        theme_override: Optional[str] = None,
        output_override: Optional[Path] = None,
        debug: bool = False,
    ) -> "BuildContext":
        resolved_content = Path(content_dir).expanduser().resolve()
        normalized_theme_override = (
            theme_override.lower() if theme_override else None
        )
        config = load_config_from_file(
            resolved_content, "config.py", "config"
        )

        site_type = str(getattr(config, "site_type", "person")).lower()
        if site_type not in {"person", "group"}:
            raise ZenFolioBuildError("site_type must be 'person' or 'group'")

        identity = config.identity
        if site_type == "group" and not isinstance(identity, GroupConfig):
            raise ZenFolioBuildError(
                "Group sites require identity=GroupConfig(...)"
            )
        if site_type == "person" and not isinstance(identity, AuthorConfig):
            raise ZenFolioBuildError(
                "Personal sites require an AuthorConfig identity"
            )

        static_dir = resolve_directory_path(config.static_path, resolved_content)
        output_dir = resolve_directory_path(
            output_override or config.output_path, resolved_content
        )
        theme = load_theme(
            config,
            resolved_content,
            normalized_theme_override,
            debug,
        )
        return cls(
            content_dir=resolved_content,
            config=config,
            identity=identity,
            site_type=site_type,
            static_dir=static_dir,
            output_dir=output_dir,
            theme=theme,
            theme_override=normalized_theme_override,
            debug=debug,
        )
