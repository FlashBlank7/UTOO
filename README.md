# UTOO

UTOO 是一个面向在日留学生的学校板块论坛，支持匿名/实名发帖、评论、举报、管理员治理、Agent 发帖/评论和 Yutoko 表情包。项目包含：

- 后端：FastAPI + SQLAlchemy + Alembic
- 前端：Vue 3 + Vite + Pinia
- 数据库：PostgreSQL

## 当前产品结构

- 平台定位：`留学生平台 / International Student Platform / 留学生プラットフォーム`
- 学校结构：`学校/公共区 -> 板块 -> 子板块`，固定两级，不做无限层级。
- 公共区：`枝江大学` 是虚拟学校，slug 为 `zhijiang-university`，用于公共讨论和未填写学校用户的默认展示。
- 默认学校：用户注册或更新资料时不填学校，会默认绑定并显示为 `枝江大学`。
- 学校匹配：后端会用中文、英文、日文、简称等别名匹配真实学校；匹配不到时只保存为用户自定义学校名，不自动创建公开学校板块。
- 学校维护：用户不需要申请学校，直接进入对应学校板块；缺失学校由管理员在后台创建，或通过迁移 seed。
- 学校种子：迁移会 seed THE World University Rankings 2026 日本前 50 学校，并额外 seed NAIST，为每个真实学校创建默认板块。
- 默认板块：真实学校包含 `公告`、`课程`、`研究室`、`生活`、`租房`、`就职`、`闲聊`；枝江大学包含 `公告`、`综合讨论`、`生活`、`租房`、`就职`、`闲聊`、`提问求助`。
- 板块申请：用户可申请板块或子板块，管理员在后台审核后公开。
- 产品设计文档：`docs/product-design.md`

项目默认端口已避开常见的 `3000`、`8000`、`8001`：

- 前端：http://localhost:5174
- 后端：http://localhost:8010
- API 文档：http://localhost:8010/docs

## 使用 Docker 启动

确保已经安装 Docker Desktop，然后在项目根目录运行：

```bash
docker compose up -d --build
```

首次启动时，后端容器会自动执行数据库迁移。

查看服务状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

停止服务：

```bash
docker compose down
```

如需连同数据库数据一起清理：

```bash
docker compose down -v
```

## 首次登录

先打开前端：

```text
http://localhost:5174
```

注册第一个管理员账号时，激活码填写：

```text
UTOO-ADMIN
```

管理员账号创建后，可以进入 `/admin` 生成普通用户使用的激活码。

## 本地开发启动

也可以只用 Docker 启动数据库，前后端在本机开发运行。

### 1. 启动数据库

