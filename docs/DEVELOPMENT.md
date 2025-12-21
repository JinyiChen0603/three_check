# 开发入口（统一）

本仓库是一个 monorepo：`frontend/`（React） + `backend/`（FastAPI）。

## 方式 A：一键起全栈（推荐给演示/预发/快速验收）

> 使用根目录的 `docker-compose.yml`：前端由 Nginx 托管，并反代 `/api` 到后端。

### 0) 后端环境变量（可选但推荐）

根 compose 已提供可启动的默认值；如果你需要配置自己的密钥/AI Key，请在 `backend/.env` 中填写。

- 参考模板：`backend/env.template`
- 创建方式：

```bash
# Windows (PowerShell)
copy backend\\env.template backend\\.env
```

```bash
docker compose up -d --build
```

- 前端：http://localhost:5173
- 后端（直连）：http://localhost:8001
- API Docs：http://localhost:8001/docs

（可选）pgAdmin：

```bash
docker compose --profile dev up -d pgadmin
```

pgAdmin：http://localhost:5050

## 方式 B：前端本地开发（最快，热更新）

> 适合日常开发：前端本地 Vite + 后端（Docker 或本地）都可。

### 1) 启动后端（Docker）

```bash
cd backend
docker compose up -d
```

后端：http://localhost:8001

### 2) 启动前端（本地）

```bash
cd frontend
npm install
npm run dev
```

前端：http://localhost:5173


