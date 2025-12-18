# 📜 项目脚本说明

本文档说明项目中所有自动化脚本的用途和使用方法。

---

## 📋 脚本列表

| 脚本 | 用途 | 使用频率 |
|------|------|---------|
| `setup.sh` | 首次初始化配置 | 一次 |
| `start.sh` | 启动所有服务 | 每天 |
| `stop.sh` | 停止所有服务 | 每天 |
| `restart.sh` | 重启所有服务 | 偶尔 |
| `logs.sh` | 查看服务日志 | 调试时 |
| `clean.sh` | 完全清理项目 | 很少 |

---

## 🚀 setup.sh - 项目初始化

**用途：** 首次克隆项目后，运行此脚本进行完整初始化。

**功能：**
1. ✅ 检查系统依赖（Docker、Node.js、npm）
2. ✅ 配置后端环境变量（.env）
3. ✅ 安装前端依赖（npm install）
4. ✅ 启动 Docker 容器（后端 + 数据库）
5. ✅ 初始化数据库（创建表、用户、资料）
6. ✅ 验证服务状态

**使用方法：**
```bash
./setup.sh
```

**注意事项：**
- ⚠️ 只需要运行**一次**
- ⚠️ 需要先启动 Docker Desktop
- ⚠️ 脚本会提示配置 API 密钥，请编辑 `backend/.env` 文件

---

## ▶️ start.sh - 启动服务

**用途：** 一键启动所有服务（前端、后端、数据库）。

**功能：**
1. ✅ 检查 Docker 是否运行
2. ✅ 启动后端和数据库容器
3. ✅ 测试后端连接
4. ✅ 启动前端开发服务器
5. ✅ 显示访问地址和测试账号

**使用方法：**
```bash
./start.sh
```

**服务地址：**
- 前端：http://localhost:5173
- 后端：http://localhost:8001
- API 文档：http://localhost:8001/docs

---

## ⏹️ stop.sh - 停止服务

**用途：** 停止所有运行中的服务。

**功能：**
1. ✅ 停止前端进程
2. ✅ 停止后端和数据库容器

**使用方法：**
```bash
./stop.sh
```

**注意事项：**
- ✅ 数据会保留在 Docker 数据卷中
- ✅ 下次 `./start.sh` 时数据仍然存在

---

## 🔄 restart.sh - 重启服务

**用途：** 快速重启所有服务（常用于代码更新后）。

**功能：**
1. 调用 `./stop.sh` 停止服务
2. 等待 3 秒
3. 调用 `./start.sh` 启动服务

**使用方法：**
```bash
./restart.sh
```

**适用场景：**
- 🔧 修改了后端代码
- 🔧 修改了环境变量
- 🔧 服务出现异常

---

## 📋 logs.sh - 查看日志

**用途：** 查看各服务的运行日志，用于调试问题。

**功能：**
- 查看前端日志
- 查看后端日志
- 查看数据库日志

**使用方法：**
```bash
# 查看所有日志
./logs.sh

# 仅查看前端日志
./logs.sh frontend

# 仅查看后端日志
./logs.sh backend

# 仅查看数据库日志
./logs.sh database
```

**实时查看日志：**
```bash
# 前端实时日志
tail -f logs/frontend.log

# 后端实时日志
cd backend && docker compose logs -f api

# 数据库实时日志
cd backend && docker compose logs -f postgres
```

---

## 🧹 clean.sh - 完全清理

**用途：** 完全清理项目，删除所有容器和数据。

**⚠️ 警告：** 此操作会删除所有数据库数据！

**功能：**
1. 停止所有服务
2. 删除 Docker 容器和网络
3. 可选：删除数据库数据卷
4. 清理日志文件

**使用方法：**
```bash
./clean.sh
```

**使用场景：**
- 🗑️ 需要完全重新开始
- 🗑️ 数据库结构有重大变更
- 🗑️ 清理磁盘空间

**恢复步骤：**
```bash
# 清理后重新初始化
./clean.sh
./setup.sh
./start.sh
```

---

## 🛠️ 调试技巧

### 1. 查看容器状态
```bash
cd backend
docker compose ps
```

### 2. 进入数据库
```bash
cd backend
docker compose exec postgres psql -U mathtasks -d mathtasks
```

### 3. 查看后端日志（详细）
```bash
cd backend
docker compose logs api --tail 100 -f
```

### 4. 重启单个服务
```bash
cd backend
docker compose restart api      # 仅重启后端
docker compose restart postgres # 仅重启数据库
```

### 5. 查看前端构建问题
```bash
cd frontend
npm run dev    # 在前台运行，查看详细输出
```

---

## 📦 日常工作流

### 每天开始工作
```bash
# 1. 启动 Docker Desktop（如果未运行）
# 2. 启动服务
./start.sh

# 3. 访问前端
open http://localhost:5173
```

### 每天结束工作
```bash
# 停止服务（可选，也可以保持运行）
./stop.sh
```

### 遇到问题时
```bash
# 1. 查看日志
./logs.sh

# 2. 重启服务
./restart.sh

# 3. 如果还有问题，完全清理后重新初始化
./clean.sh
./setup.sh
./start.sh
```

---

## 🆘 常见问题

### Q1: 脚本没有执行权限
```bash
# 解决方法：添加执行权限
chmod +x *.sh
```

### Q2: Docker Desktop 未运行
```bash
# 解决方法：
# 1. 手动启动 Docker Desktop 应用
# 2. 等待图标变为绿色
# 3. 重新运行脚本
```

### Q3: 端口被占用
```bash
# 查找占用进程
lsof -ti:5173   # 前端
lsof -ti:8001   # 后端

# 停止进程
kill $(lsof -ti:5173)

# 或使用停止脚本
./stop.sh
```

### Q4: 前端依赖问题
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
./restart.sh
```

---

## 📚 相关文档

- [快速开始指南](./QUICKSTART.md) - 新用户入门
- [完整 README](./README.md) - 项目详细说明
- [API 文档](http://localhost:8001/docs) - 后端接口
- [部署指南](./backend/DEPLOYMENT_GUIDE.md) - 生产环境部署

---

**提示：** 所有脚本都有详细的输出信息，如果遇到问题请仔细阅读输出内容。
