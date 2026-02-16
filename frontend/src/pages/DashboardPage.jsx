import { useState } from 'react'
import { Globe, Layers, Bug, FileSearch } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function DashboardPage() {
  const navigate = useNavigate()
  const [history] = useState(() => {
    try { return JSON.parse(localStorage.getItem('wv_history') || '[]') } catch { return [] }
  })

  return (
    <>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Overview of your scraping workspace</p>
      </div>

      <div className="stats-row">
        <div className="stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/scrape')}>
          <div className="stat-icon purple"><Globe size={22} /></div>
          <div>
            <div className="stat-value">{history.filter(h => h.type === 'scrape').length}</div>
            <div className="stat-label">Pages Scraped</div>
          </div>
        </div>
        <div className="stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/crawl')}>
          <div className="stat-icon green"><Bug size={22} /></div>
          <div>
            <div className="stat-value">{history.filter(h => h.type === 'crawl').length}</div>
            <div className="stat-label">Crawl Jobs</div>
          </div>
        </div>
        <div className="stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/extract')}>
          <div className="stat-icon amber"><FileSearch size={22} /></div>
          <div>
            <div className="stat-value">{history.filter(h => h.type === 'extract').length}</div>
            <div className="stat-label">Extractions</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><Layers size={16} /> Quick Actions</div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-primary" onClick={() => navigate('/scrape')}>
            <Globe size={16} /> Scrape a URL
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/crawl')}>
            <Bug size={16} /> Start Crawl
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/extract')}>
            <FileSearch size={16} /> Extract Data
          </button>
        </div>
      </div>

      {history.length > 0 && (
        <div className="card">
          <div className="card-header">Recent Activity</div>
          <div className="page-list">
            {history.slice(-10).reverse().map((item, i) => (
              <div key={i} className="page-list-item" onClick={() => navigate(`/${item.type}`)}>
                <div>
                  <div className="page-title">{item.url}</div>
                  <div className="page-url">{item.type} &middot; {new Date(item.time).toLocaleString()}</div>
                </div>
                <span className={`page-status ${item.error ? 'error' : ''}`}>
                  {item.error ? 'Failed' : 'Success'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {history.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
          <Globe size={40} style={{ marginBottom: 12, opacity: 0.3 }} />
          <p>No activity yet. Start by scraping a URL!</p>
        </div>
      )}
    </>
  )
}
