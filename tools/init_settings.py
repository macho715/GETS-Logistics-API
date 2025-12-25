from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Cursor workspace baseline")
    parser.add_argument("--git", action="store_true", help="Initialize git repository")
    parser.add_argument("--precommit", action="store_true", help="Install pre-commit hooks")
    args = parser.parse_args()

    if args.git and not Path(".git").exists():
        run(["git", "init", "-b", "main"])

    if args.precommit:
        run(["python", "-m", "pip", "install", "-U", "pre-commit"])
        run(["pre-commit", "install"])
        run(["pre-commit", "install", "--hook-type", "commit-msg"])

    print(json.dumps({"ok": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

