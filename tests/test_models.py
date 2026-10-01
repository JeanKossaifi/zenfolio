from zenfolio.models import (
    AuthorConfig,
    Config,
    GroupConfig,
    HomepageSection,
    Link,
    NewsConfig,
    Page,
    PersonItem,
    ProjectItem,
    ResearchAreaItem,
    TalkItem,
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


def test_page_eyebrow_is_optional_and_serializes():
    assert Page().eyebrow == ""
    assert Page(eyebrow="Research project").to_dict()["eyebrow"] == (
        "Research project"
    )


def test_page_presentation_options_serialize():
    page = Page(
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


def test_config_keeps_legacy_author_and_explicit_identity():
    legacy = Config(author=AuthorConfig(name="Legacy"))
    group = GroupConfig(name="Group")
    configured = Config(site_type="group", identity=group)

    assert legacy.identity is None
    assert legacy.author.name == "Legacy"
    assert configured.identity is group


def test_project_feature_metadata_serializes():
    project = ProjectItem(
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
    talk = TalkItem(
        title="Keynote",
        website="https://example.test/keynote",
        archive_url="https://archive.example.test/keynote",
    )

    assert news.title == "Updates"
    assert news.merge_talks is True
    assert talk.to_dict()["website"] == "https://example.test/keynote"
    assert talk.to_dict()["archive_url"] == "https://archive.example.test/keynote"
