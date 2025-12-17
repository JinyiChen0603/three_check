# 🚀 快速启动指南

## 前置要求

- Docker 和 Docker Compose
- 已准备好的 API Keys（DeepSeek, GPT-4o, Doubao）

---

## 步骤 1: 配置环境变量

### 1.1 创建 .env 文件
```bash
cd /Users/kylinge/Desktop/出题平台
cp .env.example .env
```

### 1.2 编辑 .env 文件
```bash
# 使用你喜欢的编辑器打开 .env
nano .env
# 或
vim .env
# 或
code .env
```

### 1.3 填入你的 API Keys
```env
# AI API Keys（必填！）
DEEPSEEK_API_KEY=sk-your-deepseek-key
OPENAI_API_KEY=sk-your-openai-key
DOUBAO_API_KEY=your-doubao-key

# 数据库配置（保持默认即可）
DATABASE_URL=postgresql+asyncpg://mathtasks:mathtasks123@postgres:5432/mathtasks

# 安全配置（生产环境请修改）
SECRET_KEY=your-very-secret-key-change-me-in-production
```

---

## 步骤 2: 启动服务

### 2.1 启动 Docker 容器
```bash
docker-compose up -d
```

### 2.2 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 只查看 API 服务日志
docker-compose logs -f api
```

### 2.3 验证服务状态
```bash
# 检查容器运行状态
docker-compose ps

# 应该看到：
# NAME                STATUS
# mathtasks-api       Up
# mathtasks-db        Up (healthy)
```

---

## 步骤 3: 初始化数据库

### 3.1 运行数据库迁移
```bash
docker-compose exec api alembic revision --autogenerate -m "Initial migration"
docker-compose exec api alembic upgrade head
```

### 3.2 创建初始用户
```bash
docker-compose exec api python scripts/init_users.py
```

你会看到类似输出：
```
🚀 开始初始化用户...
✅ 创建用户: lifanghe (admin)
✅ 创建用户: gexinlin (admin)
✅ 创建用户: hewenze (user)
✅ 创建用户: chenjinyi (user)

🎉 初始用户创建完成！

==================================================
初始账户信息：
==================================================

【管理员账户】
  用户名: lifanghe  | 密码: admin123
  用户名: gexinlin  | 密码: admin123

【普通用户账户】
  用户名: hewenze   | 密码: user123
  用户名: chenjinyi | 密码: user123

⚠️  生产环境请立即修改这些默认密码！
==================================================
```

---

## 步骤 4: 访问应用

### 4.1 API 文档
打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4.2 健康检查
```bash
curl http://localhost:8000/health
```

预期输出：
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 4.3 数据库管理（可选）
启动 pgAdmin：
```bash
docker-compose --profile dev up -d pgadmin
```

访问：http://localhost:5050
- Email: admin@mathtasks.com
- Password: admin123

---

## 步骤 5: 测试 API

### 5.1 获取访问令牌
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=lifanghe&password=admin123"
```

### 5.2 访问受保护的端点
```bash
# 使用上一步获得的 token
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 常用命令

### 查看日志
```bash
# 所有服务
docker-compose logs -f

# 只看 API
docker-compose logs -f api

# 只看数据库
docker-compose logs -f postgres
```

### 进入容器
```bash
# 进入 API 容器
docker-compose exec api bash

# 进入数据库容器
docker-compose exec postgres psql -U mathtasks -d mathtasks
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 只重启 API
docker-compose restart api
```

### 停止服务
```bash
# 停止但保留数据
docker-compose down

# 停止并删除所有数据（⚠️ 谨慎使用）
docker-compose down -v
```

### 数据库操作
```bash
# 创建新的迁移
docker-compose exec api alembic revision --autogenerate -m "描述"

# 应用迁移
docker-compose exec api alembic upgrade head

# 回滚迁移
docker-compose exec api alembic downgrade -1

# 查看迁移历史
docker-compose exec api alembic history
```

---

## 故障排查

### 问题 1: 端口被占用
```bash
# 检查端口占用
lsof -i :8000
lsof -i :5432

# 修改 docker-compose.yml 中的端口映射
# 例如：将 "8000:8000" 改为 "8001:8000"
```

### 问题 2: 数据库连接失败
```bash
# 检查数据库是否健康
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### 问题 3: 代码修改未生效
```bash
# 重建容器
docker-compose up -d --build

# 或清理后重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 问题 4: 数据库迁移失败
```bash
# 查看当前迁移状态
docker-compose exec api alembic current

# 标记当前数据库为最新（危险操作）
docker-compose exec api alembic stamp head

# 完全重置数据库（开发环境）
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/init_users.py
```

---

## 开发模式 vs 生产模式

### 开发模式（当前配置）
- 代码热重载（`--reload`）
- SQL 查询日志（`echo=True`）
- 详细错误信息
- 简单密码（admin123, user123）

### 生产模式建议
1. **修改密码**: 立即更改所有默认密码
2. **SECRET_KEY**: 使用强随机密钥
3. **DEBUG**: 设置为 `false`
4. **CORS**: 限制允许的源
5. **HTTPS**: 使用反向代理（Nginx）配置 SSL
6. **数据备份**: 定期备份 PostgreSQL 数据卷

---

## 下一步

✅ 基础设施已搭建完成！

接下来你可以：
1. 开发业务 API 路由（app/api/）
2. 实现 AI 服务集成（app/services/）
3. 添加前端界面
4. 编写测试用例（tests/）

参考文档：
- [数据库 Schema](./DATABASE_SCHEMA.md)
- [API 文档](http://localhost:8000/docs)

