"""
This module contains validation functions for the ZenFolio website generator.
"""
from pathlib import Path
import re
import struct
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from .utils import is_external_url
from .zenfolio import get_output_dir
from .models.site_config import AuthorConfig, GroupConfig


def _raster_image_size(path: Path):
    """Return PNG/JPEG dimensions without adding an imaging dependency."""
    with path.open("rb") as image_file:
        header = image_file.read(24)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            return struct.unpack(">II", header[16:24])
        if header[:2] != b"\xff\xd8":
            return None
        image_file.seek(2)
        while True:
            marker_start = image_file.read(1)
            if not marker_start:
                return None
            if marker_start != b"\xff":
                continue
            marker = image_file.read(1)
            while marker == b"\xff":
                marker = image_file.read(1)
            if marker in {
                b"\xc0", b"\xc1", b"\xc2", b"\xc3",
                b"\xc5", b"\xc6", b"\xc7",
                b"\xc9", b"\xca", b"\xcb",
                b"\xcd", b"\xce", b"\xcf",
            }:
                length = struct.unpack(">H", image_file.read(2))[0]
                data = image_file.read(length - 2)
                height, width = struct.unpack(">HH", data[1:5])
                return width, height
            length_bytes = image_file.read(2)
            if len(length_bytes) != 2:
                return None
            length = struct.unpack(">H", length_bytes)[0]
            image_file.seek(max(0, length - 2), 1)


