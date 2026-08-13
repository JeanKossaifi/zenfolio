"""Hermetic site fixtures."""

import pytest
import shutil
from pathlib import Path
from zenfolio.zenfolio import ZenFolio

FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def _copy_fixture(tmp_path_factory, name):
    tmp_dir = tmp_path_factory.mktemp(f"{name}-site") / "content"
    shutil.copytree(FIXTURES_ROOT / name, tmp_dir)
    return tmp_dir


@pytest.fixture(scope="session")
def personal_site_root(tmp_path_factory):
    return _copy_fixture(tmp_path_factory, "personal")


@pytest.fixture(scope="session")
def group_site_root(tmp_path_factory):
    return _copy_fixture(tmp_path_factory, "group")


@pytest.fixture(scope="session")
def built_site(personal_site_root):
    builder = ZenFolio(personal_site_root, debug=True)
    assert builder.build(base_url="")
    return builder.output_dir


@pytest.fixture(scope="session")
def built_group_site(group_site_root):
    builder = ZenFolio(group_site_root, debug=True)
    assert builder.build(base_url="https://example.test/research/lab/")
    return builder.output_dir
