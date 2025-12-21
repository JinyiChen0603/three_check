# 🚀 MathTasks 快速开始指南

欢迎使用 MathTasks 数学题目众包平台！本指南将帮助你在 5 分钟内启动整个项目。

---

## 📋 前置要求

在开始之前，请确保你的电脑已安装：

- ✅ **Docker Desktop** ([下载链接](https://www.docker.com/products/docker-desktop))
- ✅ **Node.js 18+** ([下载链接](https://nodejs.org/))
- ✅ **Git** ([下载链接](https://git-scm.com/))

### 检查安装

```bash
docker --version      # 应该显示 Docker 版本
node --version        # 应该显示 Node.js 版本
npm --version         # 应该显示 npm 版本
```

---

## 🎯 快速启动（3 步）

### 步骤 1：克隆项目

```bash
git clone <你的仓库地址>
cd mathtasks
```

### 步骤 2：初始化配置

```bash
./scripts/setup.sh
```

这个脚本会自动：
- ✅ 检查系统依赖
- ✅ 配置环境变量
- ✅ 安装前端依赖
- ✅ 启动 Docker 容器
- ✅ 初始化数据库

**⚠️ 重要提示：** 脚本会提示你配置 API 密钥，请编辑 `backend/.env` 文件，填入以下密钥：

```env
OPENROUTER_API_KEY=sk-or-v1-...      # GPT-4o (必需)
CANOPY_WAVE_API_KEY=_...             # DeepSeek Math-V2 (必需)
DOUBAO_API_KEY=...                   # Doubao Seed Thinking (必需)
```

联系项目管理员获取这些密钥。

### 步骤 3：启动服务

```bash
./scripts/start.sh
```

等待几秒钟，然后访问：

🌐 **前端地址：** http://localhost:5173

---

## 👥 测试账号

初始化完成后，可以使用以下测试账号登录：

### 管理员账号
```
用户名：lifanghe     密码：admin123
用户名：gexinlin     密码：admin123
```

### 普通用户账号
```
用户名：hewenze      密码：user123
用户名：chenjinyi    密码：user123
```

---

## 🛠️ 常用命令

```bash
./scripts/start.sh      # 启动所有服务
./scripts/stop.sh       # 停止所有服务
./scripts/restart.sh    # 重启所有服务
./scripts/logs.sh       # 查看服务日志
```

### 查看日志

```bash
./scripts/logs.sh             # 查看所有日志
./scripts/logs.sh frontend    # 仅查看前端日志
./scripts/logs.sh backend     # 仅查看后端日志
./scripts/logs.sh database    # 仅查看数据库日志
```

---

## 🌐 服务地址

启动成功后，可以访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | 用户界面 |
| 后端 | http://localhost:8001 | API 服务 |
| API 文档 | http://localhost:8001/docs | Swagger 文档 |
| 数据库 | localhost:5432 | PostgreSQL |

---

## ❓ 常见问题

### 1. Docker Desktop 未运行

**错误信息：**
```
❌ Docker Desktop 未运行
```

**解决方法：**
1. 打开 Docker Desktop 应用
2. 等待 Docker 图标变为绿色（运行中）
3. 重新运行 `./scripts/setup.sh` 或 `./scripts/start.sh`

---

### 2. 端口被占用

**错误信息：**
```
⚠️  端口 5173 已被占用
```

**解决方法：**
```bash
# 查找占用端口的进程
lsof -ti:5173

# 停止该进程
kill $(lsof -ti:5173)

# 或者直接运行停止脚本
./scripts/stop.sh
```

---

### 3. 前端依赖安装失败

**错误信息：**
```
npm install 失败
```

**解决方法：**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
```

---

### 4. 后端无法连接数据库

**错误信息：**
```
socket.gaierror: Name or service not known
```

**解决方法：**
```bash
# 重启 Docker 容器
cd backend
docker compose down
docker compose up -d
cd ..

# 或者使用重启脚本
./scripts/restart.sh
```

---

### 5. API 密钥未配置

**错误信息：**
```
401 Unauthorized 或 API 调用失败
```

**解决方法：**
1. 编辑 `backend/.env` 文件
2. 填入正确的 API 密钥
3. 重启后端服务：
   ```bash
   cd backend
   docker compose restart api
   cd ..
   ```

---

## 📚 更多文档

- [完整 README](./README.md) - 项目详细说明
- [API 文档](http://localhost:8001/docs) - 后端 API 接口文档
- [数据库文档](./backend/docs/DATABASE_SCHEMA.md) - 数据库结构说明
- [部署指南](./backend/DEPLOYMENT_GUIDE.md) - 生产环境部署

---

## 🆘 获取帮助

如果遇到问题：

1. 📋 查看日志：`./scripts/logs.sh`
2. 🔧 检查服务状态：`docker compose ps`（在 backend 目录）
3. 💬 联系项目管理员
4. 🐛 提交 Issue 到 GitHub

---

## 🎉 开始使用

现在一切就绪！访问 http://localhost:5173 开始使用 MathTasks 平台吧！

**祝你使用愉快！** 🚀

