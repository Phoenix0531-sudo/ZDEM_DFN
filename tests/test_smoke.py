"""Smoke tests — keep green on empty / thin packages."""
from pathlib import Path
import importlib
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_repo_has_readme():
    assert (ROOT / 'README.md').exists()


def test_license_present():
    assert any((ROOT / n).exists() for n in ('LICENSE', 'LICENSE.md', 'LICENSE.txt'))


PACKAGES = ['zdem_dfn']


def test_packages_importable():
    for name in PACKAGES:
        importlib.import_module(name)

