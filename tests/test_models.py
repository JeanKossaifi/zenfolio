import pytest
from zencfg import ConfigBase

from zenfolio import models
from zenfolio.models import (
    AuthorConfig,
    GroupConfig,
    HomepageActionConfig,
    HomepageSectionConfig,
    LinkConfig,
    NewsConfig,
    NewsEntryConfig,
    PageConfig,
    PersonConfig,
    ProjectConfig,
    ProjectsConfig,
    ResearchAreaConfig,
    ResearchAreasConfig,
    TalkConfig,
    TalksConfig,
    TeamConfig,
    ZenFolioConfig,
)
from zenfolio.team import team_people


def test_public_model_names_are_consistent_and_have_no_aliases():
    for name in models.__all__:
        model = getattr(models, name)
        assert issubclass(model, ConfigBase)
        assert name.endswith("Config")
        assert model.__name__ == name
        assert all(key == registered.__name__.lower() for key, registered in model._registry.items())


@pytest.mark.parametrize("name", [
    "Config", "Bio", "BlogPost", "HomepageAction", "HomepageButton",
    "HomepageSection", "HomepageStep", "Link", "NavItem", "NewsItem",
    "OrganizationRef", "Page", "PeopleConfig", "Person", "PersonItem",
    "Project", "ProjectItem", "PublicationConfig", "ResearchArea",
    "ResearchAreaItem", "ServiceItem", "Talk", "TalkItem", "TeamCategory",
    "TeamMember",
])
def test_removed_model_names_are_not_exposed_or_registered(name):
    assert not hasattr(models, name)
    assert name.lower() not in ConfigBase._registry


def test_identity_models_remain_distinct():
    author = AuthorConfig(name="Person", affiliation="Institute")
    group = GroupConfig(name="Group", parent_name="Research Org")

    assert author.name == "Person"
    assert author.affiliation == "Institute"
    assert group.name == "Group"
    assert group.parent_name == "Research Org"
    assert not hasattr(group, "scholar")


@pytest.mark.parametrize("identity", [
    AuthorConfig(name="Researcher", affiliation="Institute"),
    GroupConfig(name="Group", parent_name="Research Org"),
])
def test_config_uses_one_identity_field_and_preserves_identity_type(identity):
    configured = ZenFolioConfig(identity=identity)
    restored = ZenFolioConfig(**configured.to_dict())

    assert configured.identity is identity
    assert isinstance(restored.identity, type(identity))
    assert restored.identity.name == identity.name
    assert not hasattr(configured, "author")
    assert not hasattr(configured, "people")
    assert isinstance(ZenFolioConfig().identity, AuthorConfig)


def test_author_uses_same_homepage_action_model_as_sections():
    action = HomepageActionConfig(label="Contact", route="mailto:person@example.test")
    author = AuthorConfig(homepage_actions=[action])
    section = HomepageSectionConfig(actions=[action])

    assert author.homepage_actions[0].to_dict() == section.actions[0].to_dict()
    assert not hasattr(author, "homepage_buttons")


def test_group_content_models_serialize():
    person = PersonConfig(
        name="Researcher",
        links=[LinkConfig(label="Profile", url="https://example.test")],
    )
    area = ResearchAreaConfig(title="Fluids", slug="fluids", tags=["CFD"])
    section = HomepageSectionConfig(id="team", source="team", limit=3)

    assert person.to_dict()["name"] == "Researcher"
    assert person.template_name == "person_item"
    assert area.template_name == "research_area_item"
    assert section.limit == 3


@pytest.mark.parametrize("collection,field,record", [
    (NewsConfig, "news", NewsEntryConfig(date="2026-10-04", content="Release")),
    (ProjectsConfig, "projects", ProjectConfig(title="Project", description="Description")),
    (TalksConfig, "talks", TalkConfig(title="Talk")),
    (ResearchAreasConfig, "areas", ResearchAreaConfig(title="Research")),
])
def test_collection_fields_describe_their_content(collection, field, record):
    configured = collection(**{field: [record]})
    restored = collection(**configured.to_dict())
    records = getattr(restored, field)

    assert len(records) == 1
    assert isinstance(records[0], type(record))
    assert records[0].to_dict() == record.to_dict()
    assert "items" not in configured.to_dict()
    with pytest.raises(ValueError):
        collection(items=[record])


