/**
 * 主应用组件
 * 约定：路由统一指向各页面的 `index.tsx`（单一入口），避免 Simple/完整版并存导致的混乱。
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
import Materials from './pages/Materials';
import Admin from './pages/Admin';
import ProblemReview from './pages/Admin/ProblemReview';
import Tasks from './pages/Tasks';  // 使用完整版任务管理页面
import TotalPage from './pages/totalpage';
import VariantGenerator from './pages/VariantGenerator';  // 变体生成器
import Review from './pages/Review';  // ✅ 恢复评分流程
import ReviewHistory from './pages/ReviewHistory';  // ✅ 恢复我的评分记录
// 以下页面仍保持隐藏
// import Problem from './pages/Problem';
// import MyVariants from './pages/MyVariants';

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
function PrivateRoute({ children }: { children: React.ReactElement }) {
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
              <Route 
                path="tasks" 
                element={<Tasks />} 
              />
              {/* 评分相关页面 - 已恢复 */}
              <Route 
                path="review" 
                element={<Review />} 
              />
              <Route 
                path="review-history" 
                element={<ReviewHistory />} 
              />
              {/* 以下页面仍保持隐藏 */}
              {/* <Route 
                path="problem" 
                element={<Problem />} 
              /> */}
              {/* <Route 
                path="my-variants" 
                element={<MyVariants />} 
              /> */}
              <Route 
                path="materials" 
                element={<Materials />} 
              />
              <Route 
                path="admin" 
                element={<Admin />} 
              />
              <Route 
                path="admin/problem-review" 
                element={<ProblemReview />} 
              />
              <Route 
                path="totalpage" 
                element={<TotalPage />} 
              />
              <Route 
                path="variant-generator" 
                element={<VariantGenerator />} 
              />
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
