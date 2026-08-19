from pathlib import Path
import os

import pytest

from zenfolio.themes import LocalTheme, ThemeRenderError


REQUIRED_TEMPLATES = {
    "base_layout.html.j2": "<html><body>{{ content | safe }}</body></html>",
    "navbar.html.j2": "<nav>child</nav>",
    "footer.html.j2": "<footer>child</footer>",
    "landing_page.html.j2": "<main>landing</main>",
    "section.html.j2": "<section>{{ title }}</section>",
    "page_layout.html.j2": "<main>{{ title }}</main>",
    "page.html.j2": "<article>{{ item.content | safe }}</article>",
    "mathjax.html.j2": "",
}


def _write_theme(root: Path, templates=None):
    for name, content in (templates or REQUIRED_TEMPLATES).items():
        path = root / "templates" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (root / "css").mkdir(parents=True, exist_ok=True)
    (root / "css" / "theme.css").write_text("body {}", encoding="utf-8")


def test_local_theme_uses_child_first_and_parent_fallback(tmp_path):
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write_theme(parent, {"publication_item.html.j2": "<p>parent</p>"})
    _write_theme(child)
    (child / "templates" / "navbar.html.j2").write_text(
        "<nav>child override</nav>", encoding="utf-8"
    )

    theme = LocalTheme(child, parent_theme_dir=parent)

    assert "child override" in theme.render_component("navbar")
    assert "parent" in theme.render_component("publication_item")


def test_parent_templates_can_call_render_component(tmp_path):
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    templates = dict(REQUIRED_TEMPLATES)
    templates["landing_page.html.j2"] = (
        "{{ render_component('navbar') | safe }}"
    )
    _write_theme(parent, templates)
    _write_theme(
        child,
        {"navbar.html.j2": "<nav>child navigation</nav>"},
    )

    theme = LocalTheme(child, parent_theme_dir=parent)

    assert "child navigation" in theme.render_component("landing_page")


def test_missing_or_invalid_template_fails(tmp_path):
    theme_root = tmp_path / "theme"
    _write_theme(theme_root)
    theme = LocalTheme(theme_root)

    with pytest.raises(ThemeRenderError):
        theme.render_component("missing")
    with pytest.raises(ThemeRenderError):
        theme.render_component("section")


def test_local_theme_requires_compiled_css(tmp_path):
    theme_root = tmp_path / "theme"
    _write_theme(theme_root)
    (theme_root / "css" / "theme.css").unlink()
    theme = LocalTheme(theme_root)

    with pytest.raises(FileNotFoundError):
        theme.write_css_file(tmp_path / "output")


def test_local_theme_versions_copied_assets(tmp_path):
    theme_root = tmp_path / "theme"
    _write_theme(theme_root)
    theme = LocalTheme(theme_root)

    version = theme.asset_version("theme.css")

    assert len(version) == 12
    assert version == theme.asset_version("theme.css")
    assert theme.asset_version("missing.css") == "missing"


def test_local_theme_rejects_stale_compiled_css(tmp_path):
    theme_root = tmp_path / "theme"
    _write_theme(theme_root)
    source = theme_root / "css" / "input.css"
    source.write_text("body { color: black; }", encoding="utf-8")
    compiled = theme_root / "css" / "theme.css"
    future = compiled.stat().st_mtime + 10
    os.utime(source, (future, future))
    theme = LocalTheme(theme_root)

    with pytest.raises(RuntimeError, match="stale"):
        theme.write_css_file(tmp_path / "output")


def test_homepage_fragment_link_works_from_nested_page(tmp_path):
    theme_root = tmp_path / "theme"
    _write_theme(theme_root)
    theme = LocalTheme(theme_root)
    theme.set_render_context("../")

    assert theme.url_for("/#team") == "../#team"


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("<p>No equations here.</p>", False),
        ("<p>Inline $x + y$ equation.</p>", True),
        ("<p>Display $$x^2$$ equation.</p>", True),
        ("<p>Inline \\(x + y\\) equation.</p>", True),
    ],
)
def test_mathjax_is_only_required_for_math_content(content, expected):
    assert LocalTheme.content_requires_math(content) is expected
