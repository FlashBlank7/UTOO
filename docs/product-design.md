# UTOO Product Design

Last updated: 2026-06-28

## 1. Positioning

UTOO is an independent forum-style platform for international students in Japan. It is not tied to one university. The product should feel like a practical student information system rather than a marketing site:

- school-based boards for concrete campus information;
- a public area for cross-school questions and casual discussion;
- authenticated access for reading and posting;
- dense, readable, low-friction forum workflows;
- clear separation between regular users, admins, moderators, agents, and mascot ambience.

The public-facing positioning is:

- Chinese: `留学生平台`
- English: `International Student Platform`
- Japanese: `留学生プラットフォーム`

## 2. Core Information Architecture

The forum hierarchy is fixed at two levels:

```text
学校 / 公共区 -> 一级板块 -> 子板块
```

There is no infinite nesting. This keeps navigation, moderation, and posting rules understandable.

### Schools

Schools do not require user-side application. A user should go directly to the corresponding school board. If a school is missing, the correct workflow is:

1. Admin adds the school through the admin console or a seed migration.
2. The system creates the default first-level boards.
3. Users can immediately enter the school board from the school switcher.

User-facing “apply for school” is no longer part of the target product design. It can be removed or kept only as an admin-facing maintenance note, not as a primary community action.

If a user leaves school blank, the profile defaults to `枝江大学`.

### Zhijiang University

`枝江大学` is a virtual public area, not a real school.

It has two jobs:

- it is the public cross-school square;
- it is the default displayed school for users who do not fill in a real school.

Zhijiang University is a special page, not a standard school template. It should use original ASOUL / Zhijiang-inspired atmosphere:

- public square framing;
- cheering / broadcast / dorm-night / help-relay modules;
- brighter accent colors than normal school pages;
- original decorations only, with no official ASOUL assets, logos, screenshots, or confusing marks.

The special style must not damage core forum readability. It should be playful around the edges, not become a decorative landing page.

## 3. Boards And Subboards

Every real school starts with:

```text
公告, 课程, 研究室, 生活, 租房, 就职, 闲聊
```

Zhijiang University starts with:

```text
公告, 综合讨论, 提问求助, 生活, 租房, 就职, 闲聊
```

First-level boards are structural. Once created and approved, they should not be removable from the admin UI. Admins may edit their descriptions and ordering, but not hide/delete core first-level boards casually.

Subboards are optional. They exist to split a busy first-level board, such as:

```text
课程 -> 计算机课程
研究室 -> 情报系研究室
租房 -> 生驹 / 奈良 / 大阪通勤
```

When a user enters a subboard, the UI must make that state obvious:

- breadcrumb: `学校 / 一级板块 / 子板块`;
- page title: `子板块 · 一级板块 / 子板块`;
- post tags: `一级板块 > 子板块`;
- admin review rows: `一级板块 / 子板块`.

The first-level board navigation should appear only once. The current duplicate two-row feeling is a UI bug: top-level boards should not be repeated as both a full row and a second equivalent list. The second row should be reserved for child boards of the active parent only.

## 4. Board And School Descriptions

School pages and board introductions are content, not hardcoded UI copy.

Target editing rule:

- admins can edit descriptions for any school, first-level board, and subboard;
- moderators can edit descriptions within the school/board scope they moderate;
- regular users cannot edit descriptions;
- description edits should be auditable later, even if v1 only stores the latest text.

Examples of editable description content:

- Zhijiang University public-area explanation;
- school board intro;
- board scope, posting rules, or FAQ;
- subboard purpose.

This is especially important for Zhijiang University, because its public-area identity and decorations are part of the product experience.

## 5. Posting Experience

Users select a school and board context first, then read or post within that context.

Post list behavior:

- pinned announcements appear above ordinary posts;
- posts show category, school, board path, author/source, time, and reply count;
- search works by title and content;
- category filters are secondary to school/board context.

Post detail behavior:

- clicking a post from a board should open an in-page detail panel or drawer;
- direct `/post/:id` routes remain available for refresh/share compatibility;
- comments, editing, deletion, reporting, and stickers work in both contexts.

## 6. Accounts And Identity

Users have separate login identity and display identity:

- `username`: login handle;
- `display_name`: public nickname;
- `school`: matched real school or Zhijiang University default;
- `school_name_custom`: optional display fallback for unmatched input;
- `department`: optional.

Blank school means Zhijiang University. Blank department is valid.

Agent accounts are separate from user accounts. Agent-created content must be visibly marked as Agent content.

## 7. Governance

The platform should support a small but real moderation loop:

- users can report posts/comments;
- admins can hide/delete content;
- admins can ban or mute users;
- admin actions are logged;
- deleted content is soft-deleted;
- hidden content is not shown in normal user lists.

Moderator scope is school-wide in v1:

```text
application from any board -> approved school moderator -> manages all boards in that school
```

Moderators are an admin subset. They can manage board structure, descriptions, school-scoped reports, and content visibility inside their assigned school. They cannot manage activation codes, agents, users, bans/mutes, or school creation.

Board deletion is a soft archive operation. Administrators and school moderators hide boards from normal navigation, while existing posts and audit history remain intact.

## 8. Admin Console

The admin console is an operational tool, not a public page. It should stay dense and clear.

Admin responsibilities:

- activation codes;
- users and password resets;
- moderation queue;
- content visibility;
- announcements;
- board/subboard review;
- moderator application review;
- school catalog maintenance;
- agent management;
- audit logs.

Admins can directly create a missing school. School creation should create default first-level boards automatically.

## 9. Yutoko / 優都子

Yutoko is the original UTOO mascot:

```text
Yutoko / 優都子 / ゆとこ
```

Her role is ambience and lightweight interaction, not core content authority.

Rules:

- visible on public/login/school/post contexts;
- hidden by default in admin tools;
- compact pose in post detail contexts;
- does not block buttons, inputs, or reading;
- can react to search/post/comment/report events;
- uses original assets only.

Zhijiang University can give Yutoko a more playful public-square position, but real school pages should keep her quieter.

## 10. Current Implementation Gaps

These are known follow-ups beyond the current v1:

- Add finer moderator assignment controls if school-wide scope becomes too broad.
- Add moderator removal/deactivation UI for administrators.
- Add richer report context in the management queue, such as target title and direct links.
- Decide whether historical school request records should stay visible in admin or be retired completely.

## 11. Deployment Notes

`main` is production. Any change to schema, migrations, frontend build, or Azure runtime must pass:

```bash
cd frontend && npm run build
cd backend && python3 -m compileall app alembic
python scripts/azure_parity_check.py --require-static
```

The Azure runtime is a single FastAPI App Service serving both `/api/v1/*` and built Vue static assets. Deployment success is not enough; `/health` must return `{"status":"ok"}`.
