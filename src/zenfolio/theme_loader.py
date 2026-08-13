"""Built-in and site-local theme selection."""

from pathlib import Path
from typing import Any, Optional

from .errors import ZenFolioBuildError
from .themes import LocalTheme, MinimalTheme, TailwindTheme


BUILTIN_THEMES = {
    "minimal": MinimalTheme,
    "tailwind": TailwindTheme,
}


def load_theme(
    config: Any,
    content_dir: Path,
    theme_override: Optional[str] = None,
    debug: bool = False,
) -> Any:
    """Load one built-in theme or a configured site-local theme."""

    theme_name = config.theme.lower()
    theme_path = getattr(config, "theme_path", None)
    if theme_override in BUILTIN_THEMES:
        theme_path = None

    if theme_path:
        local_theme_dir = Path(theme_path).expanduser()
        if not local_theme_dir.is_absolute():
            local_theme_dir = content_dir / local_theme_dir

        parent_theme_dir = None
        parent_name = getattr(config, "theme_parent", None)
        if parent_name:
            parent_name = str(parent_name).lower()
            if parent_name not in BUILTIN_THEMES:
                raise ZenFolioBuildError(
                    f"Unknown local theme parent '{parent_name}'"
                )
            parent_theme_dir = (
                Path(__file__).parent / "themes" / parent_name
            )

        shared_templates = (
            Path(__file__).parent / "themes" / "minimal" / "templates"
            if parent_name == "tailwind"
            else None
        )
        return LocalTheme(
            local_theme_dir,
            debug=debug,
            parent_theme_dir=parent_theme_dir,
            shared_template_dir=shared_templates,
        )

    theme_class = BUILTIN_THEMES.get(theme_name)
    if theme_class:
        return theme_class(debug=debug)
    raise ZenFolioBuildError(
        f"Unknown theme '{theme_name}'. Configure theme_path for a local theme."
    )
