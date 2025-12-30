// import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import './index.css'

createRoot(document.getElementById('root')!).render(
  // StrictMode 在开发模式下会导致组件挂载两次，暂时禁用
  // <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  // </StrictMode>,
)
