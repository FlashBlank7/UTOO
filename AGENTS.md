# UTOO Agent Instructions

Before making changes that can affect deployment, startup, database migrations,
GitHub Actions, Azure App Service, static frontend hosting, or runtime settings,
read:

```text
docs/deployment-consistency.md
```

Do not treat Docker Compose success as proof that Azure App Service will work.
The production path is a single Python App Service using SQLite at
`/home/data/utoo.db`, vendored Python packages, `startup.sh`, and FastAPI serving
the built Vue static files.

For deployment-sensitive changes, run or preserve the Azure parity check:

```bash
python scripts/azure_parity_check.py --require-static
```

If the site is down, verify `/health` and inspect the failed GitHub Actions or
Azure App Service logs before pushing speculative fixes.
