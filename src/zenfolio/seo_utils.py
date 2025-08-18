"""
SEO utilities for ZenFolio - Generate structured data and metadata
Implements Person, ScholarlyArticle, and BlogPosting schemas for enhanced search appearance
"""

import json
from typing import Dict, List, Any, Optional
from .utils import build_url


class SEOGenerator:
    """Generates SEO metadata and structured data for academic websites"""
    
    def __init__(self, config, base_url: str = ""):
        self.config = config
        self.base_url = base_url.rstrip('/')
        
    def _build_url(self, path: str) -> str:
        """Build absolute URL from relative path"""
        return build_url(self.base_url, path)
    
    def generate_person_schema(self) -> str:
        """Generate Person schema for homepage"""
        if self.config.site.seo.disable_structured_data:
            return ""
            
        author = self.config.author
        seo_config = self.config.site.seo
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": author.name,
            "url": self.base_url if self.base_url else "",
            "jobTitle": author.title,
            "description": self.config.site.description
        }
        
        # Add profile image if available
        if hasattr(author, 'photo_path') and author.photo_path:
            schema["image"] = self._build_url(f"static/{author.photo_path}")
            
        # Add affiliation if available
        if hasattr(author, 'affiliation') and author.affiliation:
            schema["affiliation"] = {
                "@type": "Organization",
                "name": author.affiliation
            }
            
        # Add social media profiles
        same_as = []
        for social in ['github', 'scholar', 'linkedin', 'twitter']:
            if hasattr(author, social) and getattr(author, social):
                same_as.append(getattr(author, social))
        
        if same_as:
            schema["sameAs"] = same_as
            
        # Add email if available
        if hasattr(author, 'email') and author.email:
            schema["email"] = author.email
        
        # Add knowledge areas - use custom override or auto-detect from interests
        knowledge_areas = seo_config.custom_knowledge_areas or (author.interests if hasattr(author, 'interests') else None)
        if knowledge_areas:
            schema["knowsAbout"] = knowledge_areas
            
        # Add work organization
        if hasattr(author, 'affiliation') and author.affiliation:
            schema["worksFor"] = {
                "@type": "Organization",
                "name": author.affiliation
            }
            
        # Add alumni information from config
        if seo_config.alumni_of:
            schema["alumniOf"] = {
                "@type": "EducationalOrganization",
                "name": seo_config.alumni_of
            }
            
        return json.dumps(schema, indent=2)
    
    def generate_scholarly_article_schema(self, publication: Dict[str, Any]) -> str:
        """Generate ScholarlyArticle schema for publication"""
        schema = {
            "@context": "https://schema.org",
            "@type": "ScholarlyArticle",
            "headline": publication.get('title', ''),
            "name": publication.get('title', ''),
        }
        
        # Add authors
        if publication.get('author_list'):
            authors = []
            for author_name in publication['author_list']:
                authors.append({
                    "@type": "Person",
                    "name": author_name
                })
            schema["author"] = authors
        
        # Add publication date
        if publication.get('year'):
            year_value = publication['year']
            if hasattr(year_value, 'strftime'):
                # Convert date/datetime object to year string
                schema["datePublished"] = year_value.strftime('%Y')
            else:
                # Already a string or number
                schema["datePublished"] = str(year_value)
        
        # Add publisher/venue
        if publication.get('venue'):
            schema["publisher"] = {
                "@type": "Organization",
                "name": publication['venue']
            }
            
        # Add abstract if available
        if publication.get('abstract'):
            schema["abstract"] = publication['abstract']
            
        # Add PDF link if available
        pdf_links = [link for link in publication.get('links', []) if 'PDF' in link.get('label', '')]
        if pdf_links:
            schema["url"] = pdf_links[0]['url']
            
        return json.dumps(schema, indent=2)
    
    def generate_software_application_schema(self, project: Dict[str, Any]) -> str:
        """Generate SoftwareApplication schema for a project"""
        schema = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": project.get('title', ''),
            "description": project.get('description', ''),
            "applicationCategory": "DeveloperApplication",
        }
        
        # Add code repository URL
        if project.get('repo_url'):
            schema["codeRepository"] = project['repo_url']
        
        # Add homepage URL if available
        if project.get('url'):
            schema["url"] = project['url']
            
        # Add author
        schema["author"] = {
            "@type": "Person",
            "name": self.config.author.name
        }
            
        return json.dumps(schema, indent=2)
    
    def generate_blog_posting_schema(self, blog_post: Dict[str, Any]) -> str:
        """Generate BlogPosting schema for blog posts"""
        if self.config.site.seo.disable_structured_data:
            return ""
            
        seo_config = self.config.site.seo
        
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": blog_post.get('title', ''),
            "author": {
                "@type": "Person",
                "name": self.config.author.name
            }
        }
        
        # Add publication date
        if blog_post.get('date'):
            date_value = blog_post['date']
            if hasattr(date_value, 'strftime'):
                # Convert date/datetime object to ISO format string
                schema["datePublished"] = date_value.strftime('%Y-%m-%d')
            else:
                # Already a string
                schema["datePublished"] = str(date_value)
            
        # Add description/excerpt
        if blog_post.get('excerpt'):
            schema["description"] = blog_post['excerpt']
            
        # Add URL and mainEntityOfPage
        if blog_post.get('slug'):
            blog_url = self._build_url(f"blog/{blog_post['slug']}.html")
            schema["url"] = blog_url
            schema["mainEntityOfPage"] = {
                "@type": "WebPage",
                "@id": blog_url
            }
            
        # Add publisher - use custom overrides or auto-detect from author
        publisher_name = seo_config.custom_publisher_name or self.config.author.name
        publisher_logo_path = seo_config.custom_publisher_logo or (self.config.author.photo_path if hasattr(self.config.author, 'photo_path') else None)
        publisher_logo_url = self._build_url(f"static/{publisher_logo_path}") if publisher_logo_path else None
        
        schema["publisher"] = {
            "@type": "Organization",
            "name": publisher_name
        }
        if publisher_logo_url:
            schema["publisher"]["logo"] = {
                "@type": "ImageObject",
                "url": publisher_logo_url
            }
            
        # Add image - prioritize blog post image, fallback to publisher logo
        if blog_post.get('image'):
            schema["image"] = self._build_url(f"static/{blog_post['image']}")
        elif publisher_logo_url:
            schema["image"] = publisher_logo_url
            
        return json.dumps(schema, indent=2)
    
    def generate_website_schema(self) -> str:
        """Generate Website schema for the entire site"""
        schema = {
            "@context": "https://schema.org",
            "@type": "Website",
            "name": self.config.site.title,
            "description": self.config.site.description,
            "url": self.base_url,
            "author": {
                "@type": "Person",
                "name": self.config.author.name
            }
        }
        
        return json.dumps(schema, indent=2)
    
    def generate_meta_description(self, page_type: str, item: Optional[Dict[str, Any]] = None) -> str:
        """Generate optimized meta descriptions for different page types"""
        author_name = self.config.author.name
        
        if page_type == "homepage":
            return self.config.site.description
            
        elif page_type == "publications":
            return f"Research publications by {author_name}, covering {', '.join(self.config.author.interests[:3])} and more."
            
        elif page_type == "blog":
            return f"Insights and thoughts on {', '.join(self.config.author.interests[:3])} by {author_name}."
            
        elif page_type == "blog_post" and item:
            if item.get('excerpt'):
                # Clean HTML tags from excerpt for meta description
                import re
                clean_excerpt = re.sub('<[^<]+?>', '', item['excerpt'])
                return clean_excerpt[:155] + ('...' if len(clean_excerpt) > 155 else '')
            return f"A blog post by {author_name} about {item.get('title', 'research and development')}."
            
        elif page_type == "publication" and item:
            return f"A {item.get('year', 'recent')} publication by {author_name} et al. in {item.get('venue', 'a leading journal')}, titled '{item.get('title', '')}'."
            
        elif page_type == "projects":
            return f"Research projects and open-source contributions by {author_name} in {', '.join(self.config.author.interests[:3])}."
            
        elif page_type == "talks":
            return f"Conference talks and presentations by {author_name} on {', '.join(self.config.author.interests[:3])}."
            
        elif page_type == "news":
            return f"Latest news and updates from {author_name}'s research and academic activities."
            
        # Fallback
        return self.config.site.description
    
    def generate_sitemap_xml(self, pages: List[Dict[str, str]]) -> str:
        """Generate sitemap.xml content"""
        sitemap_entries = []
        
        for page in pages:
            url = self._build_url(page['path'])
            priority = page.get('priority', '0.5')
            changefreq = page.get('changefreq', 'monthly')
            lastmod = page.get('lastmod', '')
            
            entry = f"""  <url>
    <loc>{url}</loc>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>"""
            
            if lastmod:
                entry += f"""
    <lastmod>{lastmod}</lastmod>"""
                
            entry += """
  </url>"""
            
            sitemap_entries.append(entry)
        
        sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemap_entries)}
</urlset>"""
        
        return sitemap_xml