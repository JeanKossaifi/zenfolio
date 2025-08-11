from pathlib import Path
import pytest
from bs4 import BeautifulSoup

# --- Test Data ---

# These are the key sections we expect to find on the main page.
# This list acts as a contract for the homepage's structure.
EXPECTED_HOMEPAGE_SECTIONS = [
    "About Me",
    "Featured Work",
    "Academic Service",
    "Selected Publications",
    "Recent News"
]

# --- Tests ---

def test_build_succeeds(built_site):
    """Test that the site builds successfully and the index exists."""
    assert built_site.exists(), "The '_site' directory should be created."
    index_path = built_site / "index.html"
    assert index_path.exists(), "The main index.html file should be created."

def test_homepage_structure_and_layout(built_site):
    """
    Verify that the main page has the correct structure and consistent layout.
    """
    index_path = built_site / "index.html"
    soup = BeautifulSoup(index_path.read_text(encoding='utf-8'), "html.parser")
    
    # Find all section headers
    section_titles = {h2.text.strip() for h2 in soup.find_all('h2', class_='heading')}
    
    # 1. Structural Integrity: Check if all expected sections are present
    missing_sections = set(EXPECTED_HOMEPAGE_SECTIONS) - section_titles
    assert not missing_sections, f"Homepage is missing the following sections: {missing_sections}"
    
    # 2. Layout Consistency: Check that every section has the correct containers
    all_sections = soup.find_all('section')
    
    # All sections should correspond to the expected homepage sections
    assert len(all_sections) >= len(EXPECTED_HOMEPAGE_SECTIONS), \
        f"Found fewer sections ({len(all_sections)}) than expected ({len(EXPECTED_HOMEPAGE_SECTIONS)})."
        
    content_sections = all_sections
        
    for section in content_sections:
        # Every section must have the outer container for full-width backgrounds
        outer_container = section.find('div', class_='max-w-7xl')
        assert outer_container is not None, f"A section is missing the outer 'max-w-7xl' container. Section starts with: {str(section)[:100]}"
        
        # Every content section's title block or content should be present
        # Hero section has different structure, so check for content containers
        header = (outer_container.find('div', class_='max-w-3xl') or 
                 outer_container.find('div', class_='max-w-4xl') or
                 outer_container.find('div', class_='grid'))  # Hero section structure
        assert header is not None, f"A section is missing its content container. Section starts with: {str(section)[:100]}"
