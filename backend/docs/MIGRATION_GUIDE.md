# 数据库迁移指南

本迁移指南包含两次重要的数据库变更：
1. **删除 Problem 表**，添加变体功能支持
2. **将所有 ENUM 类型转换为 VARCHAR 字符串**，解决大小写敏感问题

---

## 📋 迁移内容概述

### **迁移 1：删除 Problem 表（68f87fd688c1）**
- ❌ 删除 `problems` 表
- ❌ 删除 `tasks.problem_id`、`reviews.problem_id`、`transactions.related_problem_id`
- ✅ 在 `ValidatedProblemExport` 表添加 `source_type` 字段（direct/variant/ocr）
- ✅ `originality_check` 和 `rigor_check` 改为可 NULL
- ✅ `reviews.validated_problem_id` 改为 NOT NULL

### **迁移 2：枚举转字符串（c666a8985e52）**
- ✅ 所有 PostgreSQL ENUM 类型转换为 VARCHAR 字符串类型
- ✅ 解决大小写敏感问题（ADMIN vs admin）
- ✅ 删除所有自定义 ENUM 类型

**涉及的字段：**
- `users.role`: `userrole` → `VARCHAR(20)`
- `tasks.task_type`: `tasktype` → `VARCHAR(50)`
- `tasks.status`: `taskstatus` → `VARCHAR(20)`
- `reviews.status`: `reviewstatus` → `VARCHAR(20)`
- `transactions.transaction_type`: `transactiontype` → `VARCHAR(50)`
- `transactions.status`: `transactionstatus` → `VARCHAR(20)`
- `material_library.category`: `materialcategory` → `VARCHAR(100)`
- `validated_problem_exports.source_type`: `validatedproblemsourcetype` → `VARCHAR(20)`
- `validated_problem_exports.admin_review_status`: `adminreviewstatus` → `VARCHAR(20)`

---

## 🚀 迁移步骤

### **步骤 0：迁移前检查**

```bash
# 1. 检查当前数据库版本
cd backend
python -m alembic current

# 记录当前版本，如果版本是 c666a8985e52 或更新，说明已经迁移过了，无需再次执行

# 2. 检查是否有不符合规范的数据（可选，如果迁移失败再回来检查）
docker-compose exec -T postgres psql -U mathtasks -d mathtasks -c "SELECT COUNT(*) FROM reviews WHERE validated_problem_id IS NULL;"

# 如果有记录，需要先清理：
# docker-compose exec -T postgres psql -U mathtasks -d mathtasks -c "DELETE FROM reviews WHERE validated_problem_id IS NULL;"

# 3. 确认 Docker 容器运行正常
docker-compose ps
```

### **步骤 1：备份数据库（必做！）**

```bash
# 方式 1：使用 docker-compose（推荐）
docker-compose exec postgres pg_dump -U mathtasks mathtasks > backup_$(date +%Y%m%d_%H%M%S).sql

# 方式 2：进入容器备份
docker-compose exec postgres bash
pg_dump -U mathtasks mathtasks > /tmp/backup.sql
exit
docker cp mathtasks-db:/tmp/backup.sql ./backup.sql
```

### **步骤 2：拉取最新代码**

```bash
git pull origin main
```

### **步骤 3：执行迁移**

```bash
cd backend
python -m alembic upgrade head
```

### **步骤 4：验证迁移结果**

```bash
# 查看当前迁移版本
python -m alembic current

# 应该显示：c666a8985e52 (head)

# 检查 ValidatedProblemExport 表结构
docker-compose exec postgres psql -U mathtasks -d mathtasks -c "\d validated_problem_exports"

# 验证 source_type 字段已添加且为 VARCHAR
docker-compose exec postgres psql -U mathtasks -d mathtasks -c "SELECT id, source_type, task_id FROM validated_problem_exports LIMIT 5;"

# 确认 problems 表已删除
docker-compose exec postgres psql -U mathtasks -d mathtasks -c "\dt problems"
# 应该显示：Did not find any relation named "problems".

# 检查所有 ENUM 类型都已删除
docker-compose exec postgres psql -U mathtasks -d mathtasks -c "\dT+"
# 应该显示：(0 rows)

# 检查 users 表的 role 字段是否为 VARCHAR
docker-compose exec postgres psql -U mathtasks -d mathtasks -c "\d users"
# role 应该是 character varying(20)

# 测试用户初始化脚本（不会有大小写问题）
cd backend
python scripts/init_users.py
```

---

## ⚠️ 注意事项

### **迁移前**
- ✅ **务必备份数据库**
- ✅ 确保 Docker 容器正在运行：`docker-compose ps`
- ✅ 确保已安装 Python 依赖：`pip install -r requirements.txt`

### **迁移后**
- ✅ 所有现有数据的 `source_type` 会自动设置为 `'direct'`
- ✅ `originality_check` 和 `rigor_check` 可以为 NULL（用于变体草稿）
- ✅ 重启后端服务：`docker-compose restart api`

### **如果迁移失败**

```bash
# 回滚到上一个版本
cd backend
python -m alembic downgrade -1

# 然后恢复备份
docker-compose exec -T postgres psql -U mathtasks -d mathtasks < backup_XXXXXX.sql
```

⚠️ **警告：回滚会丢失 `source_type` 字段和相关数据！**

