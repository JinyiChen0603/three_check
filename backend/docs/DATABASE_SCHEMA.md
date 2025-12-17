# 数据库 Schema 设计文档

## 📋 表结构总览

MathTasks 平台包含 5 个核心数据表：

1. **User** - 用户表
2. **Problem** - 题目表
3. **Task** - 任务领取记录表
4. **Review** - 评分记录表
5. **Transaction** - 资金流水表

---

## 1. User（用户表）

### 字段说明

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK, Auto Increment |
| username | String(50) | 用户名 | Unique, Not Null, Indexed |
| email | String(100) | 邮箱 | Unique, Nullable, Indexed |
| password_hash | String(255) | 密码哈希 | Not Null |
| role | Enum | 角色（admin/user） | Not Null, Default: user |
| balance | Float | 账户余额 | Not Null, Default: 0.0 |
| problems_created_count | Integer | 创建题目数 | Not Null, Default: 0 |
| reviews_completed_count | Integer | 完成评分数 | Not Null, Default: 0 |
| is_active | Boolean | 是否激活 | Not Null, Default: True |
| is_impersonating | Boolean | 访客模式标记 | Not Null, Default: False |
| created_at | DateTime | 创建时间 | Not Null |
| updated_at | DateTime | 更新时间 | Not Null |
| last_login_at | DateTime | 最后登录时间 | Nullable |

### 关系
- `created_problems`: 一对多 → Problem（作为创建者）
- `claimed_tasks`: 一对多 → Task
- `reviews`: 一对多 → Review
- `transactions`: 一对多 → Transaction

---

## 2. Problem（题目表）

### 字段说明

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK, Auto Increment |
| creator_id | Integer | 创建者ID | FK → User.id, Indexed |
| parent_problem_id | Integer | 母题ID（自关联） | FK → Problem.id, Nullable, Indexed |
| title | String(200) | 题目标题 | Not Null |
| content | JSON | 题目详细内容 | Not Null |
| answer | Text | 标准答案 | Not Null |
| difficulty | Integer | 难度等级（1-5） | Nullable |
| category | String(50) | 题目分类 | Nullable, Indexed |
| source_type | Enum | 来源类型 | Not Null, Default: manual |
| ocr_image_url | String(500) | OCR图片URL | Nullable |
| version | Integer | 版本号 | Not Null, Default: 1 |
| validation_status | Enum | 验证状态 | Not Null, Default: not_validated, Indexed |
| validation_result | JSON | 验证结果详情 | Nullable |
| validation_correct_count | Integer | 验证正确次数 | Nullable |
| validation_completed_at | DateTime | 验证完成时间 | Nullable |
| status | Enum | 生命周期状态 | Not Null, Default: draft, Indexed |
| review_count | Integer | 完成评分数 | Not Null, Default: 0 |
| avg_quality_score | Float | 平均质量分 | Nullable |
| avg_difficulty_score | Float | 平均难度分 | Nullable |
| created_at | DateTime | 创建时间 | Not Null, Indexed |
| updated_at | DateTime | 更新时间 | Not Null |
| published_at | DateTime | 发布时间 | Nullable |

### 枚举值

**ProblemSourceType:**
- `ocr`: OCR识别
- `manual`: 手动输入
- `ai_variant`: AI变体

**ProblemValidationStatus:**
- `not_validated`: 未验证
- `validating`: 验证中
- `passed`: 验证通过（≤4次正确）
- `failed`: 验证失败（>4次正确）

**ProblemStatus:**
- `draft`: 草稿
- `pending_review`: 待审核
- `published`: 已发布
- `archived`: 已下架

### 关系
- `creator`: 多对一 → User
- `parent_problem`: 多对一 → Problem（自关联）
- `variants`: 一对多 → Problem（子变体题目）
- `tasks`: 一对多 → Task
- `reviews`: 一对多 → Review
- `transactions`: 一对多 → Transaction

### 索引
- `idx_creator_status`: (creator_id, status)
- `idx_validation_status`: (validation_status, status)

---

## 3. Task（任务领取记录表）

