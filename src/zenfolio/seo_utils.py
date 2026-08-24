"""SEO metadata, structured data, and sitemap generation."""

import json
import re
from html import escape, unescape
from typing import Any, Dict, List, Optional

from .models.site_config import AuthorConfig, GroupConfig
from .utils import build_url, is_external_url



def dump_schema(schema) -> str:
    """Serialize JSON-LD, escaping "</" so no value can close the <script> tag."""
    return json.dumps(schema, indent=2).replace("</", "<\\/")


class SEOGenerator:
    """Generate entity-aware metadata for personal and group sites."""

    def __init__(
        self,
        config: Any,
        base_url: str = "",
        identity: Any = None,
        site_type: Optional[str] = None,
    ):
        self.config = config
        self.base_url = (base_url or "").rstrip("/")
        self.identity = identity or getattr(config, "identity", None) or config.author
        self.site_type = site_type or getattr(config, "site_type", "person")

    @property
    def structured_data_enabled(self) -> bool:
        return not self.config.site.seo.disable_structured_data

    @property
    def has_absolute_base_url(self) -> bool:
        return self.base_url.startswith(("http://", "https://"))

    def _build_url(self, path: str) -> str:
        if is_external_url(path):
            return path
        return build_url(self.base_url, path)

    def _image_url(self, image: str) -> str:
        if is_external_url(image):
            return image
        clean_image = str(image).lstrip("/")
        if clean_image.startswith("static/"):
            clean_image = clean_image[len("static/"):]
        return self._build_url(f"static/{clean_image}")

    def _identity_type(self) -> str:
        if self.site_type == "group" or isinstance(self.identity, GroupConfig):
            return "Organization"
        return "Person"

    def _identity_reference(self) -> Dict[str, Any]:
        reference = {
            "@type": self._identity_type(),
            "name": self.identity.name,
        }
        if self.has_absolute_base_url:
            reference["url"] = self.base_url + "/"
            reference["@id"] = (
                self.base_url
                + (
                    "/#organization"
                    if self._identity_type() == "Organization"
                    else "/#person"
                )
            )
        return reference

    def generate_identity_schema(self, people: Optional[List[Any]] = None) -> str:
        """Generate homepage JSON-LD for the configured identity."""

        if not self.structured_data_enabled:
            return ""

        identity = self.identity
        entity: Dict[str, Any] = self._identity_reference()
        entity["description"] = self.config.site.description

        if isinstance(identity, AuthorConfig) and self.site_type != "group":
            if identity.title:
                entity["jobTitle"] = identity.title
            if identity.email:
                entity["email"] = identity.email
            image = getattr(identity, "image", None) or identity.photo_path
            if image:
                entity["image"] = self._image_url(image)
            if identity.affiliation:
                organization = {
                    "@type": "Organization",
                    "name": identity.affiliation,
                }
                entity["affiliation"] = organization
                entity["worksFor"] = organization
            orcid = getattr(identity, "orcid", None)
            if orcid and not str(orcid).startswith(("http://", "https://")):
                orcid = f"https://orcid.org/{str(orcid).strip()}"
            same_as = [
                value
                for value in (
                    getattr(identity, "profile_url", None),
                    orcid,
                    identity.github,
                    identity.scholar,
                    identity.linkedin,
                    identity.twitter,
                )
                if value
            ]
            if same_as:
                entity["sameAs"] = same_as
            knowledge = (
                self.config.site.seo.custom_knowledge_areas
                or identity.interests
            )
            if knowledge:
                entity["knowsAbout"] = knowledge
            if self.config.site.seo.alumni_of:
                entity["alumniOf"] = {
                    "@type": "EducationalOrganization",
                    "name": self.config.site.seo.alumni_of,
                }
            profile: Dict[str, Any] = {
                "@context": "https://schema.org",
                "@type": "ProfilePage",
                "name": self.config.site.title,
                "mainEntity": entity,
            }
            if self.has_absolute_base_url:
                profile["@id"] = self.base_url + "/#profile"
                profile["url"] = self.base_url + "/"
            return dump_schema(profile)
        else:
            logo = getattr(identity, "logo", None) or getattr(identity, "image", None)
            if logo:
                entity["logo"] = self._image_url(logo)
            parent_name = getattr(identity, "parent_name", "")
            if parent_name:
                parent = {"@type": "Organization", "name": parent_name}
                parent_url = getattr(identity, "parent_url", None)
                if parent_url:
                    parent["url"] = parent_url
                entity["parentOrganization"] = parent
            research_areas = getattr(identity, "research_areas", [])
            if research_areas:
                entity["knowsAbout"] = research_areas
            members = []
            for person in people or []:
                profile = person.to_dict() if hasattr(person, "to_dict") else person
                member = {"@type": "Person", "name": profile.get("name", "")}
                if profile.get("profile"):
                    member["url"] = profile["profile"]
                if profile.get("role"):
                    member["jobTitle"] = profile["role"]
                members.append(member)
            if members:
                entity["member"] = members

        entity["@context"] = "https://schema.org"
        return dump_schema(entity)

    def generate_scholarly_article_schema(
        self, publication: Dict[str, Any]
    ) -> str:
        if not self.structured_data_enabled:
            return ""

        schema: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "ScholarlyArticle",
            "headline": publication.get("title", ""),
            "name": publication.get("title", ""),
        }
        authors = publication.get("authors") or publication.get("author_list") or []
        if authors:
            schema["author"] = [
                {"@type": "Person", "name": name} for name in authors
            ]
        if publication.get("year"):
            schema["datePublished"] = str(publication["year"])
        if publication.get("venue"):
            schema["publisher"] = {
                "@type": "Organization",
                "name": publication["venue"],
            }
        if publication.get("abstract"):
            schema["abstract"] = publication["abstract"]

        for link in publication.get("links", []):
            label = (
                link.get("label", "")
                if isinstance(link, dict)
                else getattr(link, "label", "")
            ).lower()
            if label in {"paper", "pdf", "arxiv"}:
                schema["url"] = (
                    link.get("url")
                    if isinstance(link, dict)
                    else getattr(link, "url", "")
                )
                break
        return dump_schema(schema)

    def generate_project_schema(self, project: Dict[str, Any]) -> str:
        if not self.structured_data_enabled:
            return ""

        schema_type = project.get("schema_type") or "SoftwareSourceCode"
        schema: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "name": project.get("title", ""),
            "description": self._plain_text(project.get("description", "")),
            "creator": self._identity_reference(),
        }
        repository = (
            project.get("github")
            or project.get("code")
            or project.get("repo_url")
        )
        if repository and schema_type == "SoftwareSourceCode":
            schema["codeRepository"] = repository
        primary_url = (
            project.get("website")
            or project.get("demo")
            or project.get("documentation")
            or project.get("url")
        )
        if primary_url:
            schema["url"] = primary_url
        elif repository:
            schema["url"] = repository
        if schema_type == "SoftwareSourceCode":
            if project.get("programming_language"):
                schema["programmingLanguage"] = project["programming_language"]
            if project.get("license"):
                schema["license"] = project["license"]
        elif schema_type == "Dataset":
            if project.get("paper"):
                schema["citation"] = project["paper"]
        if project.get("image"):
            schema["image"] = self._image_url(project["image"])
        return dump_schema(schema)

    def generate_software_application_schema(
        self, project: Dict[str, Any]
    ) -> str:
        """Backward-compatible wrapper for project structured data."""
        return self.generate_project_schema(project)

    def generate_blog_posting_schema(self, blog_post: Dict[str, Any]) -> str:
        if not self.structured_data_enabled:
            return ""

        seo_config = self.config.site.seo
        schema: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": blog_post.get("title", ""),
            "author": self._identity_reference(),
        }
        if blog_post.get("date"):
            date_value = blog_post["date"]
            schema["datePublished"] = (
                date_value.strftime("%Y-%m-%d")
                if hasattr(date_value, "strftime")
                else str(date_value)
            )
        modified = blog_post.get("updated")
        if modified:
            schema["dateModified"] = (
                modified.strftime("%Y-%m-%d")
                if hasattr(modified, "strftime")
                else str(modified)
            )
        excerpt = blog_post.get("description") or blog_post.get("excerpt")
        if excerpt:
            schema["description"] = self._plain_text(excerpt)
        if blog_post.get("route") and self.has_absolute_base_url:
            page_url = self._build_url(blog_post["route"].lstrip("/"))
            schema["url"] = page_url
            schema["mainEntityOfPage"] = {
                "@type": "WebPage",
                "@id": page_url,
            }

        publisher_name = seo_config.custom_publisher_name or self.identity.name
        publisher_logo = (
            seo_config.custom_publisher_logo
            or getattr(self.identity, "logo", None)
            or getattr(self.identity, "image", None)
            or getattr(self.identity, "photo_path", None)
        )
        schema["publisher"] = self._identity_reference()
        schema["publisher"]["name"] = publisher_name
        if publisher_logo:
            logo_url = self._image_url(publisher_logo)
            image_object = {
                "@type": "ImageObject",
                "url": logo_url,
            }
            if schema["publisher"]["@type"] == "Organization":
                schema["publisher"]["logo"] = image_object
            else:
                schema["publisher"]["image"] = image_object
        image = blog_post.get("social_image") or blog_post.get("image")
        if image:
            schema["image"] = self._image_url(image)
        elif publisher_logo:
            schema["image"] = self._image_url(publisher_logo)
        return dump_schema(schema)

    def generate_collection_schema(
        self,
        title: str,
        route: str,
        item_schemas: List[str],
    ) -> str:
        """Describe an archive as a canonical collection and ordered item list."""
        if not self.structured_data_enabled or not item_schemas:
            return ""

        items = []
        for position, raw_schema in enumerate(item_schemas, start=1):
            item = json.loads(raw_schema)
            item.pop("@context", None)
            items.append(
                {
                    "@type": "ListItem",
                    "position": position,
                    "item": item,
                }
            )

        schema: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "mainEntity": {
                "@type": "ItemList",
                "numberOfItems": len(items),
                "itemListElement": items,
            },
        }
        if self.has_absolute_base_url:
            page_url = self._build_url(route.lstrip("/"))
            schema["url"] = page_url
            schema["@id"] = page_url + "#collection"
        return dump_schema(schema)

    def generate_meta_description(
        self,
        page_type: str,
        item: Optional[Dict[str, Any]] = None,
    ) -> str:
        # A generous cap: deliberate descriptions ship whole (search engines
        # ellipsize for display); only runaway text gets cut.
        return self._truncate(
            self._meta_description(page_type, item), length=300
        )

    def _meta_description(
        self,
        page_type: str,
        item: Optional[Dict[str, Any]] = None,
    ) -> str:
        if page_type == "homepage":
            return self.config.site.description
        if item:
            explicit = item.get("description") or item.get("excerpt")
            if explicit:
                return self._plain_text(explicit)

        identity_name = self.identity.name
        interests = (
            getattr(self.identity, "interests", None)
            or getattr(self.identity, "research_areas", None)
            or []
        )
        topic_text = ", ".join(interests[:3])
        if page_type == "publications":
            return (
                f"Selected research by {identity_name}"
                + (f" on {topic_text}." if topic_text else ".")
            )
        if page_type in {"blog", "updates"}:
            return (
                self.config.site.blog_description
                or f"Research updates from {identity_name}."
            )
        if page_type == "blog_post" and item:
            return f"{item.get('title', 'Research update')}: {identity_name}."
        if page_type == "team":
            return f"Meet the {identity_name} research team."
        if page_type == "research":
            return (
                f"Research directions from {identity_name}"
                + (f": {topic_text}." if topic_text else ".")
            )
        if page_type == "projects":
            return f"Featured research and open-source work from {identity_name}."
        return self.config.site.description

    def generate_sitemap_xml(self, pages: List[Dict[str, str]]) -> str:
        """Generate a valid absolute sitemap, or an empty URL set in dev."""

        entries = []
        if self.has_absolute_base_url:
            for page in pages:
                route = page["route"]
                url = self._build_url(route.lstrip("/"))
                lastmod = page.get("lastmod", "")
                entry = "  <url>\n" f"    <loc>{escape(url)}</loc>"
                if lastmod:
                    entry += f"\n    <lastmod>{escape(lastmod)}</lastmod>"
                entry += "\n  </url>"
                entries.append(entry)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries)
            + "\n</urlset>"
        )

    @staticmethod
    def _plain_text(value: str) -> str:
        # Strip tags, then unescape entities: the result is plain text that
        # templates (autoescaped) and JSON-LD (json.dumps) escape exactly once.
        text = re.sub(r"<[^>]+>", "", str(value))
        return re.sub(r"\s+", " ", unescape(text)).strip()

    @staticmethod
    def _truncate(value: str, length: int = 155) -> str:
        return value if len(value) <= length else value[: length - 1].rstrip() + "…"
