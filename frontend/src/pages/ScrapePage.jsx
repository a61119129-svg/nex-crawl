import { useState, useCallback } from 'react'
import { Globe, Play, Copy, Check, Download } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { scrapeUrl } from '../api'

const FORMAT_OPTIONS = ['markdown', 'html', 'text', 'raw_html']

function saveHistory(entry) {
  try {
    const h = JSON.parse(localStorage.getItem('wv_history') || '[]')
    h.push(entry)
    if (h.length > 100) h.splice(0, h.length - 100)
    localStorage.setItem('wv_history', JSON.stringify(h))
  } catch {}
}

export default function ScrapePage() {
  const [url, setUrl] = useState('')
  const [format, setFormat] = useState('markdown')
  const [useBrowser, setUseBrowser] = useState(false)
  const [mainContent, setMainContent] = useState(true)
  const [waitFor, setWaitFor] = useState(0)
  const [stealth, setStealth] = useState(false)
  const [bypassCaptcha, setBypassCaptcha] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('content')
  const [copied, setCopied] = useState(false)

  const handleScrape = useCallback(async () => {
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await scrapeUrl({
        url: url.trim(),
        formats: [format],
        use_browser: useBrowser,
        only_main_content: mainContent,
        wait_for: waitFor,
        stealth,
        bypass_captcha: bypassCaptcha,
      })
      setResult(data)
      saveHistory({ type: 'scrape', url: url.trim(), time: Date.now(), error: null })
    } catch (e) {
      setError(e.message)
      saveHistory({ type: 'scrape', url: url.trim(), time: Date.now(), error: e.message })
    } finally {
      setLoading(false)
    }
  }, [url, format, useBrowser, mainContent, waitFor, stealth, bypassCaptcha])

  const content = result ? (result.markdown || result.html || result.text || result.raw_html || '') : ''

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const ext = format === 'markdown' ? 'md' : format === 'text' ? 'txt' : 'html'
    const blob = new Blob([content], { type: 'text/plain' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `scrape-${Date.now()}.${ext}`
    a.click()
  }

  return (
    <>
      <div className="page-header">
        <h1>Scrape</h1>
        <p>Fetch a single URL and get clean content</p>
      </div>

      <div className="card">
        <div className="card-header"><Globe size={16} /> Target URL</div>

        <div className="form-group">
          <label>URL</label>
          <input
            className="input"
            placeholder="https://example.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleScrape()}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Output Format</label>
            <select className="input" value={format} onChange={e => setFormat(e.target.value)}>
              {FORMAT_OPTIONS.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Wait After Load (ms)</label>
            <input className="input" type="number" min="0" step="500" value={waitFor} onChange={e => setWaitFor(Number(e.target.value))} />
          </div>
        </div>

        <div className="toggle-group">
          <label className="toggle-label">
            <input type="checkbox" checked={mainContent} onChange={e => setMainContent(e.target.checked)} />
            Main content only
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={useBrowser} onChange={e => setUseBrowser(e.target.checked)} />
            Use headless browser
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={stealth} onChange={e => setStealth(e.target.checked)} />
            Stealth mode
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={bypassCaptcha} onChange={e => setBypassCaptcha(e.target.checked)} />
            Bypass CAPTCHA
          </label>
        </div>

        <button className="btn btn-primary" disabled={loading || !url.trim()} onClick={handleScrape}>
          {loading ? <><span className="spinner" /> Scraping…</> : <><Play size={16} /> Scrape</>}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="tabs">
              <button className={`tab ${activeTab === 'content' ? 'active' : ''}`} onClick={() => setActiveTab('content')}>Content</button>
              <button className={`tab ${activeTab === 'metadata' ? 'active' : ''}`} onClick={() => setActiveTab('metadata')}>Metadata</button>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
                {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy</>}
              </button>
              <button className="btn btn-secondary btn-sm" onClick={handleDownload}>
                <Download size={14} /> Download
              </button>
            </div>
          </div>

          {activeTab === 'content' && (
            <div className="result-box">
              {format === 'markdown' ? (
                <div className="markdown-body"><ReactMarkdown>{content}</ReactMarkdown></div>
              ) : (
                <pre>{content}</pre>
              )}
            </div>
          )}

          {activeTab === 'metadata' && result.metadata && (
            <div className="meta-grid">
              {Object.entries(result.metadata).map(([k, v]) => (
                <div key={k} className="meta-item">
                  <div className="meta-key">{k}</div>
                  <div className="meta-value">{String(v)}</div>
                </div>
              ))}
              {result.status_code && (
                <div className="meta-item">
                  <div className="meta-key">Status Code</div>
                  <div className="meta-value">{result.status_code}</div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </>
  )
}
