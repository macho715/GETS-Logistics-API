# /deploy preflight

Runs deployment preflight guard against PROD_URL.

## Required
- `PROD_URL` environment variable (explicit)

## Run
```bash
chmod +x scripts/deploy_preflight.sh
export PROD_URL="https://<your-prod-app>.vercel.app"
./scripts/deploy_preflight.sh
```

## Expected
- Exit 0 and prints schemaVersion
- Any failure: exit 1; do not deploy

