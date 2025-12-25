# /automate pre-commit+ci

Applies local dev gates and CI baseline.

## What it does
- Ensures `.pre-commit-config.yaml` and `.github/workflows/ci.yml` exist
- Installs pre-commit hooks (if pre-commit is installed)

## Run
```bash
pip install -U pre-commit
pre-commit install && pre-commit install --hook-type commit-msg
pre-commit run --all-files
```

