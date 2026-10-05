"""Integration checks for the sibling AIE and personal-site themes.

The site repositories are optional when testing a standalone ZenFolio checkout.
"""

from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from zenfolio.content_processor import ContentProcessor
from zenfolio.models import ZenFolioConfig, GroupConfig, LinkConfig, PersonConfig, ProjectConfig
from zenfolio.parsers import parser_registry
from zenfolio.serialization import as_dict
from zenfolio.theme_loader import load_theme


def site_theme(site):
    content_dir = Path(__file__).resolve().parents[2] / site
    theme_name = "research" if site == "aie" else "personal"
    theme_dir = content_dir / "themes" / theme_name
    if not theme_dir.is_dir():
        pytest.skip(f"Optional sibling {site} repository is unavailable")
    config = ZenFolioConfig(
        theme_path=str(theme_dir),
        theme_parent="tailwind" if site == "website" else None,
    )
    theme = load_theme(config, content_dir)
    theme.set_render_context("../")
    return theme, ContentProcessor(config, theme, parser_registry)


def research_context(**values):
    return dict(
        item={"slug": "research", "title": "Research", "description": "", "content": ""},
        identity=GroupConfig(name="Example Lab"),
        research_areas=[],
        related_publications=values.get("publications", []),
        related_projects=values.get("projects", []),
        publications_route="/papers/",
    )


@pytest.mark.parametrize("site,component", [
    ("aie", "project_item"),
    ("aie", "featured_work_section"),
    ("aie", "page"),
    ("website", "project_item"),
    ("website", "project_feature_card"),
    ("website", "featured_work_section"),
])
def test_project_actions_keep_custom_links_without_duplicates_or_double_prefixes(site, component):
    theme, processor = site_theme(site)
    project = ProjectConfig(
        title="Example", description="Description",
        github="https://example.test/github",
        code="https://example.test/code",
        documentation="docs/manual.pdf", paper="papers/example.pdf",
        website="/project/", demo="/demo/",
        links=[
            LinkConfig(label="Repository", url="https://example.test/github"),
            LinkConfig(label="Data", url="/data/"),
            LinkConfig(label="Data again", url="/data/"),
        ],
    )
    record = processor.process_items([project], "project_item")[0]
    if component == "page":
        context = research_context(projects=[record])
    elif component == "featured_work_section":
        context = {"section": {
            "section_id": "work", "title": "Projects", "content": "", "items": [record],
        }}
    else:
        context = {"item": record}
    soup = BeautifulSoup(theme.render_component(component, **context), "html.parser")
    targets = [link["href"] for link in soup.select("a[href]")]
    assert sorted(targets) == sorted([
        "https://example.test/github", "https://example.test/code",
        "../static/docs/manual.pdf", "../static/papers/example.pdf",
        "../project/", "../demo/", "../data/",
    ])


def test_aie_publication_previews_share_links_and_respect_the_configured_route():
    theme, _ = site_theme("aie")
    publication = {
        "title": "Research & methods", "year": "2026",
        "venue": "arXiv preprint arXiv:1234.5678",
        "primary_url": "https://example.test/paper",
    }
    homepage = theme.render_component("publication_preview_section", section={
        "section_id": "publications", "title": "Publications", "items": [publication],
    })
    research = theme.render_component("page", **research_context(publications=[publication]))
    for html in (homepage, research):
        soup = BeautifulSoup(html, "html.parser")
        assert soup.select_one("h3 a")["href"] == publication["primary_url"]
        assert soup.select_one("h3").get_text() == publication["title"]
        assert soup.select_one(".publication-preview-list li p").get_text() == "arXiv preprint"
    assert BeautifulSoup(research, "html.parser").select_one(".section-action a")["href"] == "../papers/"


@pytest.mark.parametrize("person,history", [
    (PersonConfig(name="Researcher"), None),
    (PersonConfig(name="Returning researcher", internship_years=[2024, 2025]), "Internships: 2024, 2025"),
])
@pytest.mark.parametrize("membership,title", [
    ("members", "Members"),
    ("interns", "Interns"),
    ("past_interns", "Past interns"),
])
def test_aie_person_history_and_team_header_action(person, history, membership, title):
    theme, _ = site_theme("aie")
    record = as_dict(person)
    card = theme.render_component("person_item", item=record)
    preview = theme.render_component("team_preview_section", section={
        "section_id": "team", "title": "Team", "content": "",
        "grouped_items": [{"key": membership, "title": title, "people": [record]}],
        "show_research_interests": False,
        "view_all_link": {"url": "/team/", "text": "Meet the team"},
    })
    for html in (card, preview):
        assert person.name in html
        if history:
            assert history in html
    soup = BeautifulSoup(preview, "html.parser")
    assert soup.select_one(".team-heading a")["href"] == "../team/"
    assert soup.select_one(".roster-subsection .team-heading") is None
