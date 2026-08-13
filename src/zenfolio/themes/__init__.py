"""
Theme system for the academic website generator
"""

from .base_theme import BaseTheme, ThemeRenderError
from .local_theme import LocalTheme
from .minimal import MinimalTheme
from .tailwind import TailwindTheme

__all__ = [
    "BaseTheme",
    "ThemeRenderError",
    "LocalTheme",
    "MinimalTheme",
    "TailwindTheme",
]