### 字段说明

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK, Auto Increment |
| problem_id | Integer | 题目ID | FK → Problem.id, Indexed |
| user_id | Integer | 领取人ID | FK → User.id, Indexed |
| task_type | Enum | 任务类型 | Not Null, Default: review_problem |
| status | Enum | 任务状态 | Not Null, Default: pending, Indexed |
| claimed_at | DateTime | 领取时间 | Nullable |
| expires_at | DateTime | 过期时间 | Nullable, Indexed |
| submitted_at | DateTime | 提交时间 | Nullable |
| approved_at | DateTime | 批准时间 | Nullable |
| result_data | JSON | 任务结果数据 | Nullable |
| created_at | DateTime | 创建时间 | Not Null |
| updated_at | DateTime | 更新时间 | Not Null |

### 枚举值

**TaskType:**
- `review_problem`: 评分任务
- `create_problem`: 出题任务（可扩展）

**TaskStatus:**
- `pending`: 待领取
- `in_progress`: 进行中
- `submitted`: 已提交
- `approved`: 已批准
- `rejected`: 已驳回
- `timeout`: 已超时

### 关系
- `problem`: 多对一 → Problem
- `user`: 多对一 → User
- `review`: 一对一 → Review

### 索引
- `idx_user_status`: (user_id, status)
- `idx_problem_status`: (problem_id, status)
- `idx_expires_at`: (expires_at)

### 业务逻辑
- **超时机制**: `expires_at` = `claimed_at` + 12小时
- **核心约束**: 分发任务时必须过滤 `problem.creator_id != task.user_id`

---

## 4. Review（评分记录表）

### 字段说明

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK, Auto Increment |
| problem_id | Integer | 题目ID | FK → Problem.id, Indexed |
| reviewer_id | Integer | 评分者ID | FK → User.id, Indexed |
| task_id | Integer | 关联任务ID | FK → Task.id, Unique, Nullable |
| answer_submitted | Text | 评分者提交的答案 | Not Null |
| is_answer_correct | Boolean | 答案是否正确 | Not Null |
| quality_score | Integer | 质量评分（1-5） | Nullable |
| difficulty_score | Integer | 难度评分（1-5） | Nullable |
| comment | Text | 评论 | Nullable |
| status | Enum | 评分状态 | Not Null, Default: pending, Indexed |
| admin_note | Text | 管理员备注 | Nullable |
| created_at | DateTime | 创建时间 | Not Null |
| updated_at | DateTime | 更新时间 | Not Null |
| approved_at | DateTime | 批准时间 | Nullable |

### 枚举值

**ReviewStatus:**
- `pending`: 待审核
- `approved`: 已通过
- `rejected`: 已驳回

### 关系
- `problem`: 多对一 → Problem
- `reviewer`: 多对一 → User
- `task`: 一对一 → Task

### 索引
- `idx_problem_reviewer`: (problem_id, reviewer_id)
- `idx_reviewer_status`: (reviewer_id, status)

### 业务逻辑
- **前置条件**: 只有 `is_answer_correct = True` 的评分才有效
- **核心约束**: `problem.creator_id` ≠ `reviewer_id`（不能评分自己的题目）

---

## 5. Transaction（资金流水表）

### 字段说明

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | Integer | 主键 | PK, Auto Increment |
| user_id | Integer | 用户ID | FK → User.id, Indexed |
| amount | Float | 金额（可正可负） | Not Null |
| transaction_type | Enum | 交易类型 | Not Null, Indexed |
| related_problem_id | Integer | 关联题目ID | FK → Problem.id, Nullable |
| related_task_id | Integer | 关联任务ID | FK → Task.id, Nullable |
| status | Enum | 交易状态 | Not Null, Default: pending, Indexed |
| description | String(500) | 描述 | Nullable |
| balance_after | Float | 交易后余额 | Nullable |
| created_at | DateTime | 创建时间 | Not Null, Indexed |
| updated_at | DateTime | 更新时间 | Not Null |
| confirmed_at | DateTime | 确认时间 | Nullable |

### 枚举值

