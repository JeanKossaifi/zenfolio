"""Consistent frontmatter validation for Markdown, HTML, and notebooks."""

import frontmatter
from frontmatter.default_handlers import YAMLHandler


class MappingYAMLHandler(YAMLHandler):
    def load(self, value, **kwargs):
        metadata = super().load(value, **kwargs)
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("YAML frontmatter must be a mapping of field names to values")
        return metadata


def parse_frontmatter(text):
    """Preserve format detection while rejecting silently discarded YAML."""
    handler = frontmatter.detect_format(text.strip(), frontmatter.handlers)
    if isinstance(handler, YAMLHandler):
        handler = MappingYAMLHandler()
    return frontmatter.loads(text, handler=handler)
