# 项目全局重构方案

## 📋 问题分析

### 当前存在的核心问题

1. **代码组织混乱**
   - 每个页面目录下同时存在 `index.tsx` 和 `Simple.tsx` 两个版本
   - `App.tsx` 中路由指向 `Simple.tsx`，导致接口对接错误
   - 代码文件过大（Problem 960行、Review 403行），逻辑混杂，难以维护

2. **目录结构不合理**
   - 所有页面都使用目录+index.tsx结构，但简单页面不需要
   - 缺少全局共享组件和工具函数
   - 页面特定逻辑和共享逻辑混在一起

3. **代码复用性差**
   - 相似功能在不同页面重复实现
   - 缺少统一的hooks和工具函数
   - 类型定义分散，缺少统一管理

4. **临时文件未清理**
   - `App-backup.tsx`、`App-original.tsx` 备份文件
   - 所有 `Simple.tsx` 临时展示文件
   - 根目录临时脚本和测试文件

5. **项目结构不规范**
   - 根目录文件过多，缺少分类
   - 脚本文件散落
   - 缺少统一的文档目录

---

## 🎯 重构目标与原则

### 核心目标

1. **代码可维护性**：拆分大文件，按功能模块组织
2. **结构清晰性**：简单页面扁平化，复杂页面模块化
3. **代码复用性**：提取共享组件、hooks、工具函数
4. **类型安全性**：统一类型定义，集中管理
5. **项目整洁性**：清理临时文件，规范目录结构

### 设计原则

1. **统一目录结构**
   - **所有页面**：统一使用目录结构 `PageName/index.tsx`
   - 便于未来扩展，避免后续重构
   - 保持结构一致性，降低维护成本

2. **按功能模块拆分**
   - 所有页面可拆分为：components、hooks、types、utils
   - 页面特定资源放在页面目录下
   - 全局共享资源放在全局目录
   - 简单页面暂时只有 `index.tsx`，复杂后逐步拆分

3. **关注点分离**
   - UI组件：纯展示逻辑
   - Hooks：业务逻辑和状态管理
   - Utils：工具函数和数据处理
   - Types：类型定义

---

## ✅ 团队约定（精简版，优先落地）

> 目标：**结构清晰、规则少但强约束**，5 人协作不踩坑。

1. **不要过度模块化（按痛点拆分）**
   - 只优先拆“超大文件/高耦合页面”
   - 优先级建议：
     - `Problem/index.tsx`（~960 行）优先拆
     - `Review/index.tsx`（~400 行）视情况拆
     - `Dashboard/Materials/Login`（~100–220 行）暂时单文件即可

2. **API 层口径统一（减少争论成本）**
   - 所有 HTTP 请求统一放在 `frontend/src/api/`
     - 建议按资源拆：`tasks.ts / users.ts / materials.ts / reviews.ts / problems.ts`
   - `frontend/src/services/` 只放“纯业务计算/非 HTTP 的工具”，避免 `api/` 和 `services/` 混用
   - 页面中禁止直接 `import axios from 'axios'` 发请求（统一走 `src/api`）

3. **命名统一（语义清晰 + 精简）**
   - 页面目录：`PascalCase`（已满足）
   - 页面入口：一律 `index.tsx`
   - 组件文件：`ComponentName.tsx`（一眼知道是组件）
   - Hook 文件：`useXxx.ts`（一眼知道是 Hook）
   - 工具文件：`xxx.ts`（动词/名词语义明确，比如 `formatDate.ts` / `validation.ts`）
   - 样式文件：保持一致且可识别（建议二选一，团队定一个即可）
     - 方案 A：每页 `styles.css`（简单）
     - 方案 B：每页 `<PageName>.css`（更直观）

---

## 📁 全新的目录结构设计

### 整体架构

