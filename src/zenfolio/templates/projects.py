#!/usr/bin/env python3
"""Projects for your website."""

from zenfolio.models import ProjectsConfig, ProjectConfig

# Local file paths are relative to the static/ directory.

projects_config = ProjectsConfig(
    projects=[
        ProjectConfig(
            title="Your Project Name",
            description="Description of your project. Supports **markdown** formatting.",
            category="Open Source",  # Optional category
            highlight=True,  # Set to True to show on homepage
            # Project image in the static/ directory
            image="projects/project_screenshot.png",
            # Links can be URLs or local files
            github="https://github.com/yourusername/project",
            documentation="https://project-docs.com",
            paper="papers/project_paper.pdf",  # Local PDF
            demo="https://project-demo.com",
        ),
        ProjectConfig(
            title="Your Research Area",
            description="Description of your research focus.",
            category="Foundational Research",
            highlight=False,
            collaborators=["Collaborator 1", "Collaborator 2"],
            paper="research/foundational_paper.pdf",     # Local PDF
            website="https://research-project.org",      # External URL
            code="code/research_implementation.zip",     # Local code archive
            image="projects/research_diagram.png",       # Project image
        ),
        # Add more projects here.
    ]
)