**TransactionType:**
- `problem_reward`: 出题奖励（+30元）
- `review_reward`: 评分奖励（+7元）
- `withdrawal`: 提现（负数）
- `adjustment`: 调整（正负皆可）

**TransactionStatus:**
- `pending`: 待确认
- `confirmed`: 已到账
- `cancelled`: 已取消

### 关系
- `user`: 多对一 → User
- `related_problem`: 多对一 → Problem

### 索引
- `idx_user_type_status`: (user_id, transaction_type, status)
- `idx_created_at`: (created_at)

### 业务逻辑
- **双向记账**: `amount` 可正可负
- **状态流转**: pending → confirmed（到账）
- **余额快照**: `balance_after` 记录交易后的用户余额

---

## 🔗 表关系图

```
User (用户)
├─→ Problem (题目) [1:N, creator_id]
├─→ Task (任务) [1:N, user_id]
├─→ Review (评分) [1:N, reviewer_id]
└─→ Transaction (流水) [1:N, user_id]

Problem (题目)
├─→ Problem (母题) [1:N, parent_problem_id, 自关联]
├─→ Task (任务) [1:N, problem_id]
├─→ Review (评分) [1:N, problem_id]
└─→ Transaction (流水) [1:N, related_problem_id]

Task (任务)
└─→ Review (评分) [1:1, task_id]
```

---

## 🚀 核心业务约束

### 1. 任务分发约束
```sql
-- 评分任务不能分配给题目创建者
WHERE problem.creator_id != task.user_id
```

### 2. 验证通过条件
```python
# AI 验证 8 次，正确次数 <= 4 才算合格
validation_correct_count <= 4  # 通过
validation_correct_count > 4   # 失败（题目太简单）
```

### 3. 任务超时机制
```python
expires_at = claimed_at + timedelta(hours=12)
```

### 4. 奖励金额
- **出题奖励**: 30元/题（验证通过后）
- **评分奖励**: 7元/题（评分完成后）

---

## 📊 数据流转示例

### 出题流程
```
1. User 创建 Problem (status=draft)
2. 触发 AI 验证 (validation_status=validating)
3. 验证结果记录到 validation_result
4. 如果通过 (validation_status=passed):
   - Problem.status → published
   - 创建 Transaction (type=problem_reward, amount=30, status=pending)
   - Transaction.status → confirmed
   - User.balance += 30
```

### 评分流程
```
1. 系统创建 Task (type=review_problem, status=pending)
2. User 领取 Task:
   - Task.status → in_progress
   - Task.claimed_at = now()
   - Task.expires_at = now() + 12h
3. User 提交 Review:
   - Task.status → submitted
   - Review 创建 (包含答案和评分)
4. 系统验证答案正确:
   - Review.is_answer_correct = True
   - Task.status → approved
   - 创建 Transaction (type=review_reward, amount=7)
   - User.balance += 7
```

---

## 🔍 关键查询场景

### 1. 获取可分配的评分任务
```sql
SELECT p.*
FROM problems p
WHERE p.status = 'published'
  AND p.id NOT IN (
    SELECT problem_id 
    FROM tasks 
    WHERE user_id = :current_user_id
  )
  AND p.creator_id != :current_user_id  -- 核心约束
LIMIT 50;
```

### 2. 检查任务超时
```sql
UPDATE tasks
SET status = 'timeout'
WHERE status = 'in_progress'
  AND expires_at < NOW();
```

### 3. 计算用户排名
```sql
SELECT 
  username,
  balance,
  problems_created_count,
  reviews_completed_count,
  RANK() OVER (ORDER BY balance DESC) as rank
FROM users
WHERE role = 'user'
  AND is_active = TRUE;
```

---

## 📝 注意事项

1. **时区处理**: 所有 DateTime 字段使用 UTC 时间
2. **软删除**: 推荐使用 `is_active` 标记而不是物理删除
3. **性能优化**: 已为高频查询字段添加索引
4. **数据完整性**: 使用外键约束确保引用完整性
5. **异步支持**: 所有数据库操作支持 SQLAlchemy Async