```
math_tasks/
├── README.md                    # 项目主文档
├── QUICKSTART.md                # 快速开始指南
├── CONTRIBUTING.md              # 贡献指南
│
├── backend/                     # 后端服务（保持不变）
│   └── ...
│
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── api/                 # API 调用层
│   │   │   ├── auth.ts
│   │   │   ├── problems.ts
│   │   │   ├── tasks.ts
│   │   │   ├── reviews.ts
│   │   │   ├── materials.ts
│   │   │   ├── users.ts
│   │   │   ├── axios.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── components/          # 全局共享组件
│   │   │   ├── common/          # 通用组件
│   │   │   │   ├── Loading.tsx
│   │   │   │   ├── ErrorBoundary.tsx
│   │   │   │   └── EmptyState.tsx
│   │   │   ├── forms/           # 表单组件
│   │   │   │   └── ...
│   │   │   └── tables/          # 表格组件
│   │   │       └── ...
│   │   │
│   │   ├── hooks/               # 全局共享 Hooks
│   │   │   ├── useTask.ts       # 任务管理（已有）
│   │   │   ├── usePagination.ts
│   │   │   ├── useDebounce.ts
│   │   │   └── ...
│   │   │
│   │   ├── utils/               # 全局工具函数
│   │   │   ├── format.ts        # 格式化工具
│   │   │   ├── validation.ts   # 验证工具
│   │   │   ├── date.ts          # 日期工具
│   │   │   └── ...
│   │   │
│   │   ├── types/               # 全局类型定义
│   │   │   ├── index.ts         # 统一导出
│   │   │   ├── user.ts
│   │   │   ├── problem.ts
│   │   │   ├── task.ts
│   │   │   └── ...
│   │   │
│   │   ├── store/               # 状态管理
│   │   │   └── useAuthStore.ts
│   │   │
│   │   ├── config/              # 配置文件
│   │   │   └── constants.ts
│   │   │
│   │   ├── layouts/             # 布局组件
│   │   │   ├── MainLayout.tsx
│   │   │   └── MainLayout.css
│   │   │
│   │   ├── pages/               # 页面组件（统一目录结构）
│   │   │   │
│   │   │   ├── Dashboard/      # 简单页面：统一目录结构
│   │   │   │   └── index.tsx
│   │   │   │
│   │   │   ├── Materials/      # 简单页面：统一目录结构
│   │   │   │   └── index.tsx
│   │   │   │
│   │   │   ├── Login/          # 简单页面：统一目录结构
│   │   │   │   ├── index.tsx
│   │   │   │   └── Login.css
│   │   │   │
│   │   │   ├── Problem/         # 复杂页面：模块化（960行）
│   │   │   │   ├── index.tsx    # 主页面，组装各个步骤
│   │   │   │   ├── types.ts     # 页面特定类型
│   │   │   │   ├── hooks/       # 页面特定 Hooks
│   │   │   │   │   ├── useProblemValidation.ts
│   │   │   │   │   ├── useProblemTransform.ts
│   │   │   │   │   └── useQualityCheck.ts
│   │   │   │   ├── components/  # 页面特定组件
│   │   │   │   │   ├── ProblemValidationStep.tsx
│   │   │   │   │   ├── ProblemTransformStep.tsx
│   │   │   │   │   ├── QualityCheckStep.tsx
│   │   │   │   │   ├── ProblemTable.tsx
│   │   │   │   │   └── VariantTable.tsx
│   │   │   │   └── utils/       # 页面特定工具
│   │   │   │       └── validationQueue.ts
│   │   │   │
│   │   │   ├── Review/          # 复杂页面：模块化（403行）
│   │   │   │   ├── index.tsx
│   │   │   │   ├── types.ts
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── useReviewTask.ts
│   │   │   │   │   └── useReviewFlow.ts
│   │   │   │   └── components/
│   │   │   │       ├── CorrectnessStep.tsx
│   │   │   │       ├── ScoringStep.tsx
│   │   │   │       └── ProblemDisplay.tsx
│   │   │   │
│   │   │   ├── Tasks/          # 复杂页面：模块化（359行）
│   │   │   │   ├── index.tsx
│   │   │   │   ├── hooks/
│   │   │   │   │   └── useTask.ts  # 可移到全局或保留
│   │   │   │   └── components/
│   │   │   │       ├── TaskList.tsx
│   │   │   │       ├── ClaimTaskModal.tsx
│   │   │   │       └── TaskStats.tsx
│   │   │   │
│   │   │   └── Admin/          # 复杂页面：模块化（326行）
│   │   │       ├── index.tsx
│   │   │       ├── hooks/
│   │   │       │   └── useUserManagement.ts
│   │   │       └── components/
│   │   │           ├── UserTable.tsx
│   │   │           ├── UserStats.tsx
│   │   │           └── ImpersonateModal.tsx
│   │   │
│   │   ├── App.tsx             # 主应用组件
│   │   └── main.tsx            # 入口文件
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── scripts/                     # 项目级脚本
│   ├── setup.sh
│   ├── start.sh
│   ├── stop.sh
│   ├── restart.sh
│   ├── logs.sh
│
│
├── docs/                        # 项目级文档
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEPLOYMENT.md
│
├── data/                        # 数据文件
│   └── materials_data.json
│
└── .gitignore
```

