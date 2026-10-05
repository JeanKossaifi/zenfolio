"""Exercise the installed package, including non-Python scaffold assets."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


def test_installed_wheel_initializes_and_builds_a_site(tmp_path):
    repository = Path(__file__).parents[1]
    source = tmp_path / "source"
    source.mkdir()
    for filename in ("pyproject.toml", "README.md"):
        shutil.copy2(repository / filename, source / filename)
    shutil.copytree(
        repository / "src", source / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"),
    )

    environment = dict(os.environ, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1")

    def run(*arguments, cwd=tmp_path):
        result = subprocess.run(
            [sys.executable, *arguments], cwd=cwd, env=environment,
            text=True, capture_output=True, timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    wheels = tmp_path / "wheels"
    wheels.mkdir()
    run(
        "-c", "from setuptools.build_meta import build_wheel; "
        "import sys; build_wheel(sys.argv[1])", str(wheels), cwd=source,
    )
    wheel = next(wheels.glob("*.whl"))
    installed = tmp_path / "installed"
    run("-m", "pip", "install", "--no-deps", "--target", str(installed), str(wheel))
    environment["PYTHONPATH"] = str(installed)
    run(
        "-c", "from pathlib import Path; import sys, zenfolio; "
        "Path(zenfolio.__file__).relative_to(Path(sys.argv[1]))", str(installed),
    )

    site = tmp_path / "site"
    run("-m", "zenfolio", "init", "--content-dir", str(site))
    for filename in ("config.py", "index.md", "news.py", "projects.py", "talks.py"):
        assert (site / filename).is_file(), f"Installed scaffold omitted {filename}"
    run("-m", "zenfolio", "build", "--content-dir", str(site), "--dev")
    homepage = (site / "_site" / "index.html").read_text(encoding="utf-8")
    assert "Your bio here." in homepage
    assert (site / "_site" / "static" / "theme.css").is_file()
