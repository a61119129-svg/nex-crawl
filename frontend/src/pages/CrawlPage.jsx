import { useState, useCallback } from 'react'
import { Bug, Play, ChevronRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { crawlUrl } from '../api'

function saveHistory(entry) {
  try {
    const h = JSON.parse(localStorage.getItem('wv_history') || '[]')
    h.push(entry)
    if (h.length > 100) h.splice(0, h.length - 100)
    localStorage.setItem('wv_history', JSON.stringify(h))
  } catch {}
}

export default function CrawlPage() {
  const [url, setUrl] = useState('')
  const [maxDepth, setMaxDepth] = useState(2)
  const [maxPages, setMaxPages] = useState(20)
  const [format, setFormat] = useState('markdown')
  const [useBrowser, setUseBrowser] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [selectedIdx, setSelectedIdx] = useState(null)

  const handleCrawl = useCallback(async () => {
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setSelectedIdx(null)
    try {
      const data = await crawlUrl({
        url: url.trim(),
        max_depth: maxDepth,
        max_pages: maxPages,
        formats: [format],
        use_browser: useBrowser,
      })
      setResult(data)
      saveHistory({ type: 'crawl', url: url.trim(), time: Date.now(), error: null })
    } catch (e) {
      setError(e.message)
      saveHistory({ type: 'crawl', url: url.trim(), time: Date.now(), error: e.message })
    } finally {
      setLoading(false)
    }
  }, [url, maxDepth, maxPages, format, useBrowser])

  const selectedPage = result && selectedIdx !== null ? result.pages[selectedIdx] : null

  return (
    <>
      <div className="page-header">
        <h1>Crawl</h1>
        <p>Crawl an entire website following links within the same domain</p>
      </div>

      <div className="card">
        <div className="card-header"><Bug size={16} /> Crawl Settings</div>

        <div className="form-group">
          <label>Starting URL</label>
          <input
            className="input"
            placeholder="https://example.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCrawl()}
          />
        </div>

        <div className="form-row-3">
          <div className="form-group">
            <label>Max Depth</label>
            <input className="input" type="number" min="0" max="10" value={maxDepth} onChange={e => setMaxDepth(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>Max Pages</label>
            <input className="input" type="number" min="1" max="10000" value={maxPages} onChange={e => setMaxPages(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label>Format</label>
            <select className="input" value={format} onChange={e => setFormat(e.target.value)}>
              <option value="markdown">markdown</option>
              <option value="html">html</option>
              <option value="text">text</option>
            </select>
          </div>
        </div>

        <div className="toggle-group">
          <label className="toggle-label">
            <input type="checkbox" checked={useBrowser} onChange={e => setUseBrowser(e.target.checked)} />
            Use headless browser
          </label>
        </div>

        <button className="btn btn-primary" disabled={loading || !url.trim()} onClick={handleCrawl}>
          {loading ? <><span className="spinner" /> Crawling…</> : <><Play size={16} /> Start Crawl</>}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="card">
          <div className="card-header" style={{ justifyContent: 'space-between' }}>
            <span>Results</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <span className="badge badge-info">{result.completed} pages</span>
              <span className="badge badge-success">{result.status}</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: selectedPage ? '1fr 1.5fr' : '1fr', gap: 16 }}>
            {/* Page list */}
            <div className="page-list" style={{ maxHeight: 500, overflow: 'auto' }}>
              {result.pages.map((page, i) => (
                <div
                  key={i}
                  className="page-list-item"
                  style={selectedIdx === i ? { borderColor: 'var(--accent)' } : {}}
                  onClick={() => setSelectedIdx(i)}
                >
                  <div style={{ minWidth: 0 }}>
                    <div className="page-title" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {page.metadata?.title || page.url}
                    </div>
                    <div className="page-url" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {page.url}
                    </div>
                  </div>
                  <ChevronRight size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                </div>
              ))}
            </div>

            {/* Selected page content */}
            {selectedPage && (
              <div className="result-box">
                {format === 'markdown' ? (
                  <div className="markdown-body">
                    <ReactMarkdown>{selectedPage.markdown || selectedPage.html || selectedPage.text || ''}</ReactMarkdown>
                  </div>
                ) : (
                  <pre>{selectedPage[format] || ''}</pre>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
