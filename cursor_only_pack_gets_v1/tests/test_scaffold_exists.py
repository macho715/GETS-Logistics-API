from pathlib import Path


def test_scaffold_exists() -> None:
    assert Path("src/__init__.py").exists()
