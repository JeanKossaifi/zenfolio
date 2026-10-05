"""Team authoring, lifecycle changes, and rendered membership semantics."""

import json
import shutil

from bs4 import BeautifulSoup
import pytest

from zenfolio.models import (
    ZenFolioConfig, PersonConfig, TeamConfig,
)
from zenfolio.team import team_people
from zenfolio.validators import validate_site
from zenfolio.zenfolio import ZenFolio


TEAM_CONFIG = '''from zenfolio.models import (
    ZenFolioConfig, GroupConfig, HomepageSectionConfig, PersonConfig, SiteConfig, TeamConfig,
)

config = ZenFolioConfig(
    site_type="group",
    identity=GroupConfig(name="Example Lab", parent_name="Example Research"),
    site=SiteConfig(
        title="Example Lab", description="A research group.", blog_folder=None,
    ),
    team=TeamConfig(
        route="/our-team/",
        description="Our researchers and internship history.",
        members=[PersonConfig(name="Riley Lead", role="Group lead")],
        interns=[PersonConfig(name="Casey Intern", internship_years=[2024])],
        past_interns=[PersonConfig(
            name="Alex Researcher", internship_years=[2022, 2023],
            affiliation="Example University",
        )],
    ),
    news=None, projects=None, talks=None,
    homepage_sections=[
        HomepageSectionConfig(id="hero", type="hero"),
        HomepageSectionConfig(id="team", source="team", title="Team"),
    ],
)
'''


@pytest.fixture
def team_site(tmp_path, group_site_root):
    root = tmp_path / "content"
    shutil.copytree(group_site_root, root)
    (root / "config.py").write_text(TEAM_CONFIG, encoding="utf-8")
    return root


def read_page(builder, route="index.html"):
    return BeautifulSoup(
        (builder.output_dir / route).read_text(encoding="utf-8"), "html.parser"
    )


def organization_members(homepage):
    for script in homepage.find_all("script", type="application/ld+json"):
        schema = json.loads(script.string)
        if schema.get("@type") == "Organization":
            return [person["name"] for person in schema.get("member", [])]
    pytest.fail("Homepage is missing its organization schema")


@pytest.mark.parametrize("theme", ["minimal", "tailwind"])
def test_named_team_lists_build_current_preview_and_full_history(team_site, theme):
    builder = ZenFolio(team_site, theme_override=theme)
    assert builder.build(base_url="https://example.test/lab/")

    home = read_page(builder)
    preview = home.select_one("#team").get_text(" ", strip=True)
    assert "Riley Lead" in preview
    assert "Casey Intern" in preview
    assert "Alex Researcher" not in preview
    assert organization_members(home) == ["Riley Lead", "Casey Intern"]
    assert builder._route_for("team") == "/our-team/"
    assert any(entry["key"] == "team" for entry in builder.navigation)

    page = read_page(builder, "our-team/index.html")
    assert [h.get_text(strip=True) for h in page.select("h2")] == [
        "Members", "Interns", "Past interns",
    ]
    text = page.get_text(" ", strip=True)
    assert "Alex Researcher" in text
    assert "Internships: 2022, 2023" in text
    assert "Example University" in text


def test_moving_a_person_preserves_history_and_updates_current_membership(team_site):
    builder = ZenFolio(team_site, theme_override="minimal")
    team = builder.config.team
    person = team.interns.pop()
    team.past_interns.append(person)
    assert builder.build()
    assert organization_members(read_page(builder)) == ["Riley Lead"]
    assert "Casey Intern" not in read_page(builder).select_one("#team").get_text()
    assert "Internships: 2024" in read_page(builder, "our-team/index.html").get_text()

    # A returning intern carries the same profile and earlier internship years.
    team.past_interns.remove(person)
    person.internship_years.append(2025)
    team.interns.append(person)
    assert builder.build()
    assert organization_members(read_page(builder)) == ["Riley Lead", "Casey Intern"]

    # Conversion to regular membership retains both internships and one card.
    team.members.append(team.interns.pop())
    assert builder.build()
    page = read_page(builder, "our-team/index.html")
    assert page.get_text().count("Casey Intern") == 1
    assert "Internships: 2024, 2025" in page.get_text()
    assert [h.get_text(strip=True) for h in page.select("h2")] == [
        "Members", "Past interns",
    ]


def test_history_does_not_determine_current_list_membership():
    # No known dates is valid; prior internships do not make a member inactive.
    config = ZenFolioConfig(team=TeamConfig(
        members=[PersonConfig(name="Former Intern", internship_years=[2020])],
        interns=[PersonConfig(name="Current Intern")],
        past_interns=[PersonConfig(name="Past Intern")],
    ))
    assert [person.name for person in team_people(config, current_only=True)] == [
        "Former Intern", "Current Intern",
    ]


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_person_names_are_rejected(name):
    with pytest.raises(ValueError, match="name"):
        PersonConfig(name=name)


@pytest.mark.parametrize("years", [[0], [-2024], [True], [2024.5]])
def test_internship_years_must_be_positive_integers(years):
    with pytest.raises((TypeError, ValueError), match="internship_years"):
        PersonConfig(name="Example", internship_years=years)


def test_named_roster_photos_are_validated(team_site, capsys):
    path = team_site / "config.py"
    path.write_text(TEAM_CONFIG + '''
config.team.past_interns[0].photo = "missing-portrait.png"
config.team.past_interns[0].photo_alt = "Portrait of Alex Researcher"
''', encoding="utf-8")
    assert not validate_site(team_site)
    assert "Alex Researcher photo is missing" in capsys.readouterr().out


def test_empty_team_does_not_create_a_page_or_navigation(team_site):
    builder = ZenFolio(team_site)
    builder.config.team = TeamConfig(route="/our-team/")
    assert builder.build()
    assert not (builder.output_dir / "our-team/index.html").exists()
    assert all(entry["key"] != "team" for entry in builder.navigation)
    assert organization_members(read_page(builder)) == []
