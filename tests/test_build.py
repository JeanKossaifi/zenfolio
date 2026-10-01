import json
from pathlib import Path
import shutil

from bs4 import BeautifulSoup
import pytest

from zenfolio.validators import validate_generated_site
from zenfolio.zenfolio import ZenFolio, ZenFolioBuildError, build_site


def test_group_build_uses_clean_routes_and_group_metadata(built_group_site):
    expected = [
        "index.html",
        "research/index.html",
        "publications/index.html",
        "team/index.html",
        "updates/index.html",
        "updates/group-launch/index.html",
    ]
    for relative_path in expected:
        assert (built_group_site / relative_path).is_file()

    soup = BeautifulSoup(
        (built_group_site / "index.html").read_text(encoding="utf-8"),
        "html.parser",
    )
    navigation = [link.get_text(strip=True) for link in soup.select("nav li a")]
    assert navigation == ["Research", "Publications", "Team", "Updates"]
    assert soup.find("link", rel="canonical")["href"] == (
        "https://example.test/research/lab/"
    )
    schema = json.loads(
        soup.find("script", {"type": "application/ld+json"}).string
    )
    assert schema["@type"] == "Organization"
    assert "PhD, Imperial College London" not in soup.get_text()
    assert soup.find("a", string=lambda text: text and "Explore research" in text)[
        "href"
    ] == "research/"


def test_team_categories_remain_separate(built_group_site):
    soup = BeautifulSoup(
        (built_group_site / "team" / "index.html").read_text(encoding="utf-8"),
        "html.parser",
    )
    headings = [heading.get_text(strip=True) for heading in soup.select("h2")]
    assert headings == ["Group lead", "Core team"]