### 页面复杂度分类

| 页面 | 行数 | 复杂度 | 结构方案 |
|------|------|--------|----------|
| Login | ~100 | 简单 | `Login/index.tsx`（暂时单文件） |
| Materials | ~210 | 简单 | `Materials/index.tsx`（暂时单文件） |
| Dashboard | ~218 | 简单 | `Dashboard/index.tsx`（暂时单文件） |
| Admin | ~326 | 中等 | `Admin/`（需要拆分） |
| Tasks | ~359 | 中等 | `Tasks/`（需要拆分） |
| Review | ~403 | 复杂 | `Review/`（需要拆分） |
| Problem | ~960 | 非常复杂 | `Problem/`（需要拆分） |

**说明**：所有页面统一使用目录结构，简单页面暂时只有 `index.tsx`，未来变复杂时再拆分。

---

## 🔧 重构执行步骤

### 阶段一：归档临时文件（优先级：最高）

> 目标：**先归档、后验证、再删除**。任何“看起来能删”的文件都先移动到根目录临时目录 `_to_delete_later/`，待网站功能/路由/API 测试通过后再统一删除。

#### 1.1 归档所有 `Simple.tsx`（不要删除）
```bash
# 归档目录：_to_delete_later/
# 使用 git mv 保留历史，且便于后续一键删除或恢复
mkdir -p _to_delete_later/frontend/src/pages

git mv frontend/src/pages/Dashboard/Simple.tsx _to_delete_later/frontend/src/pages/Dashboard/Simple.tsx
git mv frontend/src/pages/Tasks/Simple.tsx     _to_delete_later/frontend/src/pages/Tasks/Simple.tsx
git mv frontend/src/pages/Problem/Simple.tsx   _to_delete_later/frontend/src/pages/Problem/Simple.tsx
git mv frontend/src/pages/Review/Simple.tsx    _to_delete_later/frontend/src/pages/Review/Simple.tsx
git mv frontend/src/pages/Materials/Simple.tsx _to_delete_later/frontend/src/pages/Materials/Simple.tsx
git mv frontend/src/pages/Admin/Simple.tsx     _to_delete_later/frontend/src/pages/Admin/Simple.tsx
```

#### 1.2 归档前端备份文件（不要删除）
```bash
mkdir -p _to_delete_later/frontend/src

git mv frontend/src/App-backup.tsx   _to_delete_later/frontend/src/App-backup.tsx
git mv frontend/src/App-original.tsx _to_delete_later/frontend/src/App-original.tsx
```

#### 1.3 归档根目录临时文件（不要删除）
```bash
mkdir -p _to_delete_later/root

git mv import_materials_simple.py _to_delete_later/root/import_materials_simple.py
git mv test_ocr.html             _to_delete_later/root/test_ocr.html
```

#### 1.4 立即修复路由：只保留“单一入口”（必须做）
- **规则**：每个页面只有一个入口：`pages/<PageName>/index.tsx`
- `App.tsx` 中禁止再导入 `*/Simple`
- **如果后端接口还没做完**：不要新建 `Simple.tsx`，而是在同一个 `index.tsx` 中做“优雅降级”
  - 建议模式：请求失败 → 显示 `Alert/Empty` + “接口未就绪/请联系管理员” + “重试按钮”
  - 你现在的 `Dashboard/Materials/Review` 已经基本具备这种容错，不需要另起一套页面

