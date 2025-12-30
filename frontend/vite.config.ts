import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // 监听所有网络接口
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // 本地后端
        changeOrigin: true,
        timeout: 3600000,  // 1小时超时（毫秒）
        proxyTimeout: 3600000,  // 1小时超时（毫秒）
      },
    },
  },
})
