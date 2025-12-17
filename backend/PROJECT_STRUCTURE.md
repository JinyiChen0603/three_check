# 📁 MathTasks 项目结构

## 当前项目文件树

```
出题平台/
├── README.md                    # 项目说明文档
├── .env.example                 # 环境变量模板
├── .gitignore                   # Git 忽略规则
├── requirements.txt             # Python 依赖
├── Dockerfile                   # Docker 构建文件
├── docker-compose.yml           # Docker Compose 配置
├── alembic.ini                  # Alembic 配置
│
├── docs/                        # 📚 文档目录
│   ├── DATABASE_SCHEMA.md       # 数据库设计文档
│   └── QUICK_START.md           # 快速启动指南
│
├── alembic/                     # 🗄️ 数据库迁移
│   ├── env.py                   # Alembic 环境配置（异步支持）
│   ├── script.py.mako           # 迁移脚本模板
│   └── versions/                # 迁移版本文件夹
│
├── scripts/                     # 🔧 脚本工具
│   └── init_users.py            # 初始化用户脚本
│
├── app/                         # 🎯 应用核心代码
│   ├── __init__.py
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 配置管理（从 .env 加载）
│   ├── database.py              # 数据库连接（异步）
│   ├── models.py                # SQLAlchemy 数据模型 ⭐
│   │
│   ├── api/                     # 🌐 API 路由（待开发）
│   │   ├── __init__.py
│   │   ├── deps.py              # 依赖注入
│   │   ├── auth.py              # 认证路由
│   │   ├── users.py             # 用户管理
│   │   ├── problems.py          # 题目管理
│   │   ├── tasks.py             # 任务管理
│   │   ├── reviews.py           # 评分管理
│   │   └── transactions.py      # 财务管理
│   │
│   ├── services/                # 🤖 业务服务（待开发）
│   │   ├── __init__.py
│   │   ├── ai_service.py        # AI 集成
│   │   ├── ocr_service.py       # OCR 服务
│   │   ├── validation_service.py  # 验证服务
│   │   └── task_service.py      # 任务分发
│   │
│   └── utils/                   # 🔨 工具函数
│       ├── __init__.py
│       ├── security.py          # 安全工具（密码加密、JWT）
│       └── helpers.py           # 辅助函数（待开发）
│
└── tests/                       # 🧪 测试（待开发）
    ├── __init__.py
    ├── test_api/
    ├── test_services/
    └── test_models/
```

---

## ✅ 已完成的模块

### 1. 核心配置
- ✅ `app/config.py` - 配置管理（Pydantic Settings）
- ✅ `app/database.py` - 异步数据库连接
- ✅ `.env.example` - 环境变量模板

### 2. 数据模型 ⭐⭐⭐
- ✅ `app/models.py` - 完整的 5 张表模型
  - User（用户）
  - Problem（题目）
  - Task（任务）
  - Review（评分）
  - Transaction（流水）

### 3. 基础设施
- ✅ `Dockerfile` - Docker 容器化
- ✅ `docker-compose.yml` - 服务编排（API + PostgreSQL + pgAdmin）
- ✅ `requirements.txt` - Python 依赖

### 4. 数据库迁移
- ✅ `alembic.ini` - Alembic 配置
- ✅ `alembic/env.py` - 异步迁移支持

### 5. 工具脚本
- ✅ `scripts/init_users.py` - 初始化 4 个用户（2个管理员 + 2个普通用户）

### 6. 安全工具
- ✅ `app/utils/security.py` - 密码加密、JWT 令牌

### 7. FastAPI 应用
- ✅ `app/main.py` - 应用入口（生命周期管理、健康检查）

### 8. 文档
- ✅ `README.md` - 项目说明
- ✅ `docs/DATABASE_SCHEMA.md` - 数据库详细设计文档
- ✅ `docs/QUICK_START.md` - 快速启动指南

---

## 🚧 待开发模块

### 1. API 路由（app/api/）
- ⏳ `auth.py` - 登录、注销、刷新令牌
- ⏳ `users.py` - 用户管理、访客模式切换
- ⏳ `problems.py` - 出题、查看、编辑
- ⏳ `tasks.py` - 领取任务、提交任务、超时处理
- ⏳ `reviews.py` - 提交评分、查看评分
- ⏳ `transactions.py` - 查看流水、提现

### 2. 业务服务（app/services/）
- ⏳ `ai_service.py` - 集成 DeepSeek/GPT-4o/Doubao
- ⏳ `ocr_service.py` - OCR 图片识别
- ⏳ `validation_service.py` - AI 验证逻辑（8次验证）
- ⏳ `task_service.py` - 任务分发、过滤逻辑

### 3. 测试（tests/）
- ⏳ 单元测试
- ⏳ 集成测试
- ⏳ E2E 测试

---

## 🎯 关键设计亮点

### 1. 异步架构
- 全栈异步：FastAPI + SQLAlchemy Async + asyncpg
- 支持高并发场景

### 2. 类型安全
- Pydantic Settings：配置验证
- SQLAlchemy 2.0：现代化 ORM
- Python 类型注解

### 3. 可扩展性
- 枚举类型：易于扩展任务类型、交易类型
- JSON 字段：灵活存储动态数据
- 版本控制：题目版本、数据库迁移

### 4. 业务约束
- 数据库层面：外键、索引、唯一约束
- 应用层面：任务分发过滤、验证逻辑
- 索引优化：高频查询字段已建立复合索引

### 5. 开发体验
- Docker：一键启动全套环境
- Alembic：数据库版本管理
- Swagger UI：自动生成 API 文档
- 热重载：开发模式代码自动更新

---

## 📊 数据模型统计

| 表名 | 字段数 | 关系数 | 索引数 | 枚举类型 |
|------|--------|--------|--------|----------|
| User | 13 | 4 | 3 | 1 (UserRole) |
| Problem | 20 | 6 | 4 | 3 (SourceType, ValidationStatus, Status) |
| Task | 12 | 3 | 4 | 2 (TaskType, TaskStatus) |
| Review | 13 | 3 | 3 | 1 (ReviewStatus) |
| Transaction | 12 | 2 | 3 | 2 (TransactionType, TransactionStatus) |
| **总计** | **70** | **18** | **17** | **9** |

---

## 🔑 初始账户

### 管理员（Admin）
- **lifanghe** / admin123
- **gexinlin** / admin123

### 普通用户（User）
- **hewenze** / user123
- **chenjinyi** / user123

---

## 🚀 下一步建议

### Phase 1: 认证系统（优先级：高）
1. 实现 JWT 认证
2. 登录/登出接口
3. 访客模式切换

### Phase 2: 核心业务（优先级：高）
1. 出题流程 API
2. 任务分发逻辑
3. 评分提交 API

### Phase 3: AI 集成（优先级：中）
1. DeepSeek API 集成
2. Doubao 验证服务
3. OCR 识别服务

### Phase 4: 财务系统（优先级：中）
1. 奖励发放逻辑
2. 流水查询 API
3. 提现功能

### Phase 5: 前端界面（优先级：低）
1. 用户仪表盘
2. 出题界面
3. 评分界面

---

## 📝 技术债务

目前无技术债务，架构清晰，代码质量良好。

---

## 🎓 学习资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Alembic 迁移指南](https://alembic.sqlalchemy.org/)
- [Docker Compose 教程](https://docs.docker.com/compose/)

