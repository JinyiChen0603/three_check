# 数学题目三重质检工具

<div align="center">

**一个基于 AI 的数学题目质量检测工具**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend: React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://reactjs.org/)

</div>

---

## 📋 项目简介

数学题目三重质检工具是一个纯粹的AI质检服务，提供三项核心检测功能：

- 🎯 **难度检测**: 使用 Doubao AI 对抗验证（8次回答，≤4次正确为合格）
- 🔍 **原创性检测**: 使用 GPT-Research 联网搜索检测
- ✅ **严谨性检测**: 使用 GPT-4 检查数学严谨性
- 📷 **OCR识别**: 支持图片识别（可选功能）

**特点**：
- ✨ 无需登录，直接使用
- 💾 不保存任何数据，纯质检工具
- 🚀 实时进度显示（SSE）
- 📊 详细的检测报告

---

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- Node.js 18+（前端开发）
- Python 3.11+（后端开发）

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/mathtasks-quality-check.git
cd mathtasks-quality-check
```

### 2. 配置API密钥

编辑 `backend/.env` 文件，填入API密钥：

```env
# OpenAI API（用于OCR和GPT检测）
OPENROUTER_API_KEY=sk-or-v1-...

# DeepSeek API（可选，用于题目生成）
CANOPY_WAVE_API_KEY=_...

# Doubao API（用于难度检测）
DOUBAO_API_KEY=...

# Redis（用于进度追踪）
REDIS_URL=redis://redis:6379/0
```

### 3. 启动服务

#### 方式一：Docker Compose（推荐）

```bash
docker compose up -d --build
```

访问：
- 前端：http://localhost:5173
- 后端：http://localhost:8001
- API文档：http://localhost:8001/docs

#### 方式二：手动启动

**启动后端**:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**启动前端**:

```bash
cd frontend
npm install
npm run dev
```

---

## 🏗️ 项目结构

```
mathtasks-quality-check/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/
│   │   │   └── problems.py  # 质检API
│   │   ├── services/
│   │   │   ├── difficulty_check_service.py   # 难度检测
│   │   │   ├── originality_check_service.py  # 原创性检测
│   │   │   ├── rigor_check_service.py        # 严谨性检测
│   │   │   ├── ocr_service.py                # OCR识别
│   │   │   ├── progress_service.py           # 进度管理
│   │   │   └── llm/                          # LLM客户端
│   │   ├── config.py
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/                # React 前端
│   ├── src/
│   │   ├── api/             # API调用
│   │   ├── components/      # 组件
│   │   ├── pages/
│   │   │   └── QualityCheck/  # 主页面
│   │   └── store/           # 状态管理
│   └── package.json
│
└── README.md
```

---

## ✨ 核心功能

### 1. 难度检测

- 使用 Doubao AI 进行8次对抗验证
- ≤4次正确为合格（难度适中）
- 实时进度显示（SSE）
- 详细的每次尝试记录

### 2. 原创性检测

- 使用 GPT-Research 联网搜索
- 检测题目是否为原创
- AI评价和详细说明

### 3. 严谨性检测

- 使用 GPT-4 检查数学严谨性
- 验证题目表述、条件完整性、答案正确性
- AI评价和改进建议

### 4. OCR识别（可选）

- 支持图片上传识别题目
- 使用 GPT-4o 进行OCR
- 自动提取题目、答案、解析

---

## 🔧 技术栈

### 后端
- **框架**: FastAPI（异步）
- **AI服务**: OpenAI GPT-4、Doubao、DeepSeek
- **进度管理**: Redis + SSE
- **容器化**: Docker

### 前端
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5
- **状态管理**: Zustand
- **HTTP**: Axios
- **构建**: Vite

---

## 📖 API文档

启动服务后访问 http://localhost:8001/docs 查看完整的API文档。

### 主要API端点

- `POST /api/problems/ocr` - OCR识别
- `POST /api/problems/check-difficulty-start` - 启动难度检测
- `GET /api/problems/check-difficulty-stream/{task_id}` - SSE进度流
- `POST /api/problems/check-originality` - 原创性检测
- `POST /api/problems/check-rigor` - 严谨性检测

---

## 🤝 贡献指南

欢迎贡献代码！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证。

---

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

<div align="center">

**Made with ❤️ by MathTasks Team**

</div>
