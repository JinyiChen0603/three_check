/**
 * 数学题目三重质检工具 - 主应用
 */

import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// 主页面
import QualityCheckPage from './pages/QualityCheck';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <QualityCheckPage />
    </ConfigProvider>
  );
}

export default App;
