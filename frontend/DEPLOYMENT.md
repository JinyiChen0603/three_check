# MathTasks 前端部署指南

## 🚀 推送到 GitHub

### 1. 创建 GitHub 仓库

在 GitHub 上创建一个新仓库，例如：`mathtasks-frontend`

### 2. 关联远程仓库

```bash
cd ~/Desktop/mathtasks-frontend
git remote add origin https://github.com/YOUR_USERNAME/mathtasks-frontend.git
```

### 3. 推送代码

```bash
# 推送主分支
git push -u origin master

# 如果需要创建 dev 分支
git checkout -b dev
git push -u origin dev
```

---

## 🌐 本地开发环境

### 前端服务
```bash
cd ~/Desktop/mathtasks-frontend
npm run dev
```
访问: http://localhost:3000

### 后端服务
```bash
cd ~/Desktop/出题平台
docker compose up -d
```
访问: http://localhost:8001

---

## 📦 生产环境构建

### 1. 构建静态文件

```bash
cd ~/Desktop/mathtasks-frontend
npm run build
```

构建结果在 `dist/` 目录

### 2. 预览生产构建

```bash
npm run preview
```

---

## 🖥️ 服务器部署

### 方案1: 使用 Nginx

```bash
# 1. 构建项目
npm run build

# 2. 复制 dist 目录到服务器
scp -r dist/ user@your-server:/var/www/mathtasks

# 3. Nginx 配置示例
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/mathtasks;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 代理后端API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 方案2: 使用 Docker

创建 `Dockerfile`:

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

构建和运行:

```bash
docker build -t mathtasks-frontend .
docker run -d -p 80:80 mathtasks-frontend
```

### 方案3: 使用 Vercel/Netlify（推荐）

**Vercel 部署**:
```bash
npm install -g vercel
vercel
```

**Netlify 部署**:
```bash
npm install -g netlify-cli
netlify deploy --prod
```

---

## ⚙️ 环境变量配置

创建 `.env.production`:

```env
# API地址（生产环境）
VITE_API_BASE_URL=https://api.your-domain.com

# 其他配置
VITE_APP_NAME=MathTasks
VITE_APP_VERSION=1.0.0
```

更新 `src/api/axios.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api';
```

---

## 🔒 安全建议

1. **使用 HTTPS**
   - 生产环境必须使用 HTTPS
   - 可以使用 Let's Encrypt 免费证书

2. **API 安全**
   - 配置 CORS 白名单
   - 使用环境变量管理敏感信息

3. **静态资源优化**
   - 启用 Gzip/Brotli 压缩
   - 配置缓存策略

---

## 📊 性能优化

### Vite 配置优化

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'antd-vendor': ['antd'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
});
```

### 代码分割

```typescript
// 懒加载路由组件
const Dashboard = lazy(() => import('./pages/Dashboard/Simple'));
```

---

## 🧪 部署检查清单

部署前请确认：

- [ ] 所有功能测试通过
- [ ] 生产环境构建成功
- [ ] 环境变量配置正确
- [ ] API 地址配置正确
- [ ] CORS 配置正确
- [ ] 静态资源路径正确
- [ ] 错误处理完善
- [ ] 日志配置完成
- [ ] 性能测试通过
- [ ] 安全审查通过

---

## 🐛 常见问题

### 1. 404 错误

**问题**: 刷新页面出现 404

**解决**: 配置服务器将所有路由指向 index.html

Nginx:
```nginx
try_files $uri $uri/ /index.html;
```

### 2. API 跨域错误

**问题**: CORS 错误

**解决**: 后端配置 CORS 允许前端域名

### 3. 静态资源 404

**问题**: CSS/JS 文件 404

**解决**: 检查 `vite.config.ts` 的 `base` 配置

---

## 📞 技术支持

部署遇到问题？联系技术团队。

---

最后更新: 2025-12-17