### 阶段二：整理根目录结构

#### 2.1 创建分类目录
```bash
mkdir scripts
mkdir docs
mkdir data
```

#### 2.2 移动脚本文件
```bash
git mv setup.sh scripts/setup.sh
git mv start.sh scripts/start.sh
git mv stop.sh scripts/stop.sh
git mv restart.sh scripts/restart.sh
git mv logs.sh scripts/logs.sh
```

#### 2.3 移动数据文件
```bash
git mv materials_data.json data/materials_data.json
```

### 阶段三：重构前端页面结构

#### 3.1 创建全局共享目录
```bash
mkdir -p frontend/src/components/common
mkdir -p frontend/src/components/forms
mkdir -p frontend/src/components/tables
```

#### 3.2 统一页面结构（所有页面使用目录）

**保持所有页面为目录结构**
- Dashboard：保持 `Dashboard/index.tsx`（暂时单文件）
- Materials：保持 `Materials/index.tsx`（暂时单文件）
- Login：保持 `Login/index.tsx` 和 `Login.css`（暂时单文件）
- 未来变复杂时，再按需拆分

#### 3.3 重构复杂页面（模块化拆分）

**Problem 页面拆分（优先级最高）**
1. 创建目录结构：
   ```bash
   mkdir -p frontend/src/pages/Problem/{hooks,components,utils}
   ```

2. 提取类型定义：
   - 创建 `Problem/types.ts`，提取 `ProblemItem`、`VariantItem` 等类型

3. 提取 Hooks：
   - `useProblemValidation.ts`：母题验证逻辑（队列处理、批量验证）
   - `useProblemTransform.ts`：题目变形逻辑
   - `useQualityCheck.ts`：质量检查逻辑

4. 提取组件：
   - `ProblemValidationStep.tsx`：步骤1 UI
   - `ProblemTransformStep.tsx`：步骤2 UI
   - `QualityCheckStep.tsx`：步骤3 UI
   - `ProblemTable.tsx`：题目列表表格
   - `VariantTable.tsx`：变体列表表格

5. 提取工具函数：
   - `validationQueue.ts`：验证队列处理逻辑

6. 重构 `index.tsx`：只保留页面组装逻辑

**Review 页面拆分**
1. 创建目录结构
2. 提取类型定义到 `Review/types.ts`
3. 提取 Hooks：
   - `useReviewTask.ts`：任务加载逻辑
   - `useReviewFlow.ts`：评分流程状态管理
4. 提取组件：
   - `CorrectnessStep.tsx`：正确性验证步骤
   - `ScoringStep.tsx`：质量评分步骤
   - `ProblemDisplay.tsx`：题目展示组件

**Tasks 页面拆分**
1. 创建目录结构
2. 提取组件：
   - `TaskList.tsx`：任务列表表格
   - `ClaimTaskModal.tsx`：领取任务对话框
   - `TaskStats.tsx`：统计卡片
3. `useTask.ts` 可保留在全局 hooks 或页面 hooks

**Admin 页面拆分**
1. 创建目录结构
2. 提取 Hooks：
   - `useUserManagement.ts`：用户管理逻辑
3. 提取组件：
   - `UserTable.tsx`：用户列表表格
   - `UserStats.tsx`：统计卡片
   - `ImpersonateModal.tsx`：冒充用户对话框

#### 3.4 更新 App.tsx 路由

**修改后：**
```typescript
// 所有页面：统一使用目录导入（自动解析 index.tsx）
import Dashboard from './pages/Dashboard';
import Materials from './pages/Materials';
import Login from './pages/Login';
import Tasks from './pages/Tasks';
import Problem from './pages/Problem';
import Review from './pages/Review';
import Admin from './pages/Admin';
```

### 阶段四：提取全局共享资源

#### 4.1 提取共享组件
- 从各个页面提取可复用的 UI 组件到 `components/common/`
- 例如：Loading、ErrorBoundary、EmptyState 等

#### 4.2 提取共享 Hooks
- 从各个页面提取可复用的逻辑到 `hooks/`
- 例如：usePagination、useDebounce 等

