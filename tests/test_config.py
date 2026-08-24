from types import SimpleNamespace

from zenfolio.models import (
    NewsConfig,
    NewsItem,
    TalkItem,
    TalksConfig,
)
from zenfolio.routing import RouteRegistry
from zenfolio.themes import TailwindTheme
from zenfolio.zenfolio import ZenFolio


def test_legacy_author_becomes_effective_identity(personal_site_root):
    builder = ZenFolio(personal_site_root)

    assert builder.site_type == "person"
    assert builder.identity is builder.config.author
    assert builder.config.identity is builder.config.author


def test_group_config_loads_ordered_navigation(group_site_root):
    builder = ZenFolio(group_site_root)
    builder.content.load()
    builder._configure_navigation()

    assert builder.site_type == "group"
    assert [item["label"] for item in builder.navigation] == [
        "Research",
        "Publications",
        "Team",
        "Updates",
    ]
    assert [item["route"] for item in builder.navigation] == [
        "/research/",
        "/publications/",
        "/team/",
        "/updates/",
    ]


def test_builtin_theme_override_ignores_configured_local_path(tmp_path):
    (tmp_path / "config.py").write_text(
        "from zenfolio.models import Config\n"
        "config = Config(theme='private', theme_path='missing-theme')\n",
        encoding="utf-8",
    )

    builder = ZenFolio(tmp_path, theme_override="tailwind")

    assert isinstance(builder.theme, TailwindTheme)


def test_merged_updates_replaces_talks_and_news_navigation():
    config = SimpleNamespace(
        navigation=None,
        publications=SimpleNamespace(route=None),
        projects=None,
        talks=TalksConfig(items=[TalkItem(title="Keynote")]),
        news=NewsConfig(
            title="Updates",
            merge_talks=True,
            items=[NewsItem(date="2026", content="Announcement")],
        ),
        research_areas=None,
        people=None,
        site=SimpleNamespace(
            blog_folder="",
            blog_label="Blog",
            blog_route=None,
        ),
    )
    content = SimpleNamespace(blog_posts=[])

    navigation, _ = RouteRegistry(config, content).configure_navigation()

    assert [item["label"] for item in navigation] == [
        "Publications",
        "Updates",
    ]
    assert [item["key"] for item in navigation] == [
        "publications",
        "news",
    ]
