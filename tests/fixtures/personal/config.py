from zenfolio.models import (
    AuthorConfig,
    Config,
    NewsConfig,
    NewsItem,
    ProjectItem,
    ProjectsConfig,
    PublicationConfig,
    SiteConfig,
)


config = Config(
    author=AuthorConfig(
        name="Ada Researcher",
        title="Research Scientist",
        affiliation="Example Institute",
        email="ada@example.test",
        photo_path="profile.svg",
        interests=["Operator learning", "Scientific computing"],
    ),
    site=SiteConfig(
        title="Ada Researcher",
        description="Personal research site for Ada Researcher.",
        base_url="https://ada.example.test",
    ),
    publications=PublicationConfig(
        bib_path="publications.bib",
        highlight_author="Ada Researcher",
    ),
    projects=ProjectsConfig(
        items=[
            ProjectItem(
                title="Open Solver",
                description="A reusable scientific solver.",
                highlight=True,
                website="https://example.test/solver",
            )
        ]
    ),
    news=NewsConfig(
        items=[
            NewsItem(
                date="2026",
                content="Released the Open Solver.",
            )
        ]
    ),
    talks=None,
    theme="tailwind",
)