#### 4.3 统一类型定义
- 将页面特定的类型保留在页面目录
- 将全局类型移到 `types/` 目录
- 在 `types/index.ts` 统一导出

### 阶段五：规范化命名

#### 5.1 文件命名规范
- **所有页面主文件**：`PageName/index.tsx`（统一目录结构）
- **组件文件**：`ComponentName.tsx`（PascalCase）
- **Hook 文件**：`useHookName.ts`（camelCase，use 开头）
- **工具文件**：`utilityName.ts`（camelCase）
- **类型文件**：`types.ts` 或 `PageName.types.ts`
- **样式文件**：`ComponentName.css` 或 `PageName.css`

#### 5.2 目录命名规范
- **页面目录**：PascalCase，如 `Problem`、`Review`
- **功能目录**：camelCase，如 `hooks`、`components`、`utils`
- **分类目录**：camelCase，如 `common`、`forms`、`tables`

---

## 📝 重构检查清单

### 阶段一：归档临时文件（不删除）
- [x] 将所有 `Simple.tsx` 归档到 `_to_delete_later/`（不要删除）
- [x] 将 `App-backup.tsx` / `App-original.tsx` 归档到 `_to_delete_later/`（不要删除）
- [x] 将根目录临时文件归档到 `_to_delete_later/`（不要删除）
- [x] 更新 `App.tsx`：路由只指向 `index.tsx`（单一入口）
- [ ] 提交到 Git（创建备份点）

### 阶段二：整理根目录
- [x] 创建 `scripts/`、`docs/`、`data/` 目录
- [x] 移动脚本文件到 `scripts/`
- [x] 移动数据文件到 `data/`
- [x] 更新脚本中的路径引用（如有）

### 阶段三：统一页面结构
- [x] 确保所有页面使用目录结构（Dashboard、Materials、Login、Tasks、Problem、Review、Admin）
- [x] 检查所有页面的 `index.tsx` 文件存在
- [ ] 测试所有页面功能正常

### 阶段四：重构复杂页面 - Problem（最高优先级）
- [x] 创建 Problem 目录结构（hooks、components、utils）
- [x] 提取类型定义到 `types.ts`
- [x] 提取验证逻辑到 `useProblemValidation.ts`
- [x] 提取变形逻辑到 `useProblemTransform.ts`
- [x] 提取质检逻辑到 `useQualityCheck.ts`
- [x] 提取验证队列工具到 `utils/validationQueue.ts`
- [x] 拆分 UI 组件（5个组件）
- [x] 重构 `index.tsx` 只保留组装逻辑
- [ ] 测试 Problem 页面所有功能

### 阶段五：重构复杂页面 - Review
- [x] 创建 Review 目录结构
- [x] 提取类型定义
- [x] 提取 Hooks（2个）
- [x] 提取组件（3个）
- [x] 重构 `index.tsx`
- [ ] 测试 Review 页面功能

### 阶段六：重构复杂页面 - Tasks
- [x] 创建 Tasks 目录结构
- [x] 提取组件（3个）
- [x] 重构 `index.tsx`
- [ ] 测试 Tasks 页面功能

### 阶段七：重构复杂页面 - Admin
- [x] 创建 Admin 目录结构
- [x] 提取 Hook（1个）
- [x] 提取组件（3个）
- [x] 重构 `index.tsx`
- [ ] 测试 Admin 页面功能

### 阶段八：提取全局共享资源
- [x] 创建全局 components 目录结构
- [x] 提取共享组件到 `components/common/`（Loading / EmptyState / ErrorBoundary）
- [x] 提取共享 Hooks 到 `hooks/`（useDebounce）
- [ ] 统一类型定义到 `types/`（建议先不做大迁移）
- [ ] 更新所有导入路径（按需逐步替换）

### 阶段九：更新路由和导入
- [x] 更新 `App.tsx` 中所有页面导入
- [ ] 确保所有路由正常工作
- [ ] 检查所有导入路径无错误

### 阶段十：测试验证
- [ ] 所有页面可以正常访问
- [ ] 所有路由跳转正常
- [ ] 所有 API 调用正常
- [ ] 所有功能测试通过
- [ ] 构建生产版本无错误
- [ ] 代码无 TypeScript 错误
- [ ] 代码无 ESLint 错误

