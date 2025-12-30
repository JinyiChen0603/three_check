# 数据库迁移指南

## 📋 本次修改内容

将 `ValidationRecord` 从关联 `problems` 表改为关联 `validated_problem_exports` 表。

### 主要变更
- ✅ `validation_records.problem_id` → `validation_records.validated_problem_id`
- ✅ 外键从 `problems(id)` 改为 `validated_problem_exports(id)` (CASCADE 删除)
- ✅ `validated_problem_id` 允许为 NULL（用于内容质检）
- ✅ 索引从 `idx_problem_type` 改为 `idx_validated_problem_type`

## 🚀 快速迁移

### 方法1：使用自动同步脚本（推荐）

```bash
# 1. 进入容器
docker-compose exec mathtasks-api bash

# 2. 检查数据库差异
python scripts/sync_database_schema.py --check

# 3. 执行同步（会提示确认）
python scripts/sync_database_schema.py --sync
```

### 方法2：如果是全新数据库

```bash
# 直接重建所有表
docker-compose exec mathtasks-api bash
python -c "
from app.database import Base, engine
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"
```

## 📊 迁移步骤说明

`sync_database_schema.py` 脚本会自动执行以下步骤：

1. ✅ **添加新列**：`validation_records.validated_problem_id`
2. ✅ **修改旧列**：`validation_records.problem_id` 改为可空（保留数据）
3. ✅ **添加外键**：`validated_problem_id` → `validated_problem_exports(id)` ON DELETE CASCADE
4. ✅ **删除旧索引**：`idx_problem_type`
5. ✅ **创建新索引**：`idx_validated_problem_type (validated_problem_id, validation_type)`
6. ✅ **添加缺失列**：`validated_problem_exports` 表的 `review_count` 等字段

## 🔍 验证迁移

迁移完成后，检查表结构：

```bash
docker-compose exec mathtasks-api bash
psql $DATABASE_URL -c "\d validation_records"
```

应该看到：
```
Column                | Type    | Nullable
----------------------+---------+----------
id                    | integer | not null
problem_id            | integer | yes       (旧字段，可空)
validated_problem_id  | integer | yes       (新字段)
validation_type       | varchar | not null
...
```

## 🎯 代码修改总结

### 已完成的代码修改
- ✅ `app/models.py`: ValidationRecord 模型更新
- ✅ `app/models.py`: ValidatedProblemExport 添加 validation_records 关系
- ✅ `app/api/problems.py`: 内容质检 API 使用 validated_problem_id
- ✅ `app/api/problems.py`: 导出 API 创建 ValidatedProblemExport 时同时创建 ValidationRecord

### 数据流程
**新流程（已实施）：**
```
用户提交题目 → 质量检测 → ValidatedProblemExport
                                      ↓
                              创建 ValidationRecord
                              (validated_problem_id = export.id)
```

**内容质检流程：**
```
用户测试内容 → 质量检测 → ValidationRecord
                         (validated_problem_id = NULL)
```

## ⚠️ 注意事项

1. **级联删除**：删除 `ValidatedProblemExport` 会自动删除关联的 `ValidationRecord`
2. **NULL 值**：`validated_problem_id` 允许为 NULL（用于内容质检场景）
3. **旧数据保留**：`problem_id` 字段保留但改为可空，现有数据不会丢失
4. **OPENAI_API_KEY**：严谨性检测需要 OpenAI API，请确保在 `.env` 中配置

## 🐛 常见问题

### Q: 迁移失败怎么办？
A: 检查错误信息，通常是外键冲突或表不存在。可以先运行 `--check` 查看差异。

### Q: 如何回滚？
A: 脚本不会删除数据，只是添加新列。如果需要回滚，可以手动删除 `validated_problem_id` 列。

### Q: 旧的 problem_id 列可以删除吗？
A: 可以，但建议先运行一段时间确保没问题后再删除。

## 📝 相关文件

- `scripts/sync_database_schema.py` - 自动同步脚本
- `app/models.py` - 数据模型定义
- `app/api/problems.py` - API 实现

