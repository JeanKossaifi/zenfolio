from zenfolio.models import (
    AuthorConfig,
    Config,
    GroupConfig,
    HomepageSection,
    Link,
    PersonItem,
    ResearchAreaItem,
    TeamMember,
)


def test_identity_models_remain_distinct():
    author = AuthorConfig(name="Person", affiliation="Institute")
    group = GroupConfig(name="Group", parent_name="Research Org")

    assert author.name == "Person"
    assert author.affiliation == "Institute"
    assert group.name == "Group"
    assert group.parent_name == "Research Org"
    assert not hasattr(group, "scholar")


def test_group_content_models_serialize():
    member = TeamMember(
        name="Researcher",
        links=[Link(label="Profile", url="https://example.test")],
    )
    person = PersonItem(name="Alias")
    area = ResearchAreaItem(
        title="Fluids",
        slug="fluids",
        tags=["CFD"],
    )
    section = HomepageSection(id="team", source="people", limit=3)

    assert member.to_dict()["name"] == "Researcher"
    assert person.template_name == "person_item"
    assert area.template_name == "research_area_item"
    assert section.limit == 3


def test_config_keeps_legacy_author_and_explicit_identity():
    legacy = Config(author=AuthorConfig(name="Legacy"))
    group = GroupConfig(name="Group")
    configured = Config(site_type="group", identity=group)

    assert legacy.identity is None
    assert legacy.author.name == "Legacy"
    assert configured.identity is group
