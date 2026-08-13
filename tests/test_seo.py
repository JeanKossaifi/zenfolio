import json

from zenfolio.models import (
    AuthorConfig,
    Config,
    GroupConfig,
    SEOConfig,
    SiteConfig,
    TeamMember,
)
from zenfolio.seo_utils import SEOGenerator


def test_group_identity_emits_organization_schema():
    identity = GroupConfig(
        name="Example Lab",
        parent_name="Example Research",
        parent_url="https://example.test",
    )
    config = Config(
        site_type="group",
        identity=identity,
        site=SiteConfig(
            title="Example Lab",
            description="Group description.",
            base_url="https://example.test/lab/",
        ),
    )
    generator = SEOGenerator(
        config,
        "https://example.test/lab/",
        identity=identity,
        site_type="group",
    )

    schema = json.loads(
        generator.generate_identity_schema(
            [TeamMember(name="Member", profile="https://example.test/member")]
        )
    )
    assert schema["@type"] == "Organization"
    assert schema["parentOrganization"]["name"] == "Example Research"
    assert schema["member"][0]["name"] == "Member"


def test_person_identity_emits_person_schema():
    identity = AuthorConfig(name="Ada", affiliation="Institute")
    config = Config(author=identity)
    generator = SEOGenerator(
        config,
        "https://ada.example.test",
        identity=identity,
        site_type="person",
    )

    assert json.loads(generator.generate_identity_schema())["@type"] == "Person"


def test_disable_structured_data_applies_to_all_item_schemas():
    identity = GroupConfig(name="Example Lab")
    config = Config(
        site_type="group",
        identity=identity,
        site=SiteConfig(seo=SEOConfig(disable_structured_data=True)),
    )
    generator = SEOGenerator(config, identity=identity, site_type="group")

    assert generator.generate_identity_schema() == ""
    assert generator.generate_scholarly_article_schema({"title": "Paper"}) == ""
    assert generator.generate_software_application_schema({"title": "Code"}) == ""
    assert generator.generate_blog_posting_schema({"title": "Post"}) == ""


def test_sitemap_uses_public_routes_and_effective_base_url():
    config = Config()
    generator = SEOGenerator(config, "https://example.test/base/")
    xml = generator.generate_sitemap_xml(
        [{"route": "/research/", "priority": "0.8", "changefreq": "monthly"}]
    )

    assert "<loc>https://example.test/base/research/</loc>" in xml


def test_external_structured_data_images_are_not_rewritten():
    identity = GroupConfig(
        name="Example Lab",
        logo="https://cdn.example.test/logo.png",
    )
    config = Config(site_type="group", identity=identity)
    generator = SEOGenerator(
        config,
        "https://example.test/lab/",
        identity=identity,
        site_type="group",
    )

    schema = json.loads(generator.generate_identity_schema())
    assert schema["logo"] == "https://cdn.example.test/logo.png"
