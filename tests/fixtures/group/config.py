from zenfolio.models import (
    Config,
    GroupConfig,
    HomepageAction,
    HomepageSection,
    NavItem,
    PeopleConfig,
    PublicationConfig,
    ResearchAreaItem,
    ResearchAreasConfig,
    SiteConfig,
    TeamCategory,
    TeamMember,
)


people = PeopleConfig(
    title="Team",
    description="Researchers working across learning and physical systems.",
    route="/team/",
    categories=[
        TeamCategory(key="lead", title="Group lead"),
        TeamCategory(key="core", title="Core team"),
    ],
    items=[
        TeamMember(
            name="Riley Lead",
            role="Group lead",
            category="lead",
            profile="https://example.test/riley",
        ),
        TeamMember(name="Casey Researcher", category="core"),
    ],
)

areas = ResearchAreasConfig(
    route="/research/",
    items=[
        ResearchAreaItem(
            title="Physical learning",
            description="Learning models for physical systems.",
            slug="physical-learning",
            tags=["Physics", "Operators"],
            highlight=True,
        )
    ],
)

config = Config(
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
    publications=PublicationConfig(
        bib_path="publications.bib",
        title="Publications",
        route="/publications/",
    ),
    people=people,
    research_areas=areas,
    projects=None,
    news=None,
    talks=None,
    navigation=[
        NavItem(key="research", label="Research", route="/research/"),
        NavItem(key="publications", label="Publications", route="/publications/"),
        NavItem(key="team", label="Team", route="/team/"),
        NavItem(key="updates", label="Updates", route="/updates/"),
    ],
    homepage_sections=[
        HomepageSection(
            id="hero",
            type="hero",
            actions=[
                HomepageAction(
                    label="Explore research",
                    route="/research/",
                )
            ],
        ),
        HomepageSection(
            id="research",
            type="card_grid",
            source="research_areas",
            title="Research",
            columns=1,
        ),
        HomepageSection(
            id="team",
            type="card_grid",
            source="people",
            title="Team",
            columns=2,
        ),
    ],
    theme="tailwind",
)
