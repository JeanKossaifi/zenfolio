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
