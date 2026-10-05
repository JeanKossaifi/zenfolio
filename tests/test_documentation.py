"""Keep public configuration examples executable against the current API."""

from pathlib import Path
import re

import pytest


README = Path(__file__).parents[1] / "README.md"
README_TEXT = README.read_text(encoding="utf-8")
EXAMPLES = [
    (README_TEXT.count("\n", 0, match.start()) + 2, match.group(1))
    for match in re.finditer(r"^```python\n(.*?)^```", README_TEXT, re.M | re.S)
]


@pytest.mark.parametrize("line,source", EXAMPLES, ids=[f"line-{line}" for line, _ in EXAMPLES])
def test_readme_python_configuration_examples(line, source):
    exec(compile(source, f"{README}:{line}", "exec"), {})
