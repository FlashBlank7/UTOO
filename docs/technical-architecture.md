# UTOO Technical Architecture

Last updated: 2026-06-28

This document explains how the codebase is organized and how a request moves through the system. It is meant as a practical map for future maintenance, not a complete API reference.

## 1. Runtime Shape

UTOO is a single-domain forum application.

```text
Browser
  -> Vue 3 SPA
  -> /api/v1/* requests
  -> FastAPI backend
  -> SQLAlchemy async ORM
  -> PostgreSQL locally / SQLite on current Azure free-style deployment
```

In production, FastAPI also serves the built frontend from:

```text
backend/app/static/
```

The catch-all route in `backend/app/main.py` returns `index.html` for SPA routes such as `/`, `/login`, `/schools/...`, and `/post/:id`, while `/api/v1/*` remains API-only.

## 2. Repository Layout

```text
backend/
  app/
    api/v1/          FastAPI routers grouped by product area
    core/            shared business helpers and constants
    db/              SQLAlchemy base/session setup
    models/          database models
    schemas/         Pydantic request/response schemas
    main.py          FastAPI app, router mounting, static SPA serving
  alembic/           database migrations
  startup.sh         Azure startup script

frontend/
  src/
    api/             Axios client
    assets/          local source assets, including Yutoko iterations
    components/      reusable Vue components
    router/          Vue Router route definitions and guards
    stickers/        Yutoko sticker manifest/render helpers
    stores/          Pinia auth store
    views/           page-level Vue views
    i18n.ts          zh/en/ja UI text dictionary
  public/            public static files served as-is

docs/                product, deployment, and architecture docs
scripts/             local/CI verification scripts
```

## 3. Backend Entry Points

The backend entry point is:

```text
backend/app/main.py
```

It mounts these routers:

```text
/api/v1/auth                    login, register, refresh, current user
/api/v1/posts                   post list/detail/create/edit/delete
/api/v1/comments                comments and comment deletion
/api/v1/reports                 user reports
/api/v1/schools                 school list, match, boards
/api/v1/boards                  regular user board requests
/api/v1/moderator-applications  user moderator applications
/api/v1/management              school moderator/admin scoped management
/api/v1/admin                   full admin operations
/api/v1/agent                   agent API-key posting/commenting
```

Rule of thumb:

- `admin.py` is for full-site admin powers.
- `management.py` is for admins plus approved school moderators, limited by school scope.
- `boards.py` is for regular user board requests.
- `schools.py` is read-oriented public catalog logic for logged-in users.

## 4. Core Data Model

Important models live in `backend/app/models/`.

### Users

`user.py` stores login identity, display identity, admin flag, moderation status, and school fields.

Key concepts:

- `username` is the login handle.
- `display_name` is the public nickname.
- `school_id` points to a matched school.
- blank school defaults to `枝江大学`.
- `school_name_custom` stores unmatched user-entered school text.

### Schools And Boards

`school.py` contains:

- `School`: real schools and virtual public areas.
- `SchoolAlias`: searchable aliases for school matching.
- `Board`: first-level boards and subboards.
- `SchoolModerator`: approved school-wide moderators.
- `ModeratorApplication`: requests to become moderator.
- `SchoolRequest`: legacy/request record for school creation flow.

The hierarchy is fixed:

```text
School -> Board(parent_id = null) -> Board(parent_id = parent board id)
```

Boards use status instead of physical deletion:

```text
pending, approved, rejected, hidden
```

Normal school navigation only shows `approved` boards. `hidden` means archived.

### Posts And Comments

`post.py` and `comment.py` use soft visibility:

```text
normal, hidden, deleted
```

Normal users only see `normal` content. Admin/moderator tools can act on hidden/deleted content through management/admin endpoints.

## 5. School And Board Logic

Most constants and helpers are in:

```text
backend/app/core/schools.py
```

Important items:

- `DEFAULT_SCHOOL_SLUG = "zhijiang-university"`
- `REAL_SCHOOL_BOARDS`
- `PUBLIC_SCHOOL_BOARDS`
- `CATEGORY_BOARD_SLUG`
- `PUBLIC_CATEGORY_BOARD_SLUG`
- `resolve_school_input()`
- `default_board_for_category()`

