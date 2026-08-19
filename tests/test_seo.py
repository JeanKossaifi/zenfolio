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


def test_person_identity_emits_profile_page_with_person_schema():
    identity = AuthorConfig(
        name="Ada",
        affiliation="Institute",
        profile_url="https://institute.example.test/ada",
    )
    config = Config(author=identity)
    generator = SEOGenerator(
        config,
        "https://ada.example.test",
        identity=identity,
        site_type="person",
    )

    schema = json.loads(generator.generate_identity_schema())
    assert schema["@type"] == "ProfilePage"
    assert schema["mainEntity"]["@type"] == "Person"
    assert schema["mainEntity"]["@id"] == "https://ada.example.test/#person"
    assert (
        "https://institute.example.test/ada"
        in schema["mainEntity"]["sameAs"]
    )


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
    assert "<priority>" not in xml
    assert "<changefreq>" not in xml


def test_sitemap_only_emits_lastmod_when_supplied():
    config = Config()
    generator = SEOGenerator(config, "https://example.test")
    xml = generator.generate_sitemap_xml(
        [
            {"route": "/"},
            {"route": "/blog/post.html", "lastmod": "2026-08-18"},
        ]
    )

    assert xml.count("<lastmod>") == 1
    assert "<lastmod>2026-08-18</lastmod>" in xml


def test_project_schema_uses_configured_semantic_type():
    config = Config()
    generator = SEOGenerator(config, "https://example.test")

    schema = json.loads(
        generator.generate_project_schema(
            {
                "title": "Dataset",
                "description": "Research data.",
                "schema_type": "Dataset",
                "website": "https://example.test/dataset",
            }
        )
    )

    assert schema["@type"] == "Dataset"
    assert schema["url"] == "https://example.test/dataset"


def test_blog_schema_links_author_and_tracks_modification_date():
    identity = AuthorConfig(name="Ada")
    config = Config(author=identity)
    generator = SEOGenerator(
        config,
        "https://ada.example.test",
        identity=identity,
    )

    schema = json.loads(
        generator.generate_blog_posting_schema(
            {
                "title": "Post",
                "date": "2026-01-01",
                "updated": "2026-08-18",
                "route": "/blog/post.html",
            }
        )
    )

    assert schema["dateModified"] == "2026-08-18"
    assert schema["author"]["@id"] == "https://ada.example.test/#person"


def test_collection_schema_wraps_items_in_an_item_list():
    config = Config()
    generator = SEOGenerator(config, "https://example.test")
    item = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "ScholarlyArticle",
            "name": "Paper",
        }
    )

    schema = json.loads(
        generator.generate_collection_schema(
            "Publications",
            "/publications.html",
            [item],
        )
    )

    assert schema["@type"] == "CollectionPage"
    assert schema["mainEntity"]["@type"] == "ItemList"
    assert schema["mainEntity"]["itemListElement"][0]["position"] == 1


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
