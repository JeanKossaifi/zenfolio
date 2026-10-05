from zenfolio.models import (
    ZenFolioConfig,
    GroupConfig,
    HomepageActionConfig,
    HomepageSectionConfig,
    NavigationLinkConfig,
    TeamConfig,
    PublicationsConfig,
    ResearchAreaConfig,
    ResearchAreasConfig,
    SiteConfig,
    PersonConfig,
)


team = TeamConfig(
    title="Team",
    description="Researchers working across learning and physical systems.",
    route="/team/",
    members=[
        PersonConfig(
            name="Riley Lead",
            role="Group lead",
            profile="https://example.test/riley",
        ),
        PersonConfig(name="Casey Researcher"),
    ],
)

areas = ResearchAreasConfig(
    route="/research/",
    areas=[
        ResearchAreaConfig(
            title="Physical learning",
            description="Learning models for physical systems.",
            slug="physical-learning",
            tags=["Physics", "Operators"],
            highlight=True,
        )
    ],
)

config = ZenFolioConfig(
    site_type="group",
    identity=GroupConfig(
        name="Applied Systems Lab",
        short_name="ASL",
        parent_name="Example Research",
        parent_url="https://example.test/research",
        eyebrow="Example Research",
        tagline="Learning across the engineering loop.",
        description="A neutral group fixture for ZenFolio.",
        logo="logo.svg",
        research_areas=["Physical learning"],
    ),
    site=SiteConfig(
        title="Applied Systems Lab",
        description="A neutral research-group fixture.",
        base_url="https://example.test/research/lab/",
        blog_folder="updates",
        blog_label="Updates",
        blog_route="/updates/",
    ),
    publications=PublicationsConfig(
        bib_path="publications.bib",
        title="Publications",
        route="/publications/",
    ),
    team=team,
    research_areas=areas,
    projects=None,
    news=None,
    talks=None,
    navigation=[
        NavigationLinkConfig(key="research", label="Research", route="/research/"),
        NavigationLinkConfig(key="publications", label="Publications", route="/publications/"),
        NavigationLinkConfig(key="team", label="Team", route="/team/"),
        NavigationLinkConfig(key="updates", label="Updates", route="/updates/"),
    ],
    homepage_sections=[
        HomepageSectionConfig(
            id="hero",
            type="hero",
            actions=[
                HomepageActionConfig(
                    label="Explore research",
                    route="/research/",
                )
            ],
        ),
        HomepageSectionConfig(
            id="research",
            type="card_grid",
            source="research_areas",
            title="Research",
            columns=1,
        ),
        HomepageSectionConfig(
            id="team",
            type="card_grid",
            source="team",
            title="Team",
            columns=2,
        ),
    ],
    theme="tailwind",
)