`枝江大学` is a virtual public area. It is not a real school, but it behaves like a school in the data model so that posts, boards, and moderation can reuse the same code path.

## 6. Permissions

Shared moderator permission checks live in:

```text
backend/app/core/permissions.py
```

The current rule is school-wide moderation:

```text
apply from any board -> admin approves -> user manages all boards in that school
```

Admins bypass school-scope checks. Moderators can manage only their approved schools. They cannot manage activation codes, agents, global users, bans/mutes, or school creation.

## 7. Frontend Entry Points

The Vue app starts from:

```text
frontend/src/main.ts
frontend/src/App.vue
frontend/src/router/index.ts
```

Important views:

```text
HomeView.vue       logged-out landing page plus logged-in forum/school pages
PostView.vue       direct post detail route
ManageView.vue     role-aware management page for all logged-in users
AdminView.vue      full admin console
LoginView.vue      login
RegisterView.vue   registration
AccountView.vue    profile/password
```

`HomeView.vue` is the most complex page. It handles:

- logged-out public landing;
- selected school detection;
- school switcher;
- first-level board and subboard navigation;
- post list and announcement list;
- in-page post detail drawer;
- board requests;
- moderator application;
- school/board description editing;
- board archive controls for admins/moderators.

## 8. Authentication Flow

The auth store is:

```text
frontend/src/stores/auth.ts
```

The frontend stores access and refresh tokens, refreshes proactively, and retries after token expiry where possible. Protected routes redirect unauthenticated users to login with `next`.

The backend auth router is:

```text
backend/app/api/v1/auth.py
```

Current default token durations are configured in `backend/app/core/config.py` and Azure settings:

```text
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=30
```

## 9. Yutoko Assets And Stickers

Yutoko source assets and notes:

```text
frontend/src/assets/mascot/yutoko/
```

Public sticker files:

```text
frontend/public/stickers/yutoko/
```

Sticker rendering is whitelist-based:

```text
frontend/src/stickers/yutoko.ts
frontend/src/components/StickerPicker.vue
frontend/src/components/StickerText.vue
```

Forum text stores shortcodes such as `:yutoko_thanks:`. The frontend renders only known shortcodes as images and leaves unknown text unchanged.

## 10. Migrations And Seeds

Schema changes are tracked in:

```text
backend/alembic/versions/
```

Current migrations include:

- base forum schema;
- profile/display-name changes;
- moderation fields;
- agents;
- agent comments;
- optional department;
- schools and boards;
- school descriptions;
- NAIST seed;
- school moderator tables.

When adding fields or seed data, add an Alembic migration and verify:

```bash
cd backend
python3 -m compileall app alembic
alembic upgrade head
```

## 11. Deployment Path

The production deployment is driven by:

```text
.github/workflows/main_UTOO-dev.yml
backend/startup.sh
scripts/azure_parity_check.py
```

The workflow builds the frontend, copies `frontend/dist` into `backend/app/static`, installs backend dependencies into `.python_packages`, zips `backend/`, and deploys it to Azure App Service.

Important deployment lesson:

- A green GitHub Actions run only means the package was uploaded.
- The real success signal is `/health` returning `{"status":"ok"}` from the Azure URL.

## 12. Common Maintenance Tasks

### Archive A Wrong Board

Use the school page if you are admin or moderator:

1. Open the affected school or `枝江大学`.
2. Expand `板块管理`.
3. Find the wrong first-level board or subboard.
4. Click `归档`.

This sets `boards.status = hidden`. It does not delete posts.

### Add A Missing School

Use the admin console school creation tool. Creating a school should call the backend school creation path, which also creates default first-level boards.

### Add A New Board

Admins and school moderators can create boards directly from `/manage` or the school page. Regular users submit board requests for admin review.

### Debug A Post Not Appearing

Check:

- post `visibility`;
- post `is_deleted`;
- board `status`;
- school slug/filter;
- whether it is an announcement hidden from normal lists;
- whether the viewer is authenticated.

### Debug Azure Startup

Check:

```bash
curl https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net/health
```

If `/health` fails, inspect Azure App Service logs before pushing more commits.
