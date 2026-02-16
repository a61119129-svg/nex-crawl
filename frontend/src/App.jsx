import { Routes, Route, NavLink } from 'react-router-dom'
import { Globe, Bug, FileSearch, Layers, Zap, Table, Brain, Radar } from 'lucide-react'
import { useEffect, useState } from 'react'
import { healthCheck } from './api'
import ScrapePage from './pages/ScrapePage'
import CrawlPage from './pages/CrawlPage'
import ExtractPage from './pages/ExtractPage'
import FormatPage from './pages/FormatPage'
import AnalyzePage from './pages/AnalyzePage'
import ScanPage from './pages/ScanPage'
import DashboardPage from './pages/DashboardPage'

export default function App() {
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    healthCheck()
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'))

    const interval = setInterval(() => {
      healthCheck()
        .then(() => setApiStatus('online'))
        .catch(() => setApiStatus('offline'))
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <>
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Zap size={22} />
          <span>NexCrawl</span>
        </div>

        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Layers size={18} /> Dashboard
        </NavLink>
        <NavLink to="/scan" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Radar size={18} /> Deep Scan
        </NavLink>
        <NavLink to="/scrape" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Globe size={18} /> Scrape
        </NavLink>
        <NavLink to="/crawl" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Bug size={18} /> Crawl
        </NavLink>
        <NavLink to="/extract" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <FileSearch size={18} /> Extract
        </NavLink>
        <NavLink to="/format" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Table size={18} /> Format
        </NavLink>
        <NavLink to="/analyze" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Brain size={18} /> AI Analyze
        </NavLink>

        <div className="sidebar-footer">
          <span className={`status-dot ${apiStatus === 'online' ? 'online' : 'offline'}`} />
          API {apiStatus === 'online' ? 'Connected' : apiStatus === 'checking' ? 'Checking\u2026' : 'Offline'}
        </div>
      </aside>

      <main className="main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/scan" element={<ScanPage />} />
          <Route path="/scrape" element={<ScrapePage />} />
          <Route path="/crawl" element={<CrawlPage />} />
          <Route path="/extract" element={<ExtractPage />} />
          <Route path="/format" element={<FormatPage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
        </Routes>
      </main>
    </>
  )
}
