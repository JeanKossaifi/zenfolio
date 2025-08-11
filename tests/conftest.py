"""Pytest fixtures - everything you need in one place"""
import pytest
import shutil
from pathlib import Path
from zenfolio.zenfolio import ZenFolio

# Define the root of the project and the actual website content
WEBSITE_ROOT = Path(__file__).parent.parent.parent / "website"
ZENFOLIO_ROOT = Path(__file__).parent.parent

@pytest.fixture(scope="session")
def site_root(tmp_path_factory):
    """A pytest fixture to create a temporary, clean copy of the actual website."""
    tmp_dir = tmp_path_factory.mktemp("test-site")
    shutil.copytree(WEBSITE_ROOT, tmp_dir, dirs_exist_ok=True)
    return tmp_dir

@pytest.fixture(scope="session")
def built_site(site_root):
    """A pytest fixture that builds the site and returns the output path."""
    try:
        # Instantiate the builder and build the site
        ssg = ZenFolio(content_dir=site_root, theme_override="tailwind", debug=True)
        success = ssg.build()
        if not success:
            pytest.fail("The ZenFolio build failed. See stdout/stderr for details.", pytrace=False)
    except Exception as e:
        pytest.fail(f"The ZenFolio build failed with an exception: {e}", pytrace=False)
        
    # The output directory is determined by the ZenFolio configuration
    output_dir = ssg.output_dir
    
    if not output_dir.exists():
        pytest.fail(f"The build completed but the output directory '{output_dir}' was not created.")
        
    return output_dir
