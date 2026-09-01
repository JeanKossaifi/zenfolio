"""Regression tests for silent-failure and escaping fixes.

Each test pins a bug found in the 2026-08 code review: content that was
silently dropped, parsers that wiped whole collections, unescaped HTML,
and scaffolding that crashed on first use.
"""
import shutil
from pathlib import Path

import pytest

from zenfolio.parsers.bibtex_parser import BibtexParser
from zenfolio.parsers.markdown_parser import protect_math_blocks, restore_math_blocks
from zenfolio.zenfolio import ZenFolio


FIXTURES = Path(__file__).parent / "fixtures"


def _personal_site(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(FIXTURES / "personal", content)
    return content


# ---------------------------------------------------------------------------
# One bad BibTeX entry must not wipe the whole publication list.

def test_non_numeric_year_skips_entry_not_file(tmp_path, capsys):
    bib = tmp_path / "pubs.bib"
    bib.write_text(
        "@article{good, title={Good}, author={A B}, journal={J}, year={2024}}\n"
        "@article{pending, title={Pending}, author={A B}, journal={J}, year={in press}}\n",
        encoding="utf-8",
    )
    pubs = BibtexParser().parse_file(bib)
    titles = {pub["title"] for pub in pubs}
    assert titles == {"Good", "Pending"}
    assert [pub["year"] for pub in pubs] == [2024, 0]


def test_year_with_suffix_is_extracted(tmp_path):
    bib = tmp_path / "pubs.bib"
    bib.write_text(
        "@article{sfx, title={Suffixed}, author={A B}, journal={J}, year={2023a}}\n",
        encoding="utf-8",
    )
    assert BibtexParser().parse_file(bib)[0]["year"] == 2023


def test_unreadable_bibtex_names_the_file(tmp_path):
    bib = tmp_path / "broken.bib"
    bib.write_bytes(b"@article{x, title={T}, year={2024}}\xff\xfe")  # invalid UTF-8
    with pytest.raises(ValueError, match="broken.bib"):
        BibtexParser().parse_file(bib)


def test_authors_split_on_any_case_and(tmp_path):
    bib = tmp_path / "pubs.bib"
    bib.write_text(
        "@article{x, title={T}, author={Ana Blue AND Cara Dune}, journal={J}, year={2024}}\n",
        encoding="utf-8",
    )
    assert BibtexParser().parse_file(bib)[0]["authors"] == ["Ana Blue", "Cara Dune"]


# ---------------------------------------------------------------------------
# Standalone pages: parse warnings must be visible and valid pages must build.

def test_markdown_page_with_frontmatter_builds(tmp_path):
    content = _personal_site(tmp_path)
    (content / "pages").mkdir(exist_ok=True)
    (content / "pages" / "about-me.md").write_text(
        "---\ntitle: About Me\n---\nHello page body.",
        encoding="utf-8",
    )
    site = ZenFolio(content_dir=content)
    site.build(base_url="")
    built = site.output_dir / "pages" / "about-me.html"
    assert built.exists()
    assert "Hello page body" in built.read_text(encoding="utf-8")


def test_invalid_page_warns_without_debug(tmp_path, capsys):
    content = _personal_site(tmp_path)
    (content / "pages").mkdir(exist_ok=True)
    (content / "pages" / "bad.md").write_text(
        "---\ntitle: Bad\nnot_a_field: nope\n---\nBody.",
        encoding="utf-8",
    )
    site = ZenFolio(content_dir=content)  # debug defaults to False
    site.build(base_url="")
    captured = capsys.readouterr().out
    assert "bad.md" in captured and "Warning" in captured


# ---------------------------------------------------------------------------
# Blog posts: real-world frontmatter keys must validate, failures must print.

def test_blog_post_with_updated_and_image_dimensions(tmp_path, capsys):
    content = _personal_site(tmp_path)
    blog = content / "blog"
    blog.mkdir(exist_ok=True)
    (blog / "review.md").write_text(
        "---\n"
        "title: Year in Review\n"
        "date: 2026-01-01\n"
        "updated: 2026-08-18\n"
        "image_width: 2020\n"
        "image_height: 1757\n"
        "---\nA look back.",
        encoding="utf-8",
    )
    site = ZenFolio(content_dir=content)
    if not site.config.site.blog_folder:
        pytest.skip("fixture disables the blog")
    site.build(base_url="")
    assert "validation failed" not in capsys.readouterr().out


def test_route_social_card_precedes_raw_content_image(tmp_path):
    content = _personal_site(tmp_path)
    blog = content / "blog"
    blog.mkdir(exist_ok=True)
    (blog / "review.md").write_text(
        "---\n"
        "title: Year in Review\n"
        "date: 2026-01-01\n"
        "image: images/article.jpg\n"
        "---\nA look back.",
        encoding="utf-8",
    )
    (content / "static" / "images").mkdir(exist_ok=True)
    (content / "static" / "images" / "article.jpg").write_bytes(b"article")
    generated = content / "static" / "images" / "social" / "blog"
    generated.mkdir(parents=True)
    (generated / "review.png").write_bytes(b"generated")

    site = ZenFolio(content_dir=content)
    site.build(base_url="https://ada.example.test")
    html = (site.output_dir / "blog" / "review.html").read_text(
        encoding="utf-8"
    )

    assert (
        'property="og:image" '
        'content="https://ada.example.test/static/images/social/blog/review.png"'
        in html
    )
    assert 'property="og:image:width" content="1200"' in html
    assert 'property="og:image:height" content="630"' in html


def test_explicit_social_image_precedes_generated_route_card(tmp_path):
    content = _personal_site(tmp_path)
    blog = content / "blog"
    blog.mkdir(exist_ok=True)
    (blog / "review.md").write_text(
        "---\n"
        "title: Year in Review\n"
        "date: 2026-01-01\n"
        "social_image: images/custom.png\n"
        "---\nA look back.",
        encoding="utf-8",
    )
    images = content / "static" / "images"
    images.mkdir(exist_ok=True)
    (images / "custom.png").write_bytes(b"custom")
    generated = images / "social" / "blog"
    generated.mkdir(parents=True)
    (generated / "review.png").write_bytes(b"generated")

    site = ZenFolio(content_dir=content)
    site.build(base_url="https://ada.example.test")
    html = (site.output_dir / "blog" / "review.html").read_text(
        encoding="utf-8"
    )

    assert (
        'property="og:image" '
        'content="https://ada.example.test/static/images/custom.png"'
        in html
    )


def test_duplicate_blog_slug_warns(tmp_path, capsys):
    from zenfolio.content import Content
    from zenfolio.models import Config

    content = tmp_path / "content"
    blog = content / "blog"
    blog.mkdir(parents=True)
    (content / "config.py").write_text(
        "from zenfolio.models import Config\nconfig = Config()\n",
        encoding="utf-8",
    )
    for name in ("one.md", "two.md"):
        (blog / name).write_text(
            "---\ntitle: T\nslug: same-slug\ndate: 2026-01-01\n---\nBody.",
            encoding="utf-8",
        )
    loader = Content(content, Config(), debug=False)
    posts = loader._safe_parse_blog_posts()
    assert len(posts) == 1
    assert "Duplicate blog slug 'same-slug'" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Math protection must not capture $$ inside code fences or inline code.

def test_math_protection_skips_code_fences():
    content = (
        "Real math $$a_1$$ here.\n\n"
        "```python\nprint('$$ not math $$')\n```\n\n"
        "Inline `$$ also code $$` stays.\n"
    )
    protected, blocks = protect_math_blocks(content)
    assert blocks == ["$$a_1$$"]
    assert "$$ not math $$" in protected
    assert "$$ also code $$" in protected
    assert restore_math_blocks(protected, blocks).count("$$a_1$$") == 1


# ---------------------------------------------------------------------------
# Autoescaping: special characters in data must not break generated HTML.

@pytest.mark.parametrize("theme_name", ["minimal", "tailwind"])
def test_publication_titles_are_escaped(theme_name):
    from zenfolio.theme_loader import BUILTIN_THEMES

    theme = BUILTIN_THEMES[theme_name]()
    item = {
        "id": "x",
        "title": 'Scaling "Attention" & <Memory>',
        "authors": ["A B"],
        "highlighted_authors": "A B",
        "venue": "NeurIPS & Friends",
        "year": 2024,
        "links": [],
        "bibtex": "@article{x}",
        "primary_url": "",
        "abstract": "",
        "image": "",
        "directions": [],
        "template_type": "publication_item",
    }
    html = theme.render_component("publication_item", item=item)
    assert "&amp;" in html
    assert "<Memory>" not in html


def test_json_ld_escapes_script_closers():
    from zenfolio.seo_utils import dump_schema

    payload = dump_schema({"name": "</script><script>alert(1)</script>"})
    assert "</script>" not in payload


# ---------------------------------------------------------------------------
# Scaffolding: everything init ships must import and run.

def test_template_helpers_construct_valid_models():
    from zenfolio.templates import button, news, project, service

    assert news(content="c", date="2026", url="https://x.com").website == "https://x.com"
    assert project(title="T", description="d", url="https://y.com").website == "https://y.com"
    assert service(description="Reviewer", date="2026").category == "reviewer"
    assert button(text="CV", url="cv.pdf").style == "primary"


def test_init_scaffold_builds(tmp_path, capsys):
    from zenfolio.init import init_site

    target = tmp_path / "fresh"
    init_site(target)
    for name in ("config.py", "index.md", "news.py", "projects.py",
                 "talks.py", "publications.bib"):
        assert (target / name).exists(), f"init did not create {name}"
    site = ZenFolio(content_dir=target)
    assert site.build(base_url="")


def test_scaffolded_news_file_executes(tmp_path):
    import importlib.util

    src = Path(__file__).parents[1] / "src" / "zenfolio" / "templates" / "news.py"
    spec = importlib.util.spec_from_file_location("scaffold_news", src)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.news_config.items) == 2


