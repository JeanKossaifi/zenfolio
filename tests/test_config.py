from zenfolio.models import AuthorConfig
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
