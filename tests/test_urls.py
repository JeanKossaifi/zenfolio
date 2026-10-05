from pathlib import Path
import shutil

import pytest

from zenfolio.utils import (
    build_url,
    join_route,
    normalize_route,
    route_depth,
    route_to_output_path,
)


@pytest.mark.parametrize(
    ("route", "expected"),
    [
        ("/", Path("index.html")),
        ("/research/", Path("research/index.html")),
        ("/publications.html", Path("publications.html")),
        ("updates/post/", Path("updates/post/index.html")),
    ],
)
def test_route_to_output_path(route, expected):
    assert route_to_output_path(route) == expected


def test_clean_route_helpers():
    assert normalize_route("research") == "/research/"
    assert join_route("/updates/", "launch") == "/updates/launch/"
    assert route_depth("/updates/launch/") == 2
    assert normalize_route("#team") == "#team"
    assert build_url("../", "/research/") == "../research/"


@pytest.mark.parametrize(
    "route",
    ["../config.py", "/research/../../config.py", r"\\..\\config.py"],
)
def test_route_traversal_is_rejected(route):
    with pytest.raises(ValueError):
        normalize_route(route)


def test_generated_route_rejects_query_or_fragment():
    with pytest.raises(ValueError):
        route_to_output_path("/research/?preview=true")


def test_absolute_base_url_preserves_subpath():
    assert (
        build_url("https://example.test/research/aie/", "/team/")
        == "https://example.test/research/aie/team/"
    )


def test_external_url_passes_through():
    assert (
        build_url("https://example.test/base/", "https://other.test/item")
        == "https://other.test/item"
    )


@pytest.mark.parametrize("base_url", ["", "https://example.test/nested/lab/"])
def test_homepage_body_resolves_assets_and_internal_links(tmp_path, base_url):
    from zenfolio.models import HomepageSectionConfig
    from zenfolio.zenfolio import ZenFolio

    content = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures/group", content)
    site = ZenFolio(content)
    site.config.homepage_sections.append(HomepageSectionConfig(
        type="rich_text", title="Links", id="links", layout="bio",
        body="![Logo]({static}/logo.svg)\n\n[Our team](/team/)",
    ))
    assert site.build(base_url=base_url)
    html = (site.output_dir / "index.html").read_text()
    assert "{static}" not in html
    assert f'src="{build_url(base_url, "static/logo.svg")}"' in html
    assert 'href="team/"' in html
    assert 'href="/team/"' not in html


@pytest.mark.parametrize("absolute", [False, True])
def test_validation_and_build_share_configured_static_directory(tmp_path, absolute):
    from zenfolio.validators import validate_site
    from zenfolio.zenfolio import ZenFolio

    content = tmp_path / "content"
    shutil.copytree(Path(__file__).parent / "fixtures/group", content)
    assets = content / "assets"
    (content / "static").rename(assets)
    configured_path = str(assets) if absolute else "assets"
    with (content / "config.py").open("a") as config:
        config.write(f"\nconfig.static_path = {configured_path!r}\n")
        config.write('''
from zenfolio.models import ProjectConfig, ProjectsConfig
config.identity.hero_media = "static/logo.svg"
config.identity.hero_media_approved = True
config.identity.hero_media_alt = "Fixture logo"
config.identity.hero_media_caption = "Fixture media"
config.identity.hero_media_source = "Fixture"
config.team.members[0].photo = "logo.svg"
config.team.members[0].photo_alt = "Fixture person"
config.research_areas.areas[0].image = "logo.svg"
config.research_areas.areas[0].image_alt = "Fixture area"
config.projects = ProjectsConfig(projects=[ProjectConfig(
    title="Fixture project", description="Example", image="logo.svg", image_alt="Fixture project"
)])
''')
    site = ZenFolio(content)
    assert site.static_dir == assets
    assert site.build()
    assert (site.output_dir / "static/logo.svg").is_file()
    assert validate_site(content)