# ---------------------------------------------------------------------------
# Dev server safety.

def test_serve_site_reports_missing_output(tmp_path):
    from zenfolio.server import serve_site

    (tmp_path / "config.py").write_text(
        "from zenfolio.models import Config\nconfig = Config()\n",
        encoding="utf-8",
    )
    assert serve_site(tmp_path, port=0, open_browser=False) is False


def test_cli_port_validation():
    import argparse

    from zenfolio.cli import port_number

    assert port_number("8000") == 8000
    with pytest.raises(argparse.ArgumentTypeError):
        port_number("70000")


# ---------------------------------------------------------------------------
# Fixes for issues found while verifying the fixes themselves.

def test_code_span_inside_math_block_round_trips():
    content = "Sum $$ x `y` z $$ end"
    protected, blocks = protect_math_blocks(content)
    assert blocks == ["$$ x `y` z $$"]
    assert "\x00" not in protected
    assert "\x00" not in restore_math_blocks(protected, blocks)


def test_minimal_blog_excerpt_renders_html():
    from zenfolio.theme_loader import BUILTIN_THEMES

    theme = BUILTIN_THEMES["minimal"]()
    item = {
        "title": "T",
        "slug": "t",
        "date": "2026",
        "excerpt": "<p>A <em>teaser</em> &amp; more.</p>",
        "route": "/blog/t/",
        "reading_minutes": 1,
        "tags": [],
        "image": "",
    }
    html = theme.render_component("blog_post_item", item=item)
    assert "<em>teaser</em>" in html
    assert "&lt;em&gt;" not in html


