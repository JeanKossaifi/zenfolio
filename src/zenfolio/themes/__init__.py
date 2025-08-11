"""
Theme system for the academic website generator
"""

from .base_theme import BaseTheme
from .minimal import MinimalTheme
from .tailwind import TailwindTheme

__all__ = ['BaseTheme', 'MinimalTheme', 'TailwindTheme'] 