def test_sitemap_uses_clean_public_routes(built_group_site):
    sitemap = (built_group_site / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://example.test/research/lab/research/" in sitemap
    assert "research/index.html" not in sitemap


def test_production_metadata_validation_passes_for_group_fixture(
    group_site_root, built_group_site
):
    assert validate_generated_site(
        group_site_root,
        output_override=built_group_site,
        production=True,
    )


def test_output_override_is_honored(personal_site_root):
    output = personal_site_root / "custom-output"
    assert build_site(
        personal_site_root,
        dev=True,
        output_dir=output,
    )
    assert (output / "index.html").is_file()


@pytest.mark.parametrize("theme_name", ["minimal", "tailwind"])
def test_analytics_are_in_every_page_head(tmp_path, theme_name):
    fixture = Path(__file__).parent / "fixtures" / "group"
    content = tmp_path / theme_name
    shutil.copytree(fixture, content)
    builder = ZenFolio(content, theme_override=theme_name)
    script_url = "https://analytics.example.test/site.js"
    measurement_id = "G-TEST123456"
    builder.config.site.analytics_scripts = [script_url]
    builder.config.site.google_analytics_id = measurement_id

    assert builder.build(base_url="https://example.test/research/lab/")

    html_files = list(builder.output_dir.rglob("*.html"))
    assert html_files
    for html_file in html_files:
        soup = BeautifulSoup(
            html_file.read_text(encoding="utf-8"),
            "html.parser",
        )
        scripts = soup.find_all("script", src=script_url)
        assert len(scripts) == 1, html_file
        assert scripts[0].find_parent("head") is not None, html_file
        google_scripts = soup.find_all(
            "script",
            src=(
                "https://www.googletagmanager.com/gtag/js"
                f"?id={measurement_id}"
            ),
        )
        assert len(google_scripts) == 1, html_file
        assert google_scripts[0].has_attr("async"), html_file
        assert google_scripts[0].find_parent("head") is not None, html_file
        inline_configs = [
            script
            for script in soup.find_all("script")
            if script.string
            and "gtag('config'" in script.string
            and measurement_id in script.string
        ]
        assert len(inline_configs) == 1, html_file
        assert inline_configs[0].find_parent("head") is not None, html_file


def test_html_page_supports_full_layout_hidden_chrome_and_page_assets(
    tmp_path,
):
    fixture = Path(__file__).parent / "fixtures" / "group"
    content = tmp_path / "content"
    shutil.copytree(fixture, content)
    (content / "static" / "project").mkdir()
    (content / "static" / "project" / "styles.css").write_text(
        ".project { color: black; }\n", encoding="utf-8"
    )
    (content / "static" / "project" / "site.js").write_text(
        "document.documentElement.dataset.project = 'ready';\n",
        encoding="utf-8",
    )
    (content / "pages" / "project.html").write_text(
        "---\n"
        "title: Project\n"
        "slug: project\n"
        "route: /project/\n"
        "description: Project update summary.\n"
        "show_in_updates: true\n"
        "date: 2026-09-30\n"
        "image: project/teaser.png\n"
        "image_alt: Project teaser\n"
        "layout: full\n"
        "show_site_header: false\n"
        "show_site_footer: false\n"
        "stylesheets:\n"
        "  - project/styles.css\n"
        "scripts:\n"
        "  - project/site.js\n"
        "og_type: website\n"
        "theme_color: '#090b0c'\n"
        "---\n"
        '<section class="project"><h1>Custom project</h1></section>\n',
        encoding="utf-8",
    )

    builder = ZenFolio(content)
    assert builder.build(base_url="https://example.test/research/lab/")

    project_html = (
        builder.output_dir / "project" / "index.html"
    ).read_text(encoding="utf-8")
    project = BeautifulSoup(project_html, "html.parser")
    homepage = (builder.output_dir / "index.html").read_text(encoding="utf-8")

    assert project.select_one("nav") is None
    assert project.select_one("footer") is None
    assert project.select_one("article.page-layout-full.page-project")
    assert project.select_one(
        'link[rel="stylesheet"][href^="../static/project/styles.css?v="]'
    )
    assert project.select_one(
        'script[src^="../static/project/site.js?v="][defer]'
    )
    assert project.find("meta", {"property": "og:type"})["content"] == "website"
    assert project.find("meta", {"name": "theme-color"})["content"] == "#090b0c"
    assert "project/styles.css" not in homepage
    assert "project/site.js" not in homepage
    updates = BeautifulSoup(
        (builder.output_dir / "updates" / "index.html").read_text(
            encoding="utf-8"
        ),
        "html.parser",
    )
    project_update = updates.find("a", href="../project/")
    assert project_update
    assert "Project" in project_update.get_text(strip=True)
    assert "Project update summary." in updates.get_text(" ", strip=True)
    assert not (builder.output_dir / "updates" / "project").exists()
    page_update = next(
        post
        for post in builder.content.blog_posts
        if post.get("page_update")
    )
    assert page_update["image"] == "project/teaser.png"
    assert page_update["image_alt"] == "Project teaser"
    sitemap = (builder.output_dir / "sitemap.xml").read_text(encoding="utf-8")
    assert sitemap.count("https://example.test/research/lab/project/") == 1


def test_html_page_can_keep_header_and_hide_footer(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "group"
    content = tmp_path / "content"
    shutil.copytree(fixture, content)
    (content / "pages" / "project.html").write_text(
        "---\n"
        "title: Project\n"
        "route: /project/\n"
        "navigation_key: research\n"
        "show_site_footer: false\n"
        "---\n"
        "<p>Project</p>\n",
        encoding="utf-8",
    )

    builder = ZenFolio(content)
    assert builder.build(base_url="https://example.test/research/lab/")

    project = BeautifulSoup(
        (builder.output_dir / "project" / "index.html").read_text(
            encoding="utf-8"
        ),
        "html.parser",
    )
    assert project.select_one("nav")
    research_link = project.find("a", string="Research")
    assert research_link["href"] == "../research/"
    assert "text-teal-600" in research_link.get("class", [])
    assert project.select_one("footer") is None


def test_duplicate_public_routes_fail_the_build(tmp_path):
    fixture = Path(__file__).parent / "fixtures" / "group"
    content = tmp_path / "content"
    shutil.copytree(fixture, content)
    duplicate = content / "pages" / "duplicate.md"
    duplicate.write_text(
        "---\ntitle: Duplicate\nslug: duplicate\nroute: /publications/\n---\n"
        "Duplicate route.",
        encoding="utf-8",
    )

    builder = ZenFolio(content)
    with pytest.raises(ZenFolioBuildError, match="same public route"):
        builder.build(base_url="https://example.test/lab/")


def test_research_markdown_uses_collection_route_without_explicit_navigation(
    tmp_path,
):
    fixture = Path(__file__).parent / "fixtures" / "group"
    content = tmp_path / "content"
    shutil.copytree(fixture, content)
    research_page = content / "pages" / "research.md"
    research_page.write_text(
        research_page.read_text(encoding="utf-8").replace(
            "route: /research/\n", ""
        ),
        encoding="utf-8",
    )
    builder = ZenFolio(content)
    builder.config.navigation = None

    assert builder.build(base_url="https://example.test/lab/")
    assert (builder.output_dir / "research" / "index.html").is_file()
    assert not (builder.output_dir / "pages" / "research.html").exists()