def test_team_has_explicit_lists_with_one_person_model():
    person = PersonConfig(name="Researcher", internship_years=[2025, 2026])
    team = TeamConfig(members=[person], interns=[], past_interns=[])
    restored = TeamConfig(**team.to_dict())

    assert restored.members[0].internship_years == [2025, 2026]
    assert isinstance(restored.members[0], PersonConfig)
    assert "items" not in team.to_dict()


def test_mutable_defaults_are_independent_between_configurations():
    first = ZenFolioConfig()
    second = ZenFolioConfig()
    first.projects.projects.append(ProjectConfig(title="Project", description="Description"))
    first.identity.interests.append("Another area")

    assert second.projects.projects == []
    assert "Another area" not in second.identity.interests
    assert TeamConfig().members is not TeamConfig().members


def test_page_eyebrow_is_optional_and_serializes():
    assert PageConfig().eyebrow == ""
    assert PageConfig(eyebrow="Research project").to_dict()["eyebrow"] == (
        "Research project"
    )


def test_page_presentation_options_serialize():
    page = PageConfig(
        layout="full",
        show_site_header=False,
        show_site_footer=False,
        stylesheets=["project/styles.css"],
        scripts=["project/site.js"],
        show_in_updates=True,
        date="2026-09-30",
        image="project/teaser.png",
        image_alt="Project teaser",
        image_caption="Teaser caption",
        og_type="website",
        theme_color="#090b0c",
        navigation_key="projects",
    )

    serialized = page.to_dict()
    assert serialized["layout"] == "full"
    assert serialized["show_site_header"] is False
    assert serialized["show_site_footer"] is False
    assert serialized["stylesheets"] == ["project/styles.css"]
    assert serialized["scripts"] == ["project/site.js"]
    assert serialized["show_in_updates"] is True
    assert serialized["date"] == "2026-09-30"
    assert serialized["image"] == "project/teaser.png"
    assert serialized["image_alt"] == "Project teaser"
    assert serialized["image_caption"] == "Teaser caption"
    assert serialized["og_type"] == "website"
    assert serialized["theme_color"] == "#090b0c"
    assert serialized["navigation_key"] == "projects"


def test_project_feature_metadata_serializes():
    project = ProjectConfig(
        title="Tool",
        description="Description",
        featured_order=2,
        featured_size="full",
        image_style="media",
        result="**19.8%** lower error",
        result_note="Compared with the baseline.",
    )

    serialized = project.to_dict()
    assert serialized["featured_order"] == 2
    assert serialized["featured_size"] == "full"
    assert serialized["image_style"] == "media"
    assert serialized["result"] == "**19.8%** lower error"
    assert serialized["result_note"] == "Compared with the baseline."


def test_updates_metadata_and_talk_website_serialize():
    news = NewsConfig(title="Updates", merge_talks=True)
    talk = TalkConfig(
        title="Keynote",
        website="https://example.test/keynote",
        archive_url="https://archive.example.test/keynote",
    )

    assert news.title == "Updates"
    assert news.merge_talks is True
    assert talk.to_dict()["website"] == "https://example.test/keynote"
    assert talk.to_dict()["archive_url"] == "https://archive.example.test/keynote"


@pytest.mark.parametrize("years", [[True], [2024.0], "[true]", "[2024.0]", "[0]"])
def test_person_years_reject_coercion_in_nested_config_and_assignment(years):
    with pytest.raises((ValueError, TypeError), match="internship_years"):
        PersonConfig(name="Researcher", internship_years=years)

    with pytest.raises((ValueError, TypeError), match="internship_years"):
        ZenFolioConfig(team={"members": [{"name": "Researcher", "internship_years": years}]})

    person = PersonConfig(name="Researcher", internship_years=[2024])
    with pytest.raises((ValueError, TypeError), match="internship_years"):
        person.internship_years = years
    assert person.internship_years == [2024]


def test_person_supports_json_years_and_rechecks_mutated_history():
    config = ZenFolioConfig(team={"interns": [{"name": "Researcher", "internship_years": "[2024]"}]})
    person = config.team.interns[0]
    person.internship_years = "[2024, 2025]"
    assert person.internship_years == [2024, 2025]
    person.internship_years.append(True)
    with pytest.raises((ValueError, TypeError), match="internship_years"):
        team_people(config)


def test_person_rejects_blank_name_assignment_without_losing_previous_name():
    person = PersonConfig(name="Researcher")
    with pytest.raises(ValueError, match="name"):
        person.name = " "
    assert person.name == "Researcher"
