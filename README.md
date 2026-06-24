# UTOO

UTOO 是一个匿名/实名发帖与评论应用，包含：

- 后端：FastAPI + SQLAlchemy + Alembic
- 前端：Vue 3 + Vite + Pinia
- 数据库：PostgreSQL

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

## Azure App Service 部署

本项目支持部署到单个 Azure App Service Python 应用：

- FastAPI 提供 `/api/v1/*` 接口
- FastAPI 同时托管 Vue 构建后的静态文件
- 用户只需要访问一个域名：`https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net`

GitHub Actions 工作流位于：

```text
.github/workflows/main_UTOO-dev.yml
```

工作流会在推送到 `main` 时：

1. 构建 `frontend`
2. 把 `frontend/dist` 复制到 `backend/app/static`
3. 校验后端依赖和 Python 编译
4. 将 `backend` 部署到 Azure App Service

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

Azure App Service 需要设置以下应用配置：

```text
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/<database>?ssl=require
SECRET_KEY=<生产随机长字符串>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
SCM_DO_BUILD_DURING_DEPLOYMENT=true
ALLOWED_ORIGINS=https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net
```

部署后验证：

```bash
curl https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net/health
curl https://utoo-dev-f9d3b4fteaaqb8e9.japaneast-01.azurewebsites.net/api/v1/posts
```
