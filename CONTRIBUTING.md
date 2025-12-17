# 贡献指南

感谢您考虑为 MathTasks 项目做出贡献！🎉

## 📋 目录

- [开发环境设置](#开发环境设置)
- [提交代码流程](#提交代码流程)
- [代码规范](#代码规范)
- [提交消息规范](#提交消息规范)
- [分支管理](#分支管理)

---

## 🛠️ 开发环境设置

### 后端开发

1. **克隆仓库**
```bash
git clone https://github.com/YOUR_USERNAME/mathtasks.git
cd mathtasks/backend
```

2. **设置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的 API Keys
```

3. **启动开发环境**
```bash
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/init_users.py
```

### 前端开发

1. **进入前端目录**
```bash
cd frontend
```

2. **安装依赖**
```bash
npm install
```

3. **启动开发服务器**
```bash
npm run dev
```

---

## 🔄 提交代码流程

1. **创建新分支**
```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

2. **进行开发**
   - 编写代码
   - 编写测试（如果适用）
   - 确保代码符合规范

3. **提交更改**
```bash
git add .
git commit -m "feat: 添加新功能描述"
```

4. **推送到远程**
```bash
git push origin feature/your-feature-name
```

5. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 填写详细的描述
   - 等待代码审查

---

## 📏 代码规范

### Python (后端)

- 遵循 PEP 8 规范
- 使用类型提示
- 编写文档字符串（docstrings）

**示例**:
```python
async def get_user_by_username(
    db: AsyncSession,
    username: str
) -> Optional[User]:
    """
    根据用户名获取用户
    
    Args:
        db: 数据库会话
        username: 用户名
        
    Returns:
        用户对象，如果不存在则返回 None
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()
```

### TypeScript (前端)

- 使用 TypeScript 严格模式
- 使用函数式组件 + Hooks
- 合理拆分组件

**示例**:
```typescript
interface UserProps {
  username: string;
  role: UserRole;
}

export const UserCard: React.FC<UserProps> = ({ username, role }) => {
  return (
    <Card>
      <div>用户名: {username}</div>
      <div>角色: {role}</div>
    </Card>
  );
};
```

---

## 💬 提交消息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 类型 (Type)

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（既不是新功能也不是 bug 修复）
- `perf`: 性能优化
- `test`: 添加测试
- `chore`: 构建过程或辅助工具的变动

### 示例

```bash
# 新功能
git commit -m "feat: 添加用户评分历史查询接口"

# Bug 修复
git commit -m "fix: 修复任务超时未自动释放的问题"

# 文档
git commit -m "docs: 更新 API 文档"

# 重构
git commit -m "refactor: 优化题目验证服务代码结构"
```

---

## 🌳 分支管理

### 主要分支

- `main`: 生产环境代码，始终保持可部署状态
- `dev`: 开发分支，用于集成测试

### 特性分支

从 `dev` 分支创建：

```bash
# 新功能
git checkout -b feature/user-profile

# Bug 修复
git checkout -b fix/login-error

# 优化
git checkout -b perf/database-query
```

### 合并流程

```
feature/xxx -> dev -> main
```

---

## ✅ Pull Request 检查清单

提交 PR 前请确认：

- [ ] 代码符合项目规范
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交消息清晰明了
- [ ] 没有不必要的文件（检查 .gitignore）
- [ ] 移除了所有 debug 代码和 console.log

---

## 🐛 报告 Bug

发现 Bug？请创建 Issue 并包含：

1. **问题描述**: 清晰描述问题
2. **复现步骤**: 如何触发这个 bug
3. **期望行为**: 应该发生什么
4. **实际行为**: 实际发生了什么
5. **环境信息**: 操作系统、浏览器版本等
6. **截图**: 如果适用

---

## 💡 功能建议

有新想法？欢迎创建 Feature Request Issue：

1. **功能描述**: 详细描述建议的功能
2. **使用场景**: 为什么需要这个功能
3. **可选方案**: 是否有替代方案
4. **愿意贡献**: 是否愿意自己实现

---

## 📞 获取帮助

- 查看 [README.md](./README.md)
- 查看 [API 文档](http://localhost:8001/docs)
- 提交 Issue
- 联系团队成员

---

感谢您的贡献！🙏

