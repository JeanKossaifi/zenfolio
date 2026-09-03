import json

from zenfolio.models import (
    AuthorConfig,
    Config,
    GroupConfig,
    OrganizationRef,
    PublicationConfig,
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
        name="Ada Lovelace",
        affiliation=OrganizationRef(
            name="Institute",
            url="https://institute.example.test",
        ),
        alumni_of=[
            OrganizationRef(
                name="University",
                url="https://university.example.test",
            )
        ],
        same_as=["https://institute.example.test/ada"],
        orcid="0000-0000-0000-0001",
        photo_path="ada.jpg",
        photo_width=800,
        photo_height=1000,
    )
    config = Config(author=identity)
    generator = SEOGenerator(
        config,
        "https://ada.example.test",
        identity=identity,
        site_type="person",
    )

    schema = json.loads(generator.generate_identity_schema())
    nodes = {
        node["@id"]: node
        for node in schema["@graph"]
        if node.get("@id")
    }
    person = nodes["https://ada.example.test/#person"]
    profile = nodes["https://ada.example.test/#profile"]
    website = nodes["https://ada.example.test/#website"]

    assert profile["@type"] == "ProfilePage"
    assert profile["mainEntity"]["@id"] == person["@id"]
    assert website["@type"] == "WebSite"
    assert website["name"] == "Ada Lovelace"
    assert person["affiliation"]["@id"] == (
        "https://institute.example.test/#organization"
    )
    assert person["identifier"] == {
        "@type": "PropertyValue",
        "propertyID": "ORCID",
        "value": "0000-0000-0000-0001",
        "url": "https://orcid.org/0000-0000-0000-0001",
    }
    assert person["image"]["@id"] == (
        "https://ada.example.test/#primaryimage"
    )
    assert (
        "https://institute.example.test/ada"
        in person["sameAs"]
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


def test_publication_schema_links_identity_author_to_person():
    identity = AuthorConfig(
        name="Jean Kossaifi",
    )
    config = Config(
        author=identity,
        publications=PublicationConfig(
            highlight_author=["Kossaifi", "J. Kossaifi"]
        ),
    )
    generator = SEOGenerator(
        config,
        "https://jeankossaifi.com",
        identity=identity,
    )

    schema = json.loads(
        generator.generate_scholarly_article_schema(
            {
                "title": "Paper",
                "authors": ["J. Kossaifi", "Ada Lovelace"],
                "year": "2026",
            }
        )
    )

    assert schema["author"][0]["@id"] == (
        "https://jeankossaifi.com/#person"
    )
    assert schema["author"][0]["name"] == "Jean Kossaifi"
    assert schema["author"][1] == {
        "@type": "Person",
        "name": "Ada Lovelace",
    }


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
