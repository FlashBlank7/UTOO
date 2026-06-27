# Azure Deployment Lessons

This project currently deploys to one Azure App Service Python app:

- Public site: `https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net`
- Workflow: `.github/workflows/main_UTOO-dev.yml`
- Runtime app: FastAPI serving both `/api/v1/*` and the built Vue SPA
- Production data on the free/small setup: SQLite at `/home/data/utoo.db`

## What Went Wrong

The site failure on 2026-06-25 was not a normal frontend or backend compile
failure. Local checks passed, but Azure still returned `503 Application Error`
or temporarily `403 This web app is stopped`.

The failure pattern was:

1. GitHub Actions could build the frontend.
2. GitHub Actions could install Python dependencies and compile the backend.
3. Azure login and App Service configuration succeeded.
4. The slow/failing point was Azure App Service ZIP deployment / Kudu / OneDeploy.
5. A workflow version that stopped the App Service before deploy made things
   worse, because canceling or interrupting a run could leave the site stopped.

## Rules For Future Deployments

- Do not stop the production App Service before deployment.
- Do not cancel a deployment run casually once it reaches the Azure deploy step.
- Treat `main` as production. Develop on `dev` or a feature branch and merge only
  after local checks pass.
- Do not use `main` pushes as a rapid feedback loop for mascot/image iterations.
  Validate frontend changes locally first.
- A green GitHub Actions run only means the artifact was accepted; always verify
  `/health` after deployment.
- A GitHub Actions warning about Node.js action runtime is not the main failure
  signal unless the action itself fails. The important signal is the failed step.
- Azure App Service ZIP deploy is not true hot deployment. It can lock files,
  restart the Python process, and take several minutes.

## Current Workflow Shape

The workflow intentionally vendors Python dependencies into:

```text
backend/.python_packages/lib/site-packages
```

Then it deploys `backend-deploy.zip` to Azure. This avoids relying on Azure Oryx
to install Python dependencies at runtime, which previously failed or stalled.

Current Azure App Settings managed by the workflow include:

```text
SCM_DO_BUILD_DURING_DEPLOYMENT=false
ENABLE_ORYX_BUILD=false
DATABASE_URL=sqlite+aiosqlite:////home/data/utoo.db
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=30
```

Because dependencies are packaged inside the deployment ZIP, deployment is slower
than a small source-only upload. That is the tradeoff for avoiding Oryx runtime
build failures.

## Safe Release Checklist

Read the consistency contract first:

```text
docs/deployment-consistency.md
```

Before merging to `main`:

```bash
cd backend
python3 -m compileall app alembic
```

```bash
cd frontend
npm run build
```

Then validate the Azure App Service runtime shape:

```bash
rm -rf backend/app/static
mkdir -p backend/app/static
cp -R frontend/dist/. backend/app/static/
python scripts/azure_parity_check.py --require-static
```

After the GitHub Actions run starts:

1. Do not cancel it while it is deploying.
2. Wait for the deploy step to finish or time out.
3. Verify:

```bash
curl https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net/health
```

Expected response:

```json
{"status":"ok"}
```

If the site shows `403 This web app is stopped`, start the App Service from the
Azure Portal before doing anything else.

If `/health` returns `503 Application Error`, check App Service application logs
before pushing more commits.

## Better Long-Term Options

- Use a separate `dev` App Service for preview deployments.
- Use deployment slots if the Azure plan supports them.
- Move to a container-based deployment so dependencies are built once into an
  image instead of being ZIP-deployed each release.
- Keep mascot/source-art iteration out of production deploys until the local
  frontend has been visually checked.
