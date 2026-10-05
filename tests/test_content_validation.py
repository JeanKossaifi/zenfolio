"""Build and source validation must agree about malformed existing content."""

import shutil
from pathlib import Path

import pytest

from zenfolio.errors import ZenFolioBuildError
from zenfolio.validators import validate_site
from zenfolio.zenfolio import ZenFolio


@pytest.mark.parametrize("site_type", ["personal", "group"])
@pytest.mark.parametrize(("filename", "text"), [
    ("posts/broken.md", "---\ntitle: [Invalid, title]\ndate: 2026-01-01\n---\nBody"),
    ("posts/broken.md", "---\ntitle: [Invalid YAML\n---\nBody"),
    ("posts/broken.md", "---\n[not, a, mapping]\n---\nBody"),
    ("pages/broken.html", "---\n[not, a, mapping]\n---\n<p>Body</p>"),
    ("posts/broken.ipynb", "This is not notebook JSON"),
    ("pages/broken.md", "---\ntitle: Bad\nunknown_field: true\n---\nBody"),
    ("index.md", "---\nunknown_field: true\n---\nBody"),
    ("publications.bib", "@article{broken, title={Unclosed}"),
    ("publications.bib", "@article{broken, author={Ada Lovelace}, year={2026}}"),
])
def test_malformed_content_fails_build_and_validation(tmp_path, capsys, site_type, filename, text):
    content_dir = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures" / site_type, content_dir)
    filename = filename.replace("posts/", "updates/" if site_type == "group" else "blog/")
    source = content_dir / filename
    source.parent.mkdir(exist_ok=True)
    source.write_text(text, encoding="utf-8")
    site = ZenFolio(content_dir)
    with pytest.raises(ZenFolioBuildError, match="Content validation failed") as error:
        site.build()
    assert source.stem in str(error.value)
    assert not validate_site(content_dir)
    assert "Content validation failed" in capsys.readouterr().out


def test_missing_optional_content_remains_supported(tmp_path):
    content_dir = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures/personal", content_dir)
    (content_dir / "index.md").unlink()
    (content_dir / "publications.bib").unlink()
    assert ZenFolio(content_dir).build()
    assert validate_site(content_dir)


def test_reports_failures_across_collections_together(tmp_path):
    content_dir = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures/personal", content_dir)
    (content_dir / "index.md").write_text("---\nunknown_field: true\n---\nBody")
    (content_dir / "pages").mkdir()
    (content_dir / "pages/broken.md").write_text("---\nunknown_field: true\n---\nBody")
    with pytest.raises(ZenFolioBuildError) as error:
        ZenFolio(content_dir).build()
    assert "index.md" in str(error.value)
    assert "broken.md" in str(error.value)