def test_meta_description_has_no_double_entities():
    from zenfolio.models import Config
    from zenfolio.seo_utils import SEOGenerator

    generator = SEOGenerator(Config())
    text = generator._plain_text("<p>Fast ops &amp; tricks</p>")
    assert text == "Fast ops & tricks"


def test_brace_protected_corporate_authors_stay_whole():
    assert BibtexParser._split_authors(
        "{Barnes\nand Noble} and Jane Doe"
    ) == ["{Barnes\nand Noble}", "Jane Doe"]
    assert BibtexParser._split_authors("Ana Blue AND Cara Dune") == [
        "Ana Blue",
        "Cara Dune",
    ]


# ---------------------------------------------------------------------------
# Fixes from the full-state quality review (2026-08-24).

def _write_personal_config(content, extra="", theme="minimal"):
    content.mkdir(parents=True, exist_ok=True)
    (content / "config.py").write_text(
        "from zenfolio.models import (AuthorConfig, Config, NewsConfig, NewsItem,\n"
        "    SiteConfig, ServiceItem, TalksConfig, TalkItem)\n"
        "config = Config(\n"
        "    author=AuthorConfig(name='Test Person', interests=['ML'],\n"
        "        service=[ServiceItem(description='Reviewer', date='2026', venue='NeurIPS')]),\n"
        "    site=SiteConfig(title='T', description='d', base_url='', blog_folder=None),\n"
        f"    theme='{theme}',\n"
        f"    {extra}\n"
        ")\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text("My **bio** paragraph.", encoding="utf-8")
    (content / "publications.bib").write_text(
        "@article{x, title={P}, author={Test Person}, journal={J}, year={2024}}",
        encoding="utf-8",
    )
    return content


def test_minimal_theme_legacy_homepage_builds(tmp_path):
    """The default theme must render the default homepage: bio, service,
    and publications (with authors as names, not a Python list repr)."""
    site = ZenFolio(content_dir=_write_personal_config(tmp_path / "site"))
    site.build(base_url="")
    html = (site.output_dir / "index.html").read_text(encoding="utf-8")
    assert "My <strong>bio</strong> paragraph" in html
    assert "Reviewer" in html and "NeurIPS" in html
    pubs = site.output_dir / "publications.html"
    if not pubs.exists():
        pubs = site.output_dir / "publications" / "index.html"
    assert "['Test Person']" not in pubs.read_text(encoding="utf-8")


def test_merge_talks_renders_on_stock_theme(tmp_path):
    """merge_talks must not crash stock themes and must show the talks."""
    content = _write_personal_config(
        tmp_path / "site",
        extra=(
            "news=NewsConfig(merge_talks=True, items=[NewsItem(date='2026-01-02', content='News one')]),\n"
            "    talks=TalksConfig(items=[TalkItem(title='My Talk', date='2026-01-01', venue='V')]),"
        ),
        theme="tailwind",
    )
    site = ZenFolio(content_dir=content)
    site.build(base_url="")
    news = site.output_dir / "news" / "index.html"
    if not news.exists():
        news = site.output_dir / "news.html"
    html = news.read_text(encoding="utf-8")
    assert "News one" in html and "My Talk" in html


def test_merge_talks_sorts_readable_full_dates(tmp_path):
    """Month-first talk dates must not fall behind the oldest update."""
    content = _write_personal_config(
        tmp_path / "site",
        extra=(
            "news=NewsConfig(merge_talks=True, items=["
            "NewsItem(date='April 2026', content='April news')]),\n"
            "    talks=TalksConfig(items=["
            "TalkItem(title='May talk', date='May 5, 2026'), "
            "TalkItem(title='March talk', date='March 9, 2026')]),"
        ),
        theme="tailwind",
    )
    site = ZenFolio(content_dir=content)
    site.build(base_url="")
    news = site.output_dir / "news" / "index.html"
    if not news.exists():
        news = site.output_dir / "news.html"
    html = news.read_text(encoding="utf-8")
    assert html.index("May talk") < html.index("April news")
    assert html.index("April news") < html.index("March talk")


def test_content_date_key_handles_partial_dates():
    from zenfolio.utils import (
        content_date_key,
        format_content_date,
        normalize_content_date,
    )

    assert content_date_key("2024") == (1, "2024-01-01")
    assert content_date_key("2024-03") == (1, "2024-03-01")
    assert content_date_key("March 5, 2024") == (1, "2024-03-05")
    assert content_date_key("5 March 2024") == (1, "2024-03-05")
    assert normalize_content_date("March 5th, 2024") == "2024-03-05"
    assert format_content_date("2024-03-05", abbreviated=True) == "Mar 5, 2024"
    assert content_date_key("03/05/2024")[0] == 0


def test_normalize_route_collapses_double_slashes():
    from zenfolio.utils import normalize_route

    assert normalize_route("/blog//my-post/") == normalize_route("/blog/my-post/")


def test_dollar_math_leaves_prices_and_attributes_alone():
    from zenfolio.parsers.jupyter_parser import _normalise_dollar_math

    out = _normalise_dollar_math(
        '<p>GPU costs $10k, CPU costs $2k. <a href="x?a=$v1&b=$v2">see $y_2$</a></p>'
    )
    assert "$10k" in out and "$2k" in out and "a=$v1&b=$v2" in out
    assert r"\(y_2\)" in out


def test_corporate_authors_display_without_braces(tmp_path):
    bib = tmp_path / "pubs.bib"
    bib.write_text(
        "@article{x, title={T}, author={{Barnes and Noble} and Jane Doe}, journal={J}, year={2024}}\n",
        encoding="utf-8",
    )
    authors = BibtexParser().parse_file(bib)[0]["authors"]
    assert authors == ["Barnes and Noble", "Jane Doe"]


def test_output_manager_refuses_unmarked_handmade_site(tmp_path):
    """index.html + sitemap.xml alone (a Jekyll/hand-built site) must not be
    deleted; only directories with generated theme assets qualify as legacy
    ZenFolio output."""
    from zenfolio.errors import ZenFolioBuildError
    from zenfolio.output_manager import OutputManager
    from zenfolio.models import Config

    content = tmp_path / "content"
    (content / "static").mkdir(parents=True)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.html").write_text("<html>precious</html>", encoding="utf-8")
    (docs / "sitemap.xml").write_text("<urlset/>", encoding="utf-8")
    (docs / "notes.txt").write_text("do not delete", encoding="utf-8")

    manager = OutputManager(
        Config(output_path=str(docs)), content, content / "static", docs
    )
    with pytest.raises(ZenFolioBuildError, match="not\\s+marked"):
        manager.validate()
    assert (docs / "notes.txt").exists()


def test_theme_override_is_self_contained(tmp_path):
    from zenfolio.errors import ZenFolioBuildError
    from zenfolio.theme_loader import load_theme
    from zenfolio.models import Config

    config = Config(theme="minimal")
    assert type(load_theme(config, tmp_path, "tailwind")).__name__ == "TailwindTheme"
    assert config.theme == "minimal"  # no hidden mutation
    with pytest.raises(ZenFolioBuildError, match="Unknown theme"):
        load_theme(config, tmp_path, "no-such-theme")


def test_blog_description_stays_plain_text(tmp_path):
    from zenfolio.content_processor import ContentProcessor
    from zenfolio.models import Config
    from zenfolio.parsers import parser_registry
    from zenfolio.theme_loader import BUILTIN_THEMES

    processor = ContentProcessor(
        Config(), BUILTIN_THEMES["tailwind"](), parser_registry, False
    )
    items = processor.process_items(
        [{
            "title": "T", "slug": "t", "date": "2026", "route": "/blog/t/",
            "description": "A *plain* summary", "content": "Body",
            "excerpt": "", "tags": [], "image": "", "reading_minutes": 1,
            "template_name": "blog_post_item",
        }],
        "blog_post_item",
    )
    assert items[0]["description"] == "A *plain* summary"