def validate_site(content_dir: Path):
    """Validate configuration and content files"""
    content_dir = Path(content_dir).expanduser().resolve()
    print(f"🔍 Validating academic website in {content_dir}")
    
    errors = []
    warnings = []
    site_type = "person"
    
    if not content_dir.exists():
        errors.append(f"Content directory '{content_dir}' does not exist")
        print("❌ Validation failed:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    required_files = ["config.py", "publications.bib"]
    for filename in required_files:
        file_path = content_dir / filename
        if not file_path.exists():
            errors.append(f"Required file '{filename}' is missing")
    
    try:
        from zencfg import load_config_from_file
        config = load_config_from_file(content_dir, "config.py", "config")
        print("✅ Configuration loaded and validated successfully")

        site_type = str(getattr(config, "site_type", "person")).lower()
        identity = getattr(config, "identity", None) or config.author
        if site_type not in {"person", "group"}:
            errors.append("site_type must be 'person' or 'group'")
        elif site_type == "group":
            if not isinstance(identity, GroupConfig):
                errors.append("Group sites require identity=GroupConfig(...)")
            else:
                if not identity.name or identity.name == "Your Research Group":
                    errors.append("Group name is not customized")
                if not identity.parent_name:
                    warnings.append("Group parent organization is missing")
                if not getattr(config, "homepage_sections", None):
                    errors.append("Group sites require configured homepage sections")
                if identity.hero_media:
                    if not identity.hero_media_approved:
                        errors.append("Group hero media is not approved")
                    for field, value in (
                        ("alt text", identity.hero_media_alt),
                        ("caption", identity.hero_media_caption),
                        ("source", identity.hero_media_source),
                    ):
                        if not value:
                            errors.append(f"Group hero media requires {field}")
                    if not is_external_url(identity.hero_media):
                        hero_media_path = str(identity.hero_media).lstrip("/")
                        if hero_media_path.startswith("static/"):
                            hero_media_path = hero_media_path[len("static/"):]
                        hero_path = (
                            content_dir
                            / "static"
                            / hero_media_path
                        )
                        if not hero_path.is_file():
                            errors.append(
                                f"Group hero media is missing: {hero_path}"
                            )
                if identity.hero_diagram_approved:
                    if not identity.hero_diagram_caption:
                        errors.append(
                            "Approved group hero diagram requires a caption"
                        )
                    if not identity.hero_diagram_source:
                        errors.append(
                            "Approved group hero diagram requires a source"
                        )
            if not (content_dir / "pages" / "research.md").exists():
                warnings.append("Group research page (pages/research.md) is missing")
        else:
            if not isinstance(identity, AuthorConfig):
                errors.append("Personal sites require an AuthorConfig identity")
            if not (content_dir / "index.md").exists():
                errors.append("Required file 'index.md' is missing")
            if not identity.name or identity.name == "Your Name":
                warnings.append("Author name is not customized")
            if not identity.email or identity.email == "your.email@example.com":
                warnings.append("Author email is not customized")
        
        if not config.site.base_url or config.site.base_url == "https://yourdomain.com":
            warnings.append("Site URL is not customized")

        theme_path = getattr(config, "theme_path", None)
        if theme_path:
            resolved_theme = Path(theme_path)
            if not resolved_theme.is_absolute():
                resolved_theme = content_dir / resolved_theme
            if not (resolved_theme / "templates").is_dir():
                errors.append(
                    f"Theme templates directory is missing: {resolved_theme / 'templates'}"
                )
            if not (resolved_theme / "css" / "theme.css").is_file():
                errors.append(
                    f"Compiled theme CSS is missing: {resolved_theme / 'css' / 'theme.css'}"
                )

        seen_routes = set()
        for item in getattr(config, "navigation", None) or []:
            if not item.label or not item.route:
                errors.append("Navigation items require a label and route")
            if item.route in seen_routes:
                errors.append(f"Duplicate navigation route: {item.route}")
            seen_routes.add(item.route)

        if site_type == "group":
            media_items = []
            for collection_name in ("research_areas", "projects"):
                collection = getattr(config, collection_name, None)
                for item in getattr(collection, "items", []) or []:
                    media_items.append((collection_name, item))
            for collection_name, item in media_items:
                image = getattr(item, "image", None)
                if not image:
                    continue
                label = getattr(item, "title", collection_name)
                if not getattr(item, "image_alt", ""):
                    errors.append(f"{label} image requires alt text")
                if not is_external_url(image):
                    image_path = str(image).lstrip("/")
                    if image_path.startswith("static/"):
                        image_path = image_path[len("static/"):]
                    local_image = content_dir / "static" / image_path
                    if not local_image.is_file():
                        errors.append(f"{label} image is missing: {local_image}")
            for person in getattr(getattr(config, "people", None), "items", []) or []:
                if not person.photo:
                    continue
                if not person.photo_alt:
                    errors.append(f"{person.name} photo requires alt text")
                if not is_external_url(person.photo):
                    photo_path = str(person.photo).lstrip("/")
                    if photo_path.startswith("static/"):
                        photo_path = photo_path[len("static/"):]
                    local_photo = content_dir / "static" / photo_path
                    if not local_photo.is_file():
                        errors.append(
                            f"{person.name} photo is missing: {local_photo}"
                        )
            
        content_files = (
            ["news.py", "projects.py", "talks.py"]
            if site_type == "person"
            else ["projects.py"]
        )
        for filename in content_files:
            file_path = content_dir / filename
            if file_path.exists():
                print(f"✅ Found {filename}")
            else:
                warnings.append(f"Optional content file '{filename}' is missing")

        try:
            from .zenfolio import ZenFolio

            builder = ZenFolio(content_dir=content_dir)
            builder._validate_output_directory()
            if site_type == "group":
                builder.content.load()
                for post in builder.content.blog_posts:
                    image = post.get("image")
                    if not image:
                        continue
                    label = post.get("title", "Update")
                    if not post.get("image_alt", ""):
                        errors.append(f"{label} image requires alt text")
        except Exception as exc:
            errors.append(f"Build path or theme validation failed: {exc}")
    
    except ImportError:
        errors.append("Cannot import zencfg - please install with 'pip install zencfg'")
    except FileNotFoundError:
        errors.append("config.py file not found")
    except (TypeError, ValueError, AttributeError) as e:
        errors.append(f"Configuration validation failed: {e}")
        errors.append("Check your config.py file for type mismatches or missing required fields")
    except Exception as e:
        errors.append(f"Unexpected error loading configuration: {e}")
    
    static_dir = content_dir / "static"
    if not static_dir.exists():
        warnings.append("Static directory is missing")
    else:
        if site_type == "person":
            profile_img = static_dir / "profile.jpg"
            if not profile_img.exists():
                warnings.append("Profile image (static/profile.jpg) is missing")
    
    if errors:
        print("❌ Validation failed:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    if warnings:
        print("⚠️  Validation passed with warnings:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not warnings:
        print("✅ All validation checks passed!")
    
    return len(errors) == 0


def validate_generated_site(
    content_dir: Path,
    debug: bool = False,
    output_override: Path = None,
    production: bool = False,
) -> bool:
    """Validate the generated site for common deployment issues"""
    content_dir = Path(content_dir).expanduser().resolve()
    output_dir = get_output_dir(content_dir, output_override)
    site_type = "person"
    config = None
    try:
        from zencfg import load_config_from_file

        config = load_config_from_file(content_dir, "config.py", "config")
        site_type = str(getattr(config, "site_type", "person")).lower()
    except Exception:
        pass
    strict_group_validation = site_type == "group"
    
    if not output_dir.exists():
        print("❌ Output directory doesn't exist - run build first")
        return False
    
    issues_found = []
    warnings_found = []
    page_titles = {}
    canonical_urls = []

    if production and config and config.site.require_social_image:
        social_image = config.site.social_image
        if not social_image:
            issues_found.append("A production social image is required")
        elif is_external_url(social_image):
            warnings_found.append(
                "External social-image dimensions could not be verified"
            )
        else:
            image_path = str(social_image).lstrip("/")
            if image_path.startswith("static/"):
                image_path = image_path[len("static/"):]
            social_path = content_dir / "static" / image_path
            if not social_path.is_file():
                issues_found.append(
                    f"Production social image is missing: {social_path}"
                )
            else:
                dimensions = _raster_image_size(social_path)
                expected = (
                    config.site.social_image_width,
                    config.site.social_image_height,
                )
                if dimensions != expected:
                    issues_found.append(
                        "Production social image must be "
                        f"{expected[0]}×{expected[1]} pixels; got "
                        f"{dimensions or 'an unsupported format'}"
                    )
    
    html_files = list(output_dir.glob("**/*.html"))
    if html_files:
        print(f"🔍 Validating {len(html_files)} HTML files...")
        
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                
                if '{static}' in content:
                    issues_found.append(f"Unprocessed {{static}} placeholder in {html_file.relative_to(output_dir)}")
                if '{{' in content or '{%' in content:
                    issues_found.append(
                        f"Unresolved template expression in {html_file.relative_to(output_dir)}"
                    )

                title_match = re.search(r"<title>(.*?)</title>", content, re.I | re.S)
                if not title_match or not title_match.group(1).strip():
                    issues_found.append(
                        f"Missing page title in {html_file.relative_to(output_dir)}"
                    )
                else:
                    title = re.sub(r"\s+", " ", title_match.group(1)).strip()
                    if title in page_titles:
                        warnings_found.append(
                            f"Duplicate page title '{title}' in "
                            f"{html_file.relative_to(output_dir)} and {page_titles[title]}"
                        )
                    page_titles[title] = html_file.relative_to(output_dir)

                if not re.search(
                    r'<meta\b(?=[^>]*\bname=["\']description["\'])'
                    r'(?=[^>]*\bcontent=["\'][^"\']+["\'])[^>]*>',
                    content,
                    re.I,
                ):
                    issues_found.append(
                        f"Missing meta description in {html_file.relative_to(output_dir)}"
                    )

                if production:
                    production_metadata = {
                        "absolute canonical URL": (
                            r'<link\b(?=[^>]*\brel=["\']canonical["\'])'
                            r'(?=[^>]*\bhref=["\']https?://)[^>]*>'
                        ),
                        "Open Graph URL": (
                            r'<meta\b(?=[^>]*\bproperty=["\']og:url["\'])'
                            r'(?=[^>]*\bcontent=["\']https?://)[^>]*>'
                        ),
                        "Open Graph image": (
                            r'<meta\b(?=[^>]*\bproperty=["\']og:image["\'])'
                            r'(?=[^>]*\bcontent=["\']https?://)[^>]*>'
                        ),
                        "Twitter image": (
                            r'<meta\b(?=[^>]*\bname=["\']twitter:image["\'])'
                            r'(?=[^>]*\bcontent=["\']https?://)[^>]*>'
                        ),
                    }
                    for label, pattern in production_metadata.items():
                        if not re.search(pattern, content, re.I):
                            issues_found.append(
                                f"Missing {label} in "
                                f"{html_file.relative_to(output_dir)}"
                            )
                    canonical_match = re.search(
                        r'<link\b(?=[^>]*\brel=["\']canonical["\'])'
                        r'[^>]*\bhref=["\'](https?://[^"\']+)["\'][^>]*>',
                        content,
                        re.I,
                    )
                    if canonical_match:
                        canonical_urls.append(canonical_match.group(1))

                for image_tag in re.findall(r"<img\b[^>]*>", content, re.I):
                    if not re.search(r'\balt=["\'][^"\']*["\']', image_tag, re.I):
                        message = (
                            f"Image missing alt text in "
                            f"{html_file.relative_to(output_dir)}"
                        )
                        (
                            issues_found
                            if strict_group_validation
                            else warnings_found
                        ).append(message)

                for url in re.findall(
                    r'(?:href|src)=["\']([^"\']+)["\']', content, re.I
                ):
                    if (
                        not url
                        or url.startswith(("#", "mailto:", "tel:", "data:", "//"))
                        or urlsplit(url).scheme in {"http", "https"}
                    ):
                        continue
                    path = urlsplit(url).path
                    if not path:
                        continue
                    if path.startswith("/"):
                        candidate = output_dir / path.lstrip("/")
                    else:
                        candidate = html_file.parent / path
                    if path.endswith("/") or candidate.is_dir():
                        candidate = candidate / "index.html"
                    if not candidate.exists():
                        message = (
                            f"Broken local reference '{url}' in "
                            f"{html_file.relative_to(output_dir)}"
                        )
                        (
                            issues_found
                            if strict_group_validation
                            else warnings_found
                        ).append(message)
                
                malformed_urls = re.findall(r'href="(?!https?://)[^"]*//[^"]*"', content)
                if malformed_urls:
                    for url in malformed_urls[:2]:
                        warnings_found.append(f"Malformed internal URL {url} in {html_file.relative_to(output_dir)}")
                
            except Exception as e:
                if debug:
                    warnings_found.append(f"Could not read {html_file.relative_to(output_dir)}: {e}")

    if production:
        sitemap_path = output_dir / "sitemap.xml"
        if not sitemap_path.is_file():
            issues_found.append("Production sitemap.xml is missing")
        else:
            try:
                root = ET.parse(sitemap_path).getroot()
                sitemap_urls = {
                    element.text
                    for element in root.findall(
                        "{http://www.sitemaps.org/schemas/sitemap/0.9}url/"
                        "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                    )
                    if element.text
                }
                if not sitemap_urls:
                    issues_found.append(
                        "Production sitemap.xml contains no public routes"
                    )
                for canonical_url in canonical_urls:
                    if canonical_url not in sitemap_urls:
                        issues_found.append(
                            "Canonical URL is missing from sitemap.xml: "
                            f"{canonical_url}"
                        )
            except (ET.ParseError, OSError) as exc:
                issues_found.append(f"Invalid production sitemap.xml: {exc}")

    static_dir = output_dir / 'static'
    if static_dir.exists() and not any(static_dir.iterdir()):
        warnings_found.append("Static directory is empty - images/assets may not be copied")
    
    if issues_found:
        print("❌ CRITICAL ISSUES FOUND:")
        for issue in issues_found:
            print(f"   • {issue}")
        print("🚨 These issues will cause broken functionality on the deployed site!")
        return False
    
    if warnings_found:
        print("⚠️  Warnings found:")
        for warning in warnings_found[:5]:
            print(f"   • {warning}")
        if len(warnings_found) > 5:
            print(f"   ... and {len(warnings_found) - 5} more warnings")
    
    if not issues_found and not warnings_found:
        print("✅ Site validation passed - no issues found!")
    elif not issues_found:
        print("✅ Site validation passed with warnings")
    
    return True
