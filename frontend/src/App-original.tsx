/**
 * 主应用组件
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './store/useAuthStore';

// 布局
import MainLayout from './layouts/MainLayout';

// 页面
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';
import Problem from './pages/Problem';
import Review from './pages/Review';
import Materials from './pages/Materials';
import Admin from './pages/Admin';

// 创建 React Query 客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// 路由守卫组件
function PrivateRoute({ children }: { children: JSX.Element }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <BrowserRouter>
          <Routes>
            {/* 登录页 */}
            <Route path="/login" element={<Login />} />

            {/* 需要认证的路由 */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <MainLayout />
                </PrivateRoute>
              }
            >
              {/* 默认重定向到仪表盘 */}
              <Route index element={<Navigate to="/dashboard" replace />} />
              
              {/* 仪表盘 */}
              <Route path="dashboard" element={<Dashboard />} />
              
              {/* 任务管理 */}
              <Route path="tasks" element={<Tasks />} />
              
              {/* 出题流程 */}
              <Route path="problem" element={<Problem />} />
              
              {/* 评分流程 */}
              <Route path="review" element={<Review />} />
              
              {/* 资料库 */}
              <Route path="materials" element={<Materials />} />
              
              {/* 管理员功能 */}
              <Route path="admin" element={<Admin />} />
            </Route>

            {/* 404 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