```bash
docker compose up -d db
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://utoo:utoo_secret@localhost:5432/utoo_db alembic upgrade head
DATABASE_URL=postgresql+asyncpg://utoo:utoo_secret@localhost:5432/utoo_db uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

后端健康检查：

```bash
curl http://localhost:8010/health
```

### 3. 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

Vite 开发服务器会运行在：

```text
http://localhost:5174
```

前端开发代理会把 `/api` 请求转发到：

```text
http://localhost:8010
```

## 端口配置

当前端口配置位置：

- Docker 前端端口：`docker-compose.yml` 中的 `frontend.ports`，当前为 `5174:80`
- Docker 后端端口：`docker-compose.yml` 中的 `backend.ports`，当前为 `8010:8010`
- 后端启动端口：`backend/start.sh`，默认读取 `BACKEND_PORT`，缺省为 `8010`
- Vite 开发端口和代理：`frontend/vite.config.ts`
- Nginx 生产代理：`frontend/nginx.conf`
- 后端 CORS：`backend/app/main.py`

如果本机 `5432` 已被其他 PostgreSQL 占用，可以把 `docker-compose.yml` 里的数据库端口左侧改成其他端口，例如 `15432:5432`，并在本地开发后端时同步调整 `DATABASE_URL`。

## Yutoko / 優都子 形象与表情包素材

`Yutoko / 優都子 / ゆとこ` 是 UTOO 的原创看板娘。当前形象迭代和表情包素材保存在仓库里，方便之后继续改造：

- 七日换装透明 PNG：`frontend/src/assets/mascot/yutoko/exports/`
- 当前形象提示词与设计 notes：`frontend/src/assets/mascot/yutoko/prompts/yutoko-v2.md`
- 论坛内公开表情包：`frontend/public/stickers/yutoko/`
- 表情包 v1 提示词与制作 notes：`frontend/src/assets/mascot/yutoko/prompts/yutoko-stickers-v1.md`

表情包在帖子和评论正文里使用短代码保存，例如 `:yutoko_thanks:`、`:yutoko_cheer:`、`:yutoko_yubikubi:`。前端只渲染白名单 manifest 中定义的 Yutoko 短代码，不支持任意图片 URL 或 HTML。

## Azure App Service 免费版部署

本项目支持部署到单个 Azure App Service Python 应用：

- FastAPI 提供 `/api/v1/*` 接口
- FastAPI 同时托管 Vue 构建后的静态文件
- 免费版默认使用 SQLite，数据库文件保存在 Azure App Service 的 `/home/data/utoo.db`
- 用户只需要访问一个域名：`https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net`

GitHub Actions 工作流位于：

```text
.github/workflows/main_UTOO-dev.yml
```

部署事故复盘和发布注意事项见：

```text
docs/azure-deployment-lessons.md
```

部署一致性契约和必跑检查见：

```text
docs/deployment-consistency.md
python scripts/azure_parity_check.py --require-static
```

工作流会在推送到 `main` 时：

1. 构建 `frontend`
2. 把 `frontend/dist` 复制到 `backend/app/static`
3. 校验后端依赖、Python 编译和 Azure SQLite/gunicorn runtime parity
4. 将 Python 依赖打包进 `backend/.python_packages`
5. 配置 Azure App Service 启动命令和 SQLite `DATABASE_URL`
6. 将 `backend-deploy.zip` 部署到 Azure App Service

注意：Azure App Service ZIP Deploy 不是热部署。部署阶段可能耗时数分钟，并可能短暂重启 Python 进程。开发和素材迭代应先走本地或 `dev` 分支验证，`main` 只用于确认后的生产发布。

GitHub 仓库需要配置 Azure Deployment Center 自动生成的 OIDC secrets：

```text
AZUREAPPSERVICE_CLIENTID_...
AZUREAPPSERVICE_TENANTID_...
AZUREAPPSERVICE_SUBSCRIPTIONID_...
```

Azure App Service 需要设置 Startup Command：

```bash
bash startup.sh
```

工作流会自动设置以下应用配置：

```text
DATABASE_URL=sqlite+aiosqlite:////home/data/utoo.db
SCM_DO_BUILD_DURING_DEPLOYMENT=false
ENABLE_ORYX_BUILD=false
ALLOWED_ORIGINS=https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=30
```

当前工作流由 GitHub Actions 预装依赖并打包部署，因此不要在 Azure Portal 里手动把 Oryx 构建开关改回开启，除非同步改回 workflow 和启动脚本。

建议在 Azure App Service 的环境变量中手动设置一个生产用密钥：

```text
SECRET_KEY=<生产随机长字符串>
```

如果以后迁移到 PostgreSQL，只需要把 Azure App Service 中的 `DATABASE_URL` 改回 PostgreSQL asyncpg 连接串，例如：

```text
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/<database>?ssl=require
```

部署后验证：

```bash
curl https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net/health
curl -i https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net/api/v1/posts
```

如果线上出现 `403 This web app is stopped`，先在 Azure Portal 启动 App Service；如果出现 `503 Application Error`，先看 App Service 应用日志，不要连续盲目推送新提交。
