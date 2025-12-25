from src.core.app import main


def test_app_runs() -> None:
    assert main() == "it works"
