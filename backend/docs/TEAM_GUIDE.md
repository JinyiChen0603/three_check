# 🎯 MathTasks - 团队快速上手指南

> **给同事的测试指南** - 5分钟快速启动

---

## 📋 项目简介

**MathTasks** 是一个数学题目众包平台，包含完整的出题和评分功能。

**当前状态**: ✅ 后端API已完成（100%），可以测试所有功能

---

## 🚀 快速启动（3步）

### 步骤 1: 克隆项目

```bash
git clone [仓库地址]
cd 出题平台

# 切换到dev分支
git checkout dev
```

### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入API Keys
nano .env
```

**必需的API Keys**（请联系项目负责人获取）：
- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`
- `DOUBAO_API_KEY`
- `SECRET_KEY`（任意强密码）

### 步骤 3: 启动服务

```bash
# 启动Docker服务
docker compose up -d

# 初始化数据库
docker compose exec api alembic upgrade head
docker compose exec api python scripts/init_users.py
docker compose exec api python scripts/init_materials.py

# 检查服务状态
docker compose ps
```

**启动成功标志**：
```
✅ mathtasks-api    Up
✅ mathtasks-db     Up (healthy)
```

---

## 🧪 测试功能

### 方式1: Swagger UI（推荐）

1. **打开浏览器访问**: http://localhost:8000/docs

2. **登录获取Token**:
   - 找到 "认证" → `POST /api/auth/login`
   - 点击 "Try it out"
   - 输入用户名和密码（见下方测试账户）
   - 点击 "Execute"
   - 复制返回的 `access_token`

3. **设置Token**:
   - 点击右上角的 🔒 **Authorize** 按钮
   - 粘贴 token
   - 点击 "Authorize" 和 "Close"

4. **测试其他API**:
   - 现在可以测试任何接口了！
   - 每个接口都有 "Try it out" 按钮

### 方式2: 命令行（快速测试）

```bash
# 健康检查
curl http://localhost:8000/health

# 登录
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=hewenze&password=user123"

# 查看资料库
curl -X GET "http://localhost:8000/api/materials/categories" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 👥 测试账户

### 管理员账户
- **用户名**: `lifanghe` | **密码**: `admin123`
- **用户名**: `gexinlin` | **密码**: `admin123`

### 普通用户账户
- **用户名**: `hewenze` | **密码**: `user123`
- **用户名**: `chenjinyi` | **密码**: `user123`

⚠️ **注意**: 请勿在测试时修改这些账户的密码，其他同事也需要使用。

---

## 🧩 核心功能测试清单

### ✅ 认证功能
- [ ] 登录（4个账户都测试）
- [ ] 修改密码
- [ ] 管理员访客模式切换
- [ ] 查看当前用户信息

### ✅ 资料库
- [ ] 查看12个类别
- [ ] 查看资料列表
- [ ] 查看资料详情
- [ ] 记录下载

### ✅ 出题流程
- [ ] OCR识别图片中的题目
- [ ] 单题验证（Doubao 8次验证）
- [ ] 批量验证（最多10题）
- [ ] 创建题目
- [ ] 生成题目变体（DeepSeek）
- [ ] 三维质检（难度+原创性+严谨性）

### ✅ 评分流程
- [ ] 获取4选1选项
- [ ] 提交正确性验证
- [ ] 提交创新性和严谨性评分
- [ ] 查看我的评分记录

### ✅ 任务管理
- [ ] 领取任务（最多50个）
- [ ] 查看我的任务
- [ ] 放弃单个任务
- [ ] 放弃批次任务
- [ ] 查看任务统计

### ✅ 用户和财务
- [ ] 查看我的统计信息
- [ ] 查看排行榜
- [ ] 查看交易记录
- [ ] 查看余额详情

---

## 📊 API 端点总览

| 模块 | 端点数 | 前缀 |
|------|--------|------|
| 认证 | 5 | `/api/auth` |
| 用户管理 | 6 | `/api/users` |
| 资料库 | 5 | `/api/materials` |
| 题目管理 | 8 | `/api/problems` |
| 评分管理 | 5 | `/api/reviews` |
| 任务管理 | 7 | `/api/tasks` |
| **总计** | **40+** | |

详细文档：http://localhost:8000/docs

---

## 🐛 遇到问题？

### 问题1: Docker服务启动失败

```bash
# 查看日志
docker compose logs -f api

# 重启服务
docker compose restart
```

### 问题2: 数据库连接失败

```bash
# 检查PostgreSQL状态
docker compose ps postgres

# 重启数据库
docker compose restart postgres
```

### 问题3: API返回401错误

**原因**: Token过期或未设置

**解决**: 重新登录获取新的Token

### 问题4: 端口被占用

```bash
# 修改 docker-compose.yml 中的端口
# 将 "8000:8000" 改为 "8001:8000"
```

---

## 📝 测试反馈

### 请记录以下信息：

**✅ 工作正常的功能**:
- [ ] 
- [ ] 
- [ ] 

**❌ 发现的问题**:
1. **问题描述**:
   - 重现步骤:
   - 错误信息:
   - 截图:

2. **问题描述**:
   - ...

**💡 改进建议**:
- 
- 

---

## 🔧 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看API日志
docker compose logs -f api

# 查看数据库日志
docker compose logs -f postgres

# 重启所有服务
docker compose restart

# 停止所有服务
docker compose down

# 完全清理（包括数据）
docker compose down -v
```

---

## 📚 完整文档

项目包含以下详细文档：

1. **README.md** - 项目总览
2. **DEPLOYMENT_GUIDE.md** - 完整部署指南（含所有API示例）
3. **DATABASE_SCHEMA.md** - 数据库设计文档
4. **PROGRESS.md** - 开发进度报告
5. **docs/QUICK_START.md** - 快速启动指南

---

## 💬 联系方式

**遇到问题请联系**:
- 项目负责人: [您的联系方式]
- 技术支持群: [群组链接]

---

## ⚠️ 注意事项

1. ✅ 这是 **dev 分支**，可以随意测试
2. ❌ 请勿修改测试账户的密码
3. ✅ 发现问题及时反馈
4. ✅ 测试完成后记得 `docker compose down`

---

## 🎉 测试愉快！

如有任何问题，随时联系项目组！

