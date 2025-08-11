#!/usr/bin/env python3
"""
Projects content for your academic website
"""

from zenfolio.models import ProjectsConfig, ProjectItem
# Simple strings for paths - ZenFolio handles smart resolution

projects_config = ProjectsConfig(
    items=[
        ProjectItem(
            title="Your Project Name",
            description="Description of your project. Supports **markdown** formatting.",
            category="Open Source",  # Optional category
            highlight=True,  # Set to True to show on homepage
            # Project image (local file in static/ directory)
            image="projects/project_screenshot.png",
            # Links can be URLs or local files
            github="https://github.com/yourusername/project",
            documentation="https://project-docs.com",
            paper="papers/project_paper.pdf",  # Local PDF
            demo="https://project-demo.com",
        ),
        ProjectItem(
            title="Your Research Area",
            description="Description of your research focus.",
            category="Foundational Research",
            highlight=False,
            collaborators=["Collaborator 1", "Collaborator 2"],
            # Mix of URLs and local files
            paper="research/foundational_paper.pdf",     # Local PDF
            website="https://research-project.org",      # External URL
            code="code/research_implementation.zip",     # Local code archive
            image="projects/research_diagram.png",       # Project image
        ),
        # Add more projects/research items here...
    ]
)