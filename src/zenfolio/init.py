"""
This module contains the site initialization logic for the ZenFolio website generator.
"""
import shutil
from pathlib import Path


def init_site(content_dir: Path):
    """Initialize a new academic website project"""
    print(f"🚀 Initializing new academic website in {content_dir}")
    
    content_dir.mkdir(parents=True, exist_ok=True)
    
    template_dir = Path(__file__).parent / "templates"
    
    files_to_copy = [
        ("config.py", "Configuration file"),
        ("index.md", "Bio and about page"),
        ("news.py", "News content"),
        ("projects.py", "Projects content"),
        ("talks.py", "Talks content"),
    ]
    
    for filename, description in files_to_copy:
        src = template_dir / filename
        dest = content_dir / filename
        if src.exists() and not dest.exists():
            shutil.copy2(src, dest)
            print(f"✅ Created {filename} - {description}")
    
    static_dir = content_dir / "static"
    static_dir.mkdir(exist_ok=True)
    
    publications_file = content_dir / "publications.bib"
    if not publications_file.exists():
        publications_file.write_text("% Add your BibTeX publications here\n")
        print("✅ Created publications.bib - Empty BibTeX file")
    
    profile_placeholder = static_dir / "profile.jpg"
    if not profile_placeholder.exists():
        print("📝 Add your profile photo as static/profile.jpg")
    
    print(f"✅ Academic website initialized in {content_dir}")
    print(f"📝 Edit {content_dir}/config.py to customize your site")
    print(f"📝 Edit {content_dir}/index.md to write your bio")
    print(f"📝 Edit {content_dir}/news.py, projects.py, talks.py to add content")
    print(f"📝 Edit {content_dir}/publications.bib to add your publications")
