# MathTasks - 数学题目众包平台

<div align="center">

**一个基于 AI 的数学题目创作与质量评审平台**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend: React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://reactjs.org/)
[![Database: PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791.svg)](https://www.postgresql.org/)

</div>

---

## 📋 项目简介

MathTasks 是一个创新的数学题目众包平台，结合了多个先进的 AI 模型（GPT-4、DeepSeek Math-V2、Doubao），帮助教师和内容创作者：

- 📝 **智能出题**: 通过 AI 辅助从母题生成高质量变形题目
- 🔍 **质量保证**: 多维度 AI 验证（难度、原创性、数学严谨性）
- 👥 **协作评审**: 分布式人工评审机制
- 💰 **激励机制**: 基于质量的奖励系统（出题30元/题，评审7元/题）

---

## 🏗️ 项目结构

```
mathtasks/
├── backend/              # FastAPI 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── models.py    # 数据库模型
│   │   ├── services/    # 业务逻辑（OCR、AI验证、题目生成）
│   │   └── utils/       # 工具函数
│   ├── alembic/         # 数据库迁移
│   ├── scripts/         # 初始化脚本
│   └── docker-compose.yml
│
├── frontend/            # React + Ant Design 前端
│   ├── src/
│   │   ├── api/         # API 调用
│   │   ├── components/  # 可复用组件
│   │   ├── pages/       # 页面组件
│   │   ├── store/       # Zustand 状态管理
│   │   └── layouts/     # 布局组件
│   └── package.json
│
└── README.md           # 本文件
```

---

## ✨ 核心功能

### 👤 用户角色

#### 管理员账户
- **用户**: lifanghe, gexinlin
- **权限**: 用户管理、访客模式（查看普通用户视角）、系统监控

#### 普通用户
- **用户**: hewenze, chenjinyi（可扩展）
- **权限**: 任务领取、题目创作、评审打分

### 📚 出题流程

1. **母题验证**
   - 单题/批量验证（最多10题）
   - OCR 图片识别（GPT-4o）
   - 对抗验证（Doubao-seed-thinking-250715，8次回答，≤4次正确为合格）

2. **题目创新**
   - 使用 DeepSeek Math-V2 进行题目变形
   - 支持自定义 Prompt
   - 每题最多变形10次

3. **三维质检**
   - **难度**: Doubao 对抗验证（≤50%正确率）
   - **原创性**: GPT-Research 联网搜索检测
   - **数学严谨性**: GPT-4.1 严格性检查

4. **人工评审**
   - 合格题目进入评审队列
   - 不合格题目返回修改

### 🎯 评分流程

1. **正确性验证**
   - 4选1测试（1个正确答案 + 3个GPT生成的相似错误答案）
   - 错误时展示解题过程和标准答案
   - 用户判断正确性

2. **质量打分**
   - 创新性打分（0-10分）
   - 数学严谨性打分（0-10分）
   - 一票否决权（附带理由）

### 💼 任务管理

- ✅ 最多领取50个任务（完成后才能继续领取）
- ⏰ 12小时超时自动释放
- 🚫 可主动放弃任务
- 🔒 **不能评审自己的题目**

### 💰 激励系统

- **出题奖励**: 30元/合格题目
- **评审奖励**: 7元/完成评审
- **排名系统**: 实时展示用户收益和排名

---

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- Node.js 16+ (前端开发)
- Python 3.11+ (后端开发)

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/mathtasks.git
cd mathtasks
```

### 2. 启动后端

```bash
cd backend

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入 API Keys
# OPENAI_API_KEY=your_openai_key
# DEEPSEEK_API_KEY=your_deepseek_key
# DOUBAO_API_KEY=your_doubao_key

# 启动数据库和后端服务
docker compose up -d

# 等待服务启动（约10秒）
sleep 10

# 运行数据库迁移
docker compose exec api alembic upgrade head

# 初始化用户和资料库
docker compose exec api python scripts/init_users.py
docker compose exec api python scripts/init_materials.py

# 查看日志
docker compose logs -f api
```

**后端访问地址**: http://localhost:8001
**API 文档**: http://localhost:8001/docs

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**前端访问地址**: http://localhost:3000

### 4. 测试登录

#### 管理员账户
- 用户名: `lifanghe` 或 `gexinlin`
- 密码: `admin123`

#### 普通用户
- 用户名: `hewenze` 或 `chenjinyi`
- 密码: `user123`

---

## 🔧 技术栈

### 后端
- **框架**: FastAPI (异步)
- **数据库**: PostgreSQL 16 + SQLAlchemy (异步ORM)
- **认证**: JWT + Bcrypt
- **容器化**: Docker + Docker Compose
- **数据库迁移**: Alembic

### 前端
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design 5
- **状态管理**: Zustand
- **HTTP 客户端**: Axios
- **路由**: React Router v6
- **构建工具**: Vite

### AI 集成
- **OCR**: OpenAI GPT-4o
- **题目生成**: DeepSeek Math-V2
- **难度验证**: Doubao-seed-thinking-250715
- **原创性检测**: GPT-Research
- **严谨性检查**: GPT-4.1

---

## 📖 详细文档

- [后端部署指南](./backend/DEPLOYMENT_GUIDE.md)
- [前端部署指南](./frontend/DEPLOYMENT.md)
- [API 文档](http://localhost:8001/docs) (启动后访问)
- [数据库设计](./backend/DATABASE_SCHEMA.md)

---

## 🔐 默认账户

### 管理员 (Admin)
| 用户名 | 密码 | 角色 |
|--------|------|------|
| lifanghe | admin123 | 管理员 |
| gexinlin | admin123 | 管理员 |

### 普通用户 (Regular User)
| 用户名 | 密码 | 角色 |
|--------|------|------|
| hewenze | user123 | 普通用户 |
| chenjinyi | user123 | 普通用户 |

⚠️ **首次登录后请立即修改密码！**

---

## 🛠️ 开发指南

### 后端开发

```bash
cd backend

# 创建新的数据库迁移
docker compose exec api alembic revision --autogenerate -m "描述"

# 应用迁移
docker compose exec api alembic upgrade head

# 查看日志
docker compose logs -f api

# 重启服务
docker compose restart api
```

### 前端开发

```bash
cd frontend

# 安装新依赖
npm install package-name

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 代码检查
npm run lint
```

---

## 📊 项目状态

### ✅ 已完成功能

- [x] 用户认证与权限管理
- [x] 管理员访客模式
- [x] 任务领取与管理系统
- [x] OCR 图片识别
- [x] AI 对抗验证（难度检测）
- [x] 题目变形生成（DeepSeek Math-V2）
- [x] 三维质检系统
- [x] 人工评审流程
- [x] 财务与排名系统
- [x] 资料库管理（12个类别）
- [x] 前端完整UI（React + Ant Design）
- [x] Docker 容器化部署

### 🚧 待优化功能

- [ ] API 实际对接（前端目前使用 mock 数据）
- [ ] 文件上传与存储（OSS）
- [ ] 实时通知系统（WebSocket）
- [ ] 数据可视化仪表板
- [ ] 批量操作优化
- [ ] 性能监控与日志

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👥 团队

**开发团队**:
- lifanghe - 项目负责人 & 管理员
- gexinlin - 技术负责人 & 管理员
- hewenze - 内容创作者
- chenjinyi - 内容创作者

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件: support@mathtasks.com

---

<div align="center">

**Made with ❤️ by MathTasks Team**

</div>

