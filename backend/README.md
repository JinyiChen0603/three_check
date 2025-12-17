# MathTasks - 数学题目众包平台

## 项目简介
MathTasks 是一个基于 AI 辅助的数学题目众包平台，支持题目创建、评分和质量控制。

## 技术栈
- **Backend**: Python 3.11+ with FastAPI (Async)
- **Database**: PostgreSQL with SQLAlchemy (Async)
- **Containerization**: Docker & Docker Compose
- **AI Integration**: DeepSeek, GPT-4o, Doubao APIs

## 项目结构
```
出题平台/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models.py            # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic 模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # 依赖注入
│   │   ├── auth.py          # 认证相关
│   │   ├── users.py         # 用户管理
│   │   ├── problems.py      # 题目管理
│   │   ├── tasks.py         # 任务管理
│   │   ├── reviews.py       # 评分管理
│   │   └── transactions.py  # 财务管理
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py    # AI 集成服务
│   │   ├── ocr_service.py   # OCR 服务
│   │   ├── validation_service.py  # 验证服务
│   │   └── task_service.py  # 任务分发服务
│   └── utils/
│       ├── __init__.py
│       ├── security.py      # 安全工具
│       └── helpers.py       # 辅助函数
├── alembic/                 # 数据库迁移
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 环境准备
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Keys
```

### 2. 使用 Docker 启动
```bash
docker-compose up -d
```

### 3. 数据库迁移
```bash
docker-compose exec api alembic upgrade head
```

### 4. 创建初始用户
```bash
docker-compose exec api python scripts/init_users.py
```

## 初始账户
- **管理员**: lifanghe, gexinlin
- **普通用户**: hewenze, chenjinyi

## 核心业务逻辑

### 出题流程
1. OCR 识别 → 建立母题
2. AI 变体生成
3. AI 自动化验证（Doubao 8次，≤4次正确才合格）
4. 合格后奖励 30元/题

### 评分流程
1. 领取任务（单次上限50个，12小时超时）
2. 先做题验证正确性
3. 再对质量进行打分
4. 完成后奖励 7元/题

### 核心限制
⚠️ 用户**绝对不能**评分自己出的题目（系统分发时自动过滤）

## API 文档
启动后访问: http://localhost:8000/docs

