# Deployment Consistency

UTOO has two useful local shapes, but only one production shape. Most "works
locally, fails on server" incidents came from validating the wrong shape.

## Production Contract

Azure App Service production currently means:

- One Linux Python App Service: `UTOO-dev`.
- Public URL: `https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net`.
- Startup command: `bash startup.sh`.
- FastAPI serves both `/api/v1/*` and Vue static files from `backend/app/static`.
- Database: SQLite at `sqlite+aiosqlite:////home/data/utoo.db`.
- Python dependencies are vendored into `backend/.python_packages/lib/site-packages`.
- Oryx build is disabled:
  - `SCM_DO_BUILD_DURING_DEPLOYMENT=false`
  - `ENABLE_ORYX_BUILD=false`

Docker Compose is still useful, but it uses PostgreSQL and separate frontend /
backend containers. Docker success does not prove the Azure SQLite startup path.

## Why Consistency Broke

The recurring mismatch came from four sources:

- **Database mismatch**: local Docker used PostgreSQL, while Azure free/small
  deployment used SQLite. Alembic migrations that worked on PostgreSQL failed on
  SQLite when adding foreign keys outside batch mode.
- **Startup mismatch**: local development used `uvicorn --reload`; Azure uses
  `gunicorn -k uvicorn.workers.UvicornWorker` through `startup.sh`.
- **Artifact mismatch**: local frontend dev used Vite, while Azure serves the
  built Vue files copied into `backend/app/static`.
- **Deploy/runtime mismatch**: GitHub Actions can compile and upload an artifact
  while Azure App Service still returns `503 Application Error`.

## Required Parity Gate

Before merging or pushing deployment-sensitive code, run:

```bash
cd frontend
npm run build
```

```bash
rm -rf backend/app/static
mkdir -p backend/app/static
cp -R frontend/dist/. backend/app/static/
python scripts/azure_parity_check.py --require-static
```

The parity script must pass all of these checks:

- Compile backend Python files.
- Run the full Alembic chain against a fresh SQLite database.
- Run the latest SQLite migration from a simulated half-applied state, because
  Azure can retain DDL from a failed startup migration while `alembic_version`
  still points at the previous revision.
- Verify the Alembic version expected by `scripts/azure_parity_check.py`.
- Verify `枝江大学` exists as `virtual_public`.
- Verify seeded school and board counts.
- Boot FastAPI with the Azure-style gunicorn/uvicorn worker.
- Return `{"status":"ok"}` from `/health`.

GitHub Actions runs the same parity check before vendoring dependencies and
deploying. If this check fails, do not deploy.

## Migration Rules

- Any migration that alters existing SQLite tables must use
  `op.batch_alter_table`.
- Foreign keys created in batch mode must have explicit names.
- If a migration is intended to support Azure, test it from an empty SQLite
  database, not only against the existing local PostgreSQL volume.
- For migrations that create tables and then alter existing SQLite tables, make
  the upgrade recoverable when the new tables already exist but Alembic has not
  advanced the version yet.
- Keep migrations idempotent where this project already has defensive checks.

## Release Rules

- Treat `main` as production.
- Avoid rapid-fire pushes to `main`; use local checks or a branch first.
- The workflow uses `concurrency.cancel-in-progress: true` so a newer production
  fix can release a stuck Azure deploy run. Avoid using that as a normal retry
  habit; investigate the failed step after the site is stable.
- Do not stop the App Service before deploy.
- A successful build is not enough. Production is healthy only when:

```bash
curl https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net/health
```

returns:

```json
{"status":"ok"}
```

## If Azure Is Down

Use this order:

1. Check the latest GitHub Actions run and identify the exact failed step.
2. Check `/health`; distinguish `503`, `403`, timeout, and `200`.
3. If deploy failed at ZIP Deploy / Kudu / OneDeploy, do not change app code
   blindly; inspect Azure deployment logs.
4. If deploy succeeded but `/health` fails, inspect App Service Log Stream for
   `startup.sh`, `alembic`, and `gunicorn` output.
5. Only push a fix after reproducing the failing path locally or in CI.

## What This Document Is For

Read this file before changing deployment, migrations, runtime settings, or
backend/frontend packaging. Its job is to keep future work aligned with the
actual Azure runtime instead of a friendlier local runtime.