---

## 📝 数据库字段说明

### **source_type 枚举值**

| 值 | 说明 | 使用场景 |
|----|------|---------|
| `direct` | 直接输入 | 在"题目验证导出"页面直接创建的题目（默认值） |
| `variant` | 变体生成 | 从"变体生成"页面保存的变体草稿 |
| `ocr` | OCR识别 | OCR识别的题目（预留） |

### **变体草稿的判断条件**

```sql
-- 我的变体草稿（未验证）
SELECT * FROM validated_problem_exports 
WHERE source_type = 'variant' AND task_id IS NULL;

-- 已验证的题目（包括变体）
SELECT * FROM validated_problem_exports 
WHERE task_id IS NOT NULL;
```

---

## 🤔 常见问题 FAQ

### **Q1: 我的同事已经有数据了，迁移会删除数据吗？**

**A**: ❌ **不会删除**。迁移只改变表结构和字段类型，所有现有数据都会保留。

- ✅ `ValidatedProblemExport` 中的所有题目数据保持不变
- ✅ 用户数据、任务数据、评分数据全部保留
- ✅ 枚举值自动转换为字符串（admin 还是 admin）
- ⚠️ **唯一例外**：`problems` 表会被删除（但这个表已经废弃）

---

### **Q2: 如果我的同事的数据库版本和我不一样怎么办？**

**A**: 使用 `alembic upgrade head` 会自动应用所有缺失的迁移。

```bash
# 检查当前版本
python -m alembic current

# 无论当前在哪个版本，都可以直接升级到最新
python -m alembic upgrade head
```

如果提示版本冲突，参考下面 Q4。

---

### **Q3: 迁移失败了怎么办？**

**A**: 常见失败原因和解决方案：

**失败 1**: `validated_problem_id cannot be null`
```bash
# 原因：有 review 记录的 validated_problem_id 是 NULL
# 解决：删除这些不符合规范的记录
docker-compose exec -T postgres psql -U mathtasks -d mathtasks -c "DELETE FROM reviews WHERE validated_problem_id IS NULL;"
```

**失败 2**: `invalid input value for enum`
```bash
# 原因：枚举类型转换失败（通常是因为有旧的数据）
# 解决：这个问题在新的迁移脚本中已经解决，重新执行即可
python -m alembic upgrade head
```

**失败 3**: `relation "problems" does not exist`
```bash
# 原因：problems 表已经被删除，但迁移脚本尝试再次删除
# 解决：这是正常的，迁移脚本会自动跳过（使用了 IF EXISTS）
```

---

### **Q4: 我的同事本地有其他迁移文件，会冲突吗？**

**A**: 会冲突。需要协调迁移顺序。

**推荐做法**：
1. 所有人先同步到相同的数据库版本（比如 `c666a8985e52`）
2. 之后的新迁移，由一个人创建并提交到 Git
3. 其他人拉取代码后执行 `upgrade head`

**如果已经冲突**：
```bash
# 方式 1：回滚到公共版本，然后重新升级
python -m alembic downgrade c666a8985e52
git pull origin main
python -m alembic upgrade head

# 方式 2：手动合并迁移（高级，需要修改迁移脚本的 down_revision）
```

---

### **Q5: 为什么要把 ENUM 改成字符串？**

**A**: 解决三个问题：

1. **大小写敏感**：PostgreSQL 的 ENUM 严格区分大小写（`ADMIN` ≠ `admin`），导致脚本执行困难
2. **修改成本高**：添加新的枚举值需要 ALTER TYPE，锁表时间长
3. **跨数据库兼容性**：VARCHAR 在所有数据库中都通用，ENUM 是 PostgreSQL 特性

代码中使用不变：
```python
# 仍然可以用常量类
user.role = UserRole.ADMIN  # "admin"
```

---

### **Q6: 迁移需要多长时间？**

**A**: 取决于数据量：

- **小数据量**（< 1万条记录）：**10-30 秒**
- **中等数据量**（1-10万条）：**1-3 分钟**
- **大数据量**（> 10万条）：**3-10 分钟**

迁移过程中：
- ✅ 数据库**不会锁表**（使用 transactional DDL）
- ⚠️ 建议在**低峰期**执行
- ⚠️ 执行期间**不要关闭终端**

---

### **Q7: 可以重复执行迁移吗？**

**A**: 不建议，但如果误操作了：

```bash
# 检查当前版本
python -m alembic current

# 如果已经是 c666a8985e52，重复执行会报错
# 解决：先回滚再升级
python -m alembic downgrade -1
python -m alembic upgrade head
```

或者直接跳过（已经迁移过就不需要再执行）。

---

### **Q8: 备份的数据库如何恢复？**

**A**: 

```bash
# 1. 停止应用（避免数据冲突）
docker-compose stop api

# 2. 恢复数据库
docker-compose exec -T postgres psql -U mathtasks -d mathtasks < backup_20260104_150000.sql

# 3. 重启应用
docker-compose start api
```

⚠️ **注意**：恢复后数据库版本会回到备份时的版本，需要重新执行迁移。

---

## 📞 联系方式

如果遇到其他问题：
1. 查看迁移日志：`backend/alembic/versions/` 目录下的迁移文件
2. 检查 Alembic 日志：运行 `python -m alembic history`
3. 联系数据库管理员

