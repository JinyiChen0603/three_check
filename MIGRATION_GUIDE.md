# 项目重构迁移指南

## 📢 重要变更通知

MathTasks 项目已完成重大重构，前后端代码已合并到统一的仓库结构中。

---

## 🔄 变更内容

### 旧结构
```
出题平台/                    # 只有后端
mathtasks-frontend/         # 独立的前端（可能在不同的仓库）
```

### 新结构 ✅
```
mathtasks/
├── backend/               # 后端代码（原"出题平台"）
├── frontend/              # 前端代码（原"mathtasks-frontend"）
├── README.md             # 统一的项目文档
└── CONTRIBUTING.md       # 贡献指南
```

---

## 🚀 如何迁移到新结构

### 选项1: 全新克隆（推荐）

**适用于**: 新加入的团队成员，或想要全新开始的开发者

```bash
# 1. 删除旧的目录（如果有）
cd ~/Desktop
rm -rf 出题平台 mathtasks-frontend

# 2. 克隆新的统一仓库
git clone https://github.com/Ceiling-dsk/mathtasks_v2.git mathtasks
cd mathtasks

# 3. 查看项目结构
ls -la
# 应该看到: backend/ frontend/ README.md 等
```

### 选项2: 保留旧目录，只克隆新结构

**适用于**: 想要保留旧代码作为备份的开发者

```bash
# 1. 克隆新仓库到新目录
cd ~/Desktop
git clone https://github.com/Ceiling-dsk/mathtasks_v2.git mathtasks

# 2. 旧目录保持不变（可选保留作为备份）
# 出题平台/ 和 mathtasks-frontend/ 仍然存在
```

---

## 🛠️ 启动项目（新结构）

### 后端启动

```bash
cd mathtasks/backend

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Keys

# 启动服务
docker compose up -d

# 等待服务启动
sleep 10

# 初始化数据库
docker compose exec api alembic upgrade head
docker compose exec api python scripts/init_users.py
docker compose exec api python scripts/init_materials.py

# 查看日志
docker compose logs -f api
```

**后端地址**: http://localhost:8001

### 前端启动

```bash
cd mathtasks/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**前端地址**: http://localhost:3000

---

## 📝 开发工作流（新结构）

### 1. 拉取最新代码

```bash
cd ~/Desktop/mathtasks
git pull origin main
```

### 2. 创建功能分支

```bash
# 后端开发
git checkout -b feature/backend-your-feature

# 前端开发
git checkout -b feature/frontend-your-feature

# 全栈开发
git checkout -b feature/fullstack-your-feature
```

### 3. 进行开发

```bash
# 后端开发
cd backend
# 修改代码...

# 前端开发
cd frontend
# 修改代码...
```

### 4. 提交代码

```bash
# 回到项目根目录
cd ~/Desktop/mathtasks

# 添加更改
git add .

# 提交（使用规范的提交消息）
git commit -m "feat(backend): 添加用户评分历史接口"
# 或
git commit -m "feat(frontend): 添加题目预览功能"

# 推送到远程
git push origin feature/your-feature
```

### 5. 创建 Pull Request

在 GitHub 上创建 PR，等待代码审查。

---

## 🔍 常见问题

### Q1: 我的旧代码怎么办？

**A**: 旧代码已经完整地迁移到新结构中：
- `出题平台/` → `mathtasks/backend/`
- `mathtasks-frontend/` → `mathtasks/frontend/`

您可以：
1. **删除旧目录**（推荐）- 所有代码都在新仓库中
2. **保留作为备份** - 如果您不确定，可以先保留几天

### Q2: 我正在开发的功能会丢失吗？

**A**: 不会！请按以下步骤操作：

```bash
# 1. 在旧目录提交您的更改
cd ~/Desktop/出题平台  # 或 mathtasks-frontend
git add .
git commit -m "WIP: 我的功能"

# 2. 克隆新仓库
cd ~/Desktop
git clone https://github.com/Ceiling-dsk/mathtasks_v2.git mathtasks

# 3. 手动复制您的更改到新仓库对应目录
# backend/ 或 frontend/

# 4. 在新仓库中提交
cd mathtasks
git add .
git commit -m "feat: 迁移我的功能到新结构"
git push origin feature/your-feature
```

### Q3: 环境变量 (.env) 需要重新配置吗？

**A**: 是的，但很简单：

```bash
cd mathtasks/backend

# 复制旧的 .env 文件
cp ~/Desktop/出题平台/.env .env

# 或者重新配置
cp .env.example .env
# 编辑 .env 文件
```

### Q4: Docker 容器需要重新启动吗？

**A**: 是的，建议重新启动：

```bash
# 停止旧容器
cd ~/Desktop/出题平台
docker compose down

# 启动新容器
cd ~/Desktop/mathtasks/backend
docker compose up -d
```

### Q5: 前端的 node_modules 需要重新安装吗？

**A**: 是的：

```bash
cd ~/Desktop/mathtasks/frontend
npm install
```

---

## 📚 更多资源

- [项目 README](./README.md) - 完整的项目介绍
- [贡献指南](./CONTRIBUTING.md) - 如何贡献代码
- [后端部署指南](./backend/DEPLOYMENT_GUIDE.md) - 后端详细文档
- [前端部署指南](./frontend/DEPLOYMENT.md) - 前端详细文档

---

## 💡 建议

1. **尽快迁移** - 新结构更清晰，更易于协作
2. **删除旧目录** - 避免混淆（迁移成功后）
3. **更新书签** - 将项目路径更新为 `~/Desktop/mathtasks`
4. **更新 IDE** - 在 Cursor 中打开新的 `mathtasks` 目录

---

## 📞 需要帮助？

如果您在迁移过程中遇到任何问题，请：

1. 查看本指南的常见问题部分
2. 在 GitHub 上创建 Issue
3. 联系团队成员：lifanghe 或 gexinlin

---

**祝迁移顺利！🎉**

