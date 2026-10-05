"""Rendering failures must not publish an apparently successful raw-text site."""

from pathlib import Path
import shutil

import pytest

from zenfolio.errors import ZenFolioBuildError
from zenfolio.zenfolio import ZenFolio


def test_invalid_markdown_extension_preserves_last_successful_build(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures/personal", content)
    builder = ZenFolio(content)
    assert builder.build()
    output = builder.output_dir
    previous = {
        str(path.relative_to(output)): path.read_bytes()
        for path in output.rglob("*") if path.is_file()
    }
    builder.config.site.markdown_extensions = ["zenfolio_nonexistent_extension"]

    with pytest.raises(ZenFolioBuildError, match="Failed to process .*MarkdownParser"):
        builder.build()

    current = {
        str(path.relative_to(output)): path.read_bytes()
        for path in output.rglob("*") if path.is_file()
    }
    assert current == previous
    assert not list(content.glob("._site.zenfolio-*"))


def test_fallback_markdown_failure_identifies_the_field(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures/personal", content)
    builder = ZenFolio(content)
    builder.config.site.markdown_extensions = ["zenfolio_nonexistent_extension"]
    with pytest.raises(ZenFolioBuildError, match="description with fallback Markdown"):
        builder.content_processor.process_content_field(
            "**Content**", "custom-content-type", "description"
        )
