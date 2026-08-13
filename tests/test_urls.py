from pathlib import Path

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
