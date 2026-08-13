from zenfolio.collection_builder import CollectionBuilder
from zenfolio.content_processor import ContentProcessor
from zenfolio.homepage_composer import HomepageComposer
from zenfolio.output_manager import OutputManager
from zenfolio.page_renderer import PageRenderer
from zenfolio.routing import RouteRegistry
from zenfolio.site_builder import SiteBuilder
from zenfolio.zenfolio import ZenFolio


def test_public_facade_composes_focused_build_services(group_site_root):
    builder = ZenFolio(group_site_root)

    assert isinstance(builder.route_registry, RouteRegistry)
    assert isinstance(builder.output_manager, OutputManager)
    assert isinstance(builder.content_processor, ContentProcessor)
    assert isinstance(builder.page_renderer, PageRenderer)
    assert isinstance(builder.homepage_composer, HomepageComposer)
    assert isinstance(builder.collection_builder, CollectionBuilder)
    assert isinstance(builder.site_builder, SiteBuilder)
    assert builder.homepage_composer.host is builder
    assert builder.collection_builder.host is builder
    assert builder.site_builder.host is builder


def test_homepage_publication_selection_preserves_priority_order():
    publications = [
        {"id": "recent", "highlight": False},
        {"id": "second", "highlight": True, "homepage_order": 2},
        {"id": "first", "highlight": True, "homepage_order": 1},
    ]

    selected = HomepageComposer.selected_publications(publications, 3)

    assert [item["id"] for item in selected] == [
        "first",
        "second",
        "recent",
    ]


def test_route_registry_keeps_team_and_updates_aliases(group_site_root):
    builder = ZenFolio(group_site_root)

    routes = builder.route_registry.configured_routes()

    assert routes["team"] == routes["people"] == "/team/"
    assert routes["updates"] == routes["blog"] == "/updates/"


def test_absolute_seo_base_does_not_leak_into_internal_links():
    public_url = "https://example.test/labs/aie/"

    assert RouteRegistry.page_base_url("/", public_url) == ""
    assert RouteRegistry.page_base_url("/research/", public_url) == "../"
    assert (
        RouteRegistry.page_base_url("/updates/launch/", public_url)
        == "../../"
    )