---

## ⚠️ 注意事项

1. **备份重要数据**
   - 在删除文件前，建议先提交到 Git，或创建备份分支

2. **逐步重构**
   - 建议分阶段进行，每完成一个阶段就测试一次
   - 不要一次性删除所有文件

3. **更新脚本路径**
   - 如果脚本文件移动到 `scripts/` 目录，需要更新脚本内的相对路径

4. **团队协作**
   - 重构前通知团队成员
   - 在重构分支进行，完成后合并到主分支

---

## 🚀 执行建议

### 方案 A：保守方案（推荐）
1. 创建新分支 `refactor/cleanup`
2. 先将 Simple/备份/临时文件**归档到 `_to_delete_later/`**（不要删除）
3. 更新 `App.tsx` 路由（只指向 `index.tsx`）
4. 测试所有功能
5. 功能确认无误后再统一删除 `_to_delete_later/` 中的文件
6. 提交并合并

### 方案 B：激进方案
1. 创建新分支 `refactor/full-restructure`
2. 一次性完成所有重构
3. 全面测试
4. 提交并合并

**建议使用方案 A**，更安全可控。

---

## 📊 预期收益

1. **代码清晰度提升**
   - 消除 Simple 文件带来的混淆
   - 统一页面入口，降低维护成本

2. **减少错误**
   - 避免误用 Simple 版本导致接口对接问题
   - 统一命名规范，减少查找文件的时间

3. **项目结构优化**
   - 根目录更整洁
   - 文件分类更清晰
   - 便于新成员理解项目结构

4. **维护性提升**
   - 删除冗余文件，减少维护负担
   - 规范化结构，便于后续扩展

---

## 🔄 后续优化建议

### 代码质量
1. **添加单元测试**
   - 为关键 Hooks 添加测试
   - 为复杂组件添加测试
   - 使用 Vitest 或 Jest

2. **添加 E2E 测试**
   - 使用 Playwright 或 Cypress
   - 覆盖主要用户流程

3. **代码规范**
   - 配置 ESLint 规则
   - 配置 Prettier 格式化
   - 添加 pre-commit hooks

### 性能优化
1. **代码分割**
   - 使用 React.lazy 实现路由级别的代码分割
   - 优化首屏加载时间

2. **组件优化**
   - 使用 React.memo 优化重渲染
   - 使用 useMemo 和 useCallback 优化计算

### 开发体验
1. **开发工具**
   - 添加 Storybook 用于组件开发
   - 添加组件文档

2. **类型安全**
   - 完善类型定义
   - 使用严格模式 TypeScript

### 文档完善
1. **开发文档**
   - 组件使用指南
   - Hooks 使用指南
   - 页面开发规范

2. **架构文档**
   - 更新架构图
   - 添加数据流图


## ✅ 完成标准

### 基础标准（最小可行）
1. ✅ 所有 `Simple.tsx` 文件已删除
2. ✅ 所有备份文件已删除
3. ✅ 所有页面统一使用目录结构（`PageName/index.tsx`）
4. ✅ `App.tsx` 中所有路由指向正确版本
5. ✅ 根目录整洁，文件分类清晰
6. ✅ 所有功能测试通过

### 完整标准（推荐目标）
1. ✅ 所有页面统一使用目录结构（`PageName/index.tsx`）
2. ✅ Problem 页面拆分为多个模块（hooks、components、utils）
3. ✅ Review、Tasks、Admin 页面完成模块化拆分
4. ✅ 简单页面（Dashboard、Materials、Login）暂时单文件，未来可扩展
5. ✅ 全局共享组件和 Hooks 已提取
6. ✅ 类型定义统一管理
7. ✅ 代码文件大小合理（单个文件 < 300 行）
8. ✅ 代码复用性提升，无重复逻辑
9. ✅ 所有功能测试通过
10. ✅ 构建生产版本无错误
11. ✅ 代码质量检查通过（TypeScript、ESLint）

---

**最后更新**：2025-01-XX  
**文档维护者**：开发团队

