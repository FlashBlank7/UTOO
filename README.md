# UTOO · 留学生交流社区

UTOO is a personal student forum with school boards, posts, comments, moderation tools and an AI-assisted mascot, Yutoko. To try it locally, follow the two-terminal setup below, then register the first administrator at `/register` with the bootstrap code `UTOO-ADMIN` in your own fresh database.

UTOO 把校园交流按「学校 → 板块 → 子板块」组织。用户可以匿名或实名发帖、回复、使用表情包和举报内容；管理员可以处理举报、审批板块申请和生成邀请码。注册时可以不填学校，默认公共区「枝江大学」是虚拟社区。经费有限，后续开发与推广暂缓；体验公开源码可以直接在本机运行。

## 本地启动 · Local quick start

准备 Git、Python 3.12 和 Node.js 22（含 npm）。后端是 FastAPI，前端是 Vue 3。首次体验直接用 SQLite，空库迁移会创建表、学校和板块。以下命令使用全新目录和默认配置。

```sh
git clone https://github.com/FlashBlank7/UTOO.git
cd UTOO
```

**终端 1 · API。** 从仓库根目录进入 `backend`，按系统选择一组命令。保持终端运行。默认数据库写入 `backend/utoo.db`；已有 `DATABASE_URL` 会覆盖此默认值。

Windows PowerShell：

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Linux / macOS：

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

打开 [API 健康检查](http://127.0.0.1:8010/health)，应看到 `{"status":"ok"}`。接口可在 [API 文档](http://127.0.0.1:8010/docs) 查看。

**终端 2 · Web。** 从同一个仓库的根目录执行：

```sh
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

打开 [论坛](http://127.0.0.1:5174/)。前端会把 `/api` 请求转发到 8010。结束试用时在两个终端分别按 Ctrl+C；下次保留数据库，在相同目录重新启动 API 和 Web 即可。

### 试一遍注册、发帖和表情

1. 在[注册页](http://127.0.0.1:5174/register)输入新用户名、密码和激活码 `UTOO-ADMIN`。这一步用于初始化本机数据库的首个管理员。提示该码已使用时，登录原管理员账号，在 [管理后台](http://127.0.0.1:5174/admin) 生成普通邀请码。
2. 进入「枝江大学」的「闲聊」板块，发一条测试帖子，在正文中加入 `:yutoko_thanks:`。打开帖子，检查正文和表情，再留一条评论。看板角色和表情来自项目内的[素材目录](frontend/public/stickers/yutoko/)。
3. 若注册或发帖失败，先看 8010 的健康检查，再看终端 1 的迁移是否成功。未登录直接请求帖子列表会返回 401。若 5174 启动时报端口占用，先检查是否已经启动了另一个前端实例。

## Docker 与部署

需要试 PostgreSQL 或容器版时，在根目录用 Docker Engine/Desktop 和 Compose v2 启动。该方案占用宿主端口 5432、8010、5174；先停止同端口的本地服务。

```sh
docker compose up -d --build
docker compose ps
docker compose logs --tail 60 backend
```

入口仍是 [5174](http://localhost:5174/)。这里的 PostgreSQL 数据保存在 Compose 卷中，和本地 SQLite 分开，首次注册也分别进行。用 `docker compose down` 停止并保留数据。Compose 文件中的开发配置适合本机试用；在对外开放之前需设置独立密钥并完成管理员初始化。

Azure 部署采用另一种结构：FastAPI 同时提供 Vue 静态文件，SQLite 写入持久目录。配置、静态资源打包、启动命令及发布前检查见[部署一致性文档](docs/deployment-consistency.md)和[部署问题记录](docs/azure-deployment-lessons.md)。

## 项目导航

| 想了解什么 | 从哪里看 |
|---|---|
| 学校、公共区、学校别名和板块治理 | [产品设计](docs/product-design.md) |
| API、数据模型、前端与鉴权 | [技术架构](docs/technical-architecture.md) · [后端](backend/app) · [前端](frontend/src) |
| Yutoko 的形象与表情如何制作 | [形象设定](frontend/src/assets/mascot/yutoko/prompts/yutoko-v2.md) · [表情包制作笔记](frontend/src/assets/mascot/yutoko/prompts/yutoko-stickers-v1.md) |
