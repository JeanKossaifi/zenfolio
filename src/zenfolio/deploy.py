"""
This module contains deployment-related functions for the ZenFolio website generator.
"""
from pathlib import Path

from .zenfolio import get_output_dir


def create_github_pages_files(content_dir: Path):
    """Create deployment configuration files for GitHub Pages"""
    output_dir = content_dir / get_output_dir(content_dir)
    print("📦 Creating GitHub Pages deployment files...")
    
    nojekyll_file = output_dir / '.nojekyll'
    nojekyll_file.touch()
    print("✅ Created .nojekyll file for GitHub Pages")
    
    print("💡 To use a custom domain, add a CNAME file with your domain name")
    
    print("🚀 GitHub Pages deployment files ready!")
    print(f"📁 Deploy the contents of {output_dir}/ to GitHub Pages")
