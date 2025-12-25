# /rules tune

Tuning checklist for Cursor rules.

## Steps
1) Confirm `AGENTS.md` ZERO fail-safe matches current production behavior.
2) If schemaVersion changes, update BOTH:
   - `AGENTS.md` lock value
   - `.cursor/rules/300-gets-api-domain.mdc`
3) Require CODEOWNERS review for `AGENTS.md`, `scripts/deploy_preflight.sh`, `vercel.json`, and any schema lock files.

