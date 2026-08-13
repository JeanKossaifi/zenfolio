from bs4 import BeautifulSoup

EXPECTED_HOMEPAGE_SECTIONS = [
    "About",
    "Featured Work",
    "Selected Publications",
    "Recent News"
]

def test_build_succeeds(built_site):
    """Test that the site builds successfully and the index exists."""
    assert built_site.exists(), "The '_site' directory should be created."
    index_path = built_site / "index.html"
    assert index_path.exists(), "The main index.html file should be created."

def test_homepage_structure_and_layout(built_site):
    index_path = built_site / "index.html"
    soup = BeautifulSoup(index_path.read_text(encoding='utf-8'), "html.parser")

    sections = soup.select("section[data-section]")
    section_titles = [section.find("h2").get_text(strip=True) for section in sections]
    assert section_titles == EXPECTED_HOMEPAGE_SECTIONS
    assert soup.find("h1").get_text(strip=True) == "Ada Researcher"
    assert "PhD, Imperial College London" not in soup.get_text()
