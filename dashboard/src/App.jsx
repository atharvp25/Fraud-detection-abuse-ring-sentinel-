import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Shield, LayoutDashboard, Search, BarChart3, Zap, Activity } from 'lucide-react'
import Overview from './pages/Overview'
import RingExplorer from './pages/RingExplorer'
import RingDetail from './pages/RingDetail'
import ModelAnalysis from './pages/ModelAnalysis'
import LiveAnalysis from './pages/LiveAnalysis'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        {/* Sidebar */}
        <nav className="sidebar">
          <div className="sidebar-logo">
            <div className="logo-icon">
              <Shield size={22} color="white" />
            </div>
            <div>
              <h1>Abuse Ring Sentinel</h1>
              <p>Fraud Detection System</p>
            </div>
          </div>

          <ul className="nav-links">
            <li>
              <NavLink to="/" end className={({isActive}) => isActive ? 'active' : ''}>
                <LayoutDashboard size={18} /> Overview
              </NavLink>
            </li>
            <li>
              <NavLink to="/analyze" className={({isActive}) => isActive ? 'active' : ''}>
                <Activity size={18} /> Live Analysis
              </NavLink>
            </li>
            <li>
              <NavLink to="/rings" className={({isActive}) => isActive ? 'active' : ''}>
                <Search size={18} /> Ring Explorer
              </NavLink>
            </li>
            <li>
              <NavLink to="/models" className={({isActive}) => isActive ? 'active' : ''}>
                <BarChart3 size={18} /> Model Analysis
              </NavLink>
            </li>
          </ul>

          <div style={{marginTop: 'auto', padding: '16px', borderTop: '1px solid var(--border-color)'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <Zap size={14} color="var(--accent-green)" />
              <span style={{fontSize: '12px', color: 'var(--text-muted)'}}>Powered by Groq + XGBoost</span>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/analyze" element={<LiveAnalysis />} />
            <Route path="/rings" element={<RingExplorer />} />
            <Route path="/rings/:ringId" element={<RingDetail />} />
            <Route path="/models" element={<ModelAnalysis />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
