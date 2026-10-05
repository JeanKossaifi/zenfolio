# ZenFolio

ZenFolio builds personal and research-group websites from Python settings,
Markdown, Jupyter notebooks, and BibTeX publications. It uses
[ZenCFG](https://github.com/JeanKossaifi/zencfg) to check configuration values.

## Start a site

This version requires Python 3.11+, ZenCFG 1.0+, and Pydantic 2. From the
ZenFolio directory, install a local ZenCFG checkout first. Replace
`/path/to/zencfg` with its location:

```bash
python -m pip install -e /path/to/zencfg
python -m pip install -e .
zenfolio init --content-dir my-site
zenfolio dev --content-dir my-site
```

Edit `my-site/config.py` and `my-site/index.md`. The preview rebuilds when you
save. Refresh the browser after each successful build.

These are the main files in a site. The `init` command creates the starter
files; add folders such as `blog/` and `pages/` when you need them.

| File or folder | What to put there |
| --- | --- |
| `config.py` | Site settings and references to content |
| `index.md` | Homepage introduction or biography |
| `publications.bib` | Publications in BibTeX format |
| `news.py`, `projects.py`, `talks.py` | News, projects, and talks |
| `blog/` | Blog posts in Markdown or Jupyter notebooks |
| `pages/` | Other pages in Markdown, HTML, or Jupyter notebooks |
| `static/` | Images, PDFs, and other files to copy to the site |
| `_site/` | Generated website; edit the source files above instead |

## Configure the site

The main file is `config.py`. It must define a variable named `config`
containing a `ZenFolioConfig`. Here is a personal-site example:

```python
from zenfolio.models import (
    AuthorConfig,
    PublicationsConfig,
    SiteConfig,
    ZenFolioConfig,
)

config = ZenFolioConfig(
    identity=AuthorConfig(
        name="Riley Chen",
        title="Researcher",
        affiliation="Example University",
        email="riley@example.com",
        photo_path="profile.jpg",
        tagline="Learning methods for physical systems.",
        interests=["Scientific machine learning"],
    ),
    site=SiteConfig(
        title="Riley Chen",
        description="Research on learning methods for physical systems.",
        base_url="https://riley.example.com",
    ),
    publications=PublicationsConfig(
        bib_path="publications.bib",
        highlight_author=["Riley Chen", "R. Chen"],
    ),
    theme="tailwind",
)
```

Put the photo at `static/profile.jpg` and write the biography in `index.md`.
Set `base_url` to the published address, including any subfolder, such as
`https://example.com/research/`.

### Names

All configuration classes end in `Config`. A singular name describes one
entry; a plural or collective name holds a list of entries and its settings.

| Holds the list | List field | One entry |
| --- | --- | --- |
| `TeamConfig` | `members`, `interns`, `past_interns` | `PersonConfig` |
| `ProjectsConfig` | `projects` | `ProjectConfig` |
| `TalksConfig` | `talks` | `TalkConfig` |
| `ResearchAreasConfig` | `areas` | `ResearchAreaConfig` |
| `NewsConfig` | `news` | `NewsEntryConfig` |

Use `AuthorConfig` for the owner of a personal site, `GroupConfig` for a
research group's details, and `PersonConfig` for a person on a team.
Classes use names such as `PersonConfig`; fields and variables use names
such as `internship_years` and `team_config`.

The full field definitions are in
[site_config.py](src/zenfolio/models/site_config.py) and
[content_models.py](src/zenfolio/models/content_models.py).

## Add news, projects, and talks

Keep each collection in its own Python file. In `config.py`, import the
variable from that file and pass it to `ZenFolioConfig`. For example, import
`news_config` from `news`, then set `news=news_config`. The starter
`config.py` includes these lines, commented out.

### News: `news.py`

```python
from zenfolio.models import NewsConfig, NewsEntryConfig

news_config = NewsConfig(
    news=[
        NewsEntryConfig(
            date="2026-05-05",
            content="Our seminar slides are available.",
            slides="talks/seminar.pdf",
        ),
    ],
)
```

### Projects: `projects.py`

```python
from zenfolio.models import ProjectConfig, ProjectsConfig

projects_config = ProjectsConfig(
    projects=[
        ProjectConfig(
            title="Open Solver",
            description="A Python solver for fluid simulations.",
            image="projects/solver.png",
            image_alt="A simulated flow around a cylinder",
            github="https://github.com/example/open-solver",
            paper="papers/solver.pdf",
        ),
    ],
)
```

Pass `projects=projects_config` in the main configuration.

### Talks: `talks.py`

```python
from zenfolio.models import TalkConfig, TalksConfig

talks_config = TalksConfig(
    talks=[
        TalkConfig(
            title="Learning for physical systems",
            date="2026-05-05",
            venue="Research seminar",
            slides="talks/seminar.pdf",
            video="https://example.com/seminar",
        ),
    ],
)
```

Pass `talks=talks_config` in the main configuration. Use dates such as
`"2026"`, `"2026-05"`, or `"2026-05-05"`, according to what you know.

For publications, edit `publications.bib`. Set
`PublicationsConfig.highlight_author` to the name or list of name spellings
you want emphasized in author lists.

## Maintain a team

A group site uses `GroupConfig` for its identity and `TeamConfig` for its
people. This example includes a team page and a homepage team section:

```python
from zenfolio.models import (
    GroupConfig,
    HomepageSectionConfig,
    PersonConfig,
    SiteConfig,
    TeamConfig,
    ZenFolioConfig,
)

config = ZenFolioConfig(
    site_type="group",
    identity=GroupConfig(name="Example Research Group"),
    site=SiteConfig(
        title="Example Research Group",
        description="Research on learning methods for physical systems.",
        base_url="https://group.example.com",
    ),
    team=TeamConfig(
        route="/team/",
        members=[
            PersonConfig(name="Riley Chen", role="Group lead"),
        ],
        interns=[
            PersonConfig(name="Casey Morgan", internship_years=[2026]),
        ],
        past_interns=[
            PersonConfig(name="Alex Kim", internship_years=[2024, 2025]),
        ],
    ),
    homepage_sections=[
        HomepageSectionConfig(id="hero", type="hero"),
        HomepageSectionConfig(
            id="team",
            type="team_preview",
            source="team",
            title="Team",
            view_all_label="Meet the team",
            view_all_route="/team/",
        ),
    ],
    theme="tailwind",
)
```

Keep each person in one list:

- `members`: regular team members.
- `interns`: current interns.
- `past_interns`: former interns who are no longer on the team.

When an internship ends, move the whole `PersonConfig` to `past_interns`.
If the person returns, move it back to `interns`; if they join as a regular
member, move it to `members`. Keep their known `internship_years` in the
record through each move. Leave years empty when they are unknown.

The team page shows all three lists and the internship years. The homepage
shows current members and interns. Empty lists are hidden. Set a homepage
section's `limit` only if you want to show fewer people.

## Write pages and posts

Put blog posts in `blog/` and other pages in `pages/`. Both accept Markdown
and Jupyter notebooks; `pages/` also accepts HTML.

Start a Markdown post with settings between `---` lines, followed by the
text. For example, save this as `blog/simulation-notes.md`:

```markdown
---
title: Simulation notes
date: "2026-05-05"
description: Notes on setting up a flow simulation.
image: images/flow.png
image_alt: Flow around a cylinder
---

Here are the steps used to set up the simulation.
```

For a notebook, put the same settings in the first Markdown cell. ZenFolio
renders the notebook's saved code and outputs.

For a page with a custom layout, write an HTML fragment such as
`pages/solver.html`:

```html
---
title: Open Solver
route: /solver/
layout: wide
stylesheets:
  - solver/styles.css
---
<article class="solver">
  <h1>Open Solver</h1>
  <p>A Python solver for fluid simulations.</p>
</article>
```

The theme supplies the surrounding document, header, and footer. Leave out
`doctype`, `html`, `head`, and `body` tags.

Page settings include:

| Setting | What it does |
| --- | --- |
| `route` | Sets the page address. `/solver/` creates `solver/index.html`. |
| `layout` | Sets the content width: `prose` (default), `wide`, or `full`. |
| `show_site_header`, `show_site_footer` | Set either to `false` to hide it. |
| `stylesheets`, `scripts` | Loads extra CSS or JavaScript files from `static/`. |
| `navigation_key` | Marks the matching navigation link as the current page. |
| `show_in_updates` | Adds a page to updates; also provide a `date` and `route`. |
| `image`, `image_alt`, `image_caption` | Sets the preview image, its text description, and caption. |

## Link to files and pages

Put local images, PDFs, and downloads in `static/`. In configuration fields,
write paths relative to that folder: `papers/solver.pdf` refers to
`static/papers/solver.pdf`. Use a full URL for an external link and a path
such as `/team/` for a page on the site.

Projects, people, and research areas also accept custom labels through
`links`. For example:

```python
from zenfolio.models import LinkConfig, PersonConfig

person_config = PersonConfig(
    name="Riley Chen",
    photo="people/riley.jpg",
    links=[
        LinkConfig(label="Research", url="/research/"),
        LinkConfig(label="Profile", url="https://example.com/riley"),
    ],
)
```

ZenFolio adjusts local links for the page they appear on. Keep the same
source paths when previewing locally or publishing under a subfolder.

## Choose or edit a theme

ZenFolio includes `minimal` and `tailwind`. The starter site selects
`tailwind`; a `ZenFolioConfig` with no theme setting uses `minimal`.

To keep a custom theme beside your site, set its name and folder:

```python
from zenfolio.models import ZenFolioConfig

config = ZenFolioConfig(
    theme="research",
    theme_path="themes/research",
    theme_parent="tailwind",
)
```

The folder must contain `templates/` and a built `css/theme.css`.
`theme_parent` is optional: it supplies templates and files that your theme
does not replace.

If the theme uses npm, install its dependencies once:

```bash
npm --prefix themes/research install
```

During `zenfolio dev`, ZenFolio runs the theme's `build:css` script, or its
`build` script if `build:css` is absent. Before a regular `build` or
`deploy`, run the theme's build command yourself:

```bash
npm --prefix themes/research run build
```

The included themes already have built CSS files.

## Preview, check, and publish

Run these commands from the site folder, or add `--content-dir my-site`.

| Command | What it does |
| --- | --- |
| `zenfolio dev` | Builds, serves, and rebuilds when source files change. Refresh the browser after a rebuild. |
| `zenfolio build --dev` | Builds once for local viewing. |
| `zenfolio serve` | Serves an existing build. |
| `zenfolio build` | Builds using `site.base_url` for search and sharing information. |
| `zenfolio validate` | Checks configuration and content, plus the generated site if it exists. |
| `zenfolio deploy` | Builds, validates, and adds `.nojekyll` for GitHub Pages. |

Output goes to `_site/` by default. Set `output_path` in `ZenFolioConfig`
or pass `--output-dir` to change it. Restart `dev` after changing the output
folder. Use `--port 8765` to choose a preview port.

If a file cannot be parsed or a page cannot be rendered, the build reports
the error and keeps the last successful output. In `dev`, fix the file and
save to try again. If the first build fails and no previous output exists,
fix the error and restart `dev`.

The `deploy` command prepares files locally. To publish the site, upload
the contents of `_site/` using your hosting service or GitHub Actions
workflow. For a custom domain on GitHub Pages, include a `CNAME` file with
that domain in the uploaded output.

## Other settings

- Set `SiteConfig.social_image` and `social_image_alt` for the image shown
  when someone shares the site. Page-specific settings can override it.
- Set `SiteConfig.blog_folder` to change where posts live, or to `None` to
  disable the blog.
- Set `SiteConfig.markdown_extensions` to choose which Markdown features
  to enable. The defaults include code blocks, tables, and footnotes.
- Set `ZenFolioConfig.mathjax` with a `MathJaxConfig` to adjust math
  rendering. The default uses MathJax 3.
- Set `SiteConfig.google_analytics_id` for Google Analytics, or
  `analytics_scripts` for other tracking scripts.
- Set `SiteConfig.seo` with an `SEOConfig` to control search-engine
  instructions and machine-readable page descriptions.

See the [site settings](src/zenfolio/models/site_config.py) for all fields
and their defaults.

## Work on ZenFolio

From the library directory, install the test dependencies and run the tests:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

When editing the included Tailwind theme, rebuild its CSS before previewing:

```bash
npm --prefix src/zenfolio/themes/tailwind install
npm --prefix src/zenfolio/themes/tailwind run build
```
