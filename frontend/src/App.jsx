import { Routes, Route, NavLink } from 'react-router-dom'
import { Globe, Bug, FileSearch, Layers, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'
import { healthCheck } from './api'
import ScrapePage from './pages/ScrapePage'
import CrawlPage from './pages/CrawlPage'
import ExtractPage from './pages/ExtractPage'
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
        <NavLink to="/scrape" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Globe size={18} /> Scrape
        </NavLink>
        <NavLink to="/crawl" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Bug size={18} /> Crawl
        </NavLink>
        <NavLink to="/extract" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <FileSearch size={18} /> Extract
        </NavLink>

        <div className="sidebar-footer">
          <span className={`status-dot ${apiStatus === 'online' ? 'online' : 'offline'}`} />
          API {apiStatus === 'online' ? 'Connected' : apiStatus === 'checking' ? 'Checking\u2026' : 'Offline'}
        </div>
      </aside>

      <main className="main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/scrape" element={<ScrapePage />} />
          <Route path="/crawl" element={<CrawlPage />} />
          <Route path="/extract" element={<ExtractPage />} />
        </Routes>
      </main>
    </>
  )
}
