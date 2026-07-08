import { StrictMode, lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'

// Lazy load page components
const App = lazy(() => import('./App.jsx'))
const Introduction = lazy(() => import('./Introduction.jsx'))

// Loading spinner component
const Loading = () => (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-slate-400">Loading...</p>
    </div>
  </div>
)

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Suspense fallback={<Loading />}>
        <App />
      </Suspense>
    </BrowserRouter>
  </StrictMode>,
)
