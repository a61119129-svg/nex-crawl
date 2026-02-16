import { useState, useCallback } from 'react'
import { Table, Play, Copy, Check, Download } from 'lucide-react'
import { formatData } from '../api'

export default function FormatPage() {
  const [url, setUrl] = useState('')
  const [useBrowser, setUseBrowser] = useState(false)
  const [mainContent, setMainContent] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('tables')
  const [copied, setCopied] = useState(false)

  const handleFormat = useCallback(async () => {
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await formatData({
        url: url.trim(),
        use_browser: useBrowser,
        only_main_content: mainContent,
      })
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [url, useBrowser, mainContent])

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownloadCSV = () => {
    if (!result?.tables_csv) return
    const blob = new Blob([result.tables_csv], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `tables-${Date.now()}.csv`
    a.click()
  }

  return (
    <>
      <div className="page-header">
        <h1>Format & Structure</h1>
        <p>Extract tables, lists, and structured data from any page</p>
      </div>

      <div className="card">
        <div className="card-header"><Table size={16} /> Target URL</div>

        <div className="form-group">
          <label>URL</label>
          <input
            className="input"
            placeholder="https://en.wikipedia.org/wiki/Web_scraping"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleFormat()}
          />
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
        </div>

        <button className="btn btn-primary" disabled={loading || !url.trim()} onClick={handleFormat}>
          {loading ? <><span className="spinner" /> Extracting…</> : <><Play size={16} /> Extract Structure</>}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <>
          {/* Summary stats */}
          <div className="stats-row">
            <div className="stat-card">
              <div className="stat-icon purple"><Table size={22} /></div>
              <div>
                <div className="stat-value">{result.summary?.tables_found || 0}</div>
                <div className="stat-label">Tables ({result.summary?.total_rows || 0} rows)</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon green"><span style={{fontSize: 20}}>☰</span></div>
              <div>
                <div className="stat-value">{result.summary?.lists_found || 0}</div>
                <div className="stat-label">Lists ({result.summary?.total_list_items || 0} items)</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon amber"><span style={{fontSize: 20}}>🔑</span></div>
              <div>
                <div className="stat-value">{result.summary?.key_value_pairs_found || 0}</div>
                <div className="stat-label">Key-Value Pairs</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon purple"><span style={{fontSize: 20}}>#</span></div>
              <div>
                <div className="stat-value">{result.summary?.headings_found || 0}</div>
                <div className="stat-label">Headings</div>
              </div>
            </div>
          </div>

          {/* Tab navigation */}
          <div className="card">
            <div className="tab-bar">
              {['tables', 'lists', 'key-values', 'outline', 'csv'].map(tab => (
                <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            <div className="result-box" style={{ minHeight: 200 }}>
              {/* Tables tab */}
              {activeTab === 'tables' && (
                result.tables?.length > 0 ? (
                  result.tables.map((table, i) => (
                    <div key={i} style={{ marginBottom: 24 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 8 }}>{table.caption}</h3>
                      <div style={{ overflowX: 'auto' }}>
                        <table className="data-table">
                          <thead>
                            <tr>
                              {table.headers?.map((h, j) => <th key={j}>{h}</th>)}
                            </tr>
                          </thead>
                          <tbody>
                            {table.rows?.map((row, j) => (
                              <tr key={j}>
                                {row.map((cell, k) => <td key={k}>{cell}</td>)}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div style={{ color: 'var(--text-dim)', fontSize: 12, marginTop: 4 }}>
                        {table.row_count} rows × {table.col_count} columns
                      </div>
                    </div>
                  ))
                ) : <p style={{ color: 'var(--text-dim)' }}>No tables found on this page.</p>
              )}

              {/* Lists tab */}
              {activeTab === 'lists' && (
                result.lists?.length > 0 ? (
                  result.lists.map((list, i) => (
                    <div key={i} style={{ marginBottom: 16 }}>
                      <h4 style={{ color: 'var(--text)', marginBottom: 4 }}>
                        {list.type === 'ol' ? 'Ordered' : 'Unordered'} List ({list.count} items)
                      </h4>
                      {list.type === 'ol' ? (
                        <ol style={{ paddingLeft: 20, color: 'var(--text-dim)' }}>
                          {list.items.map((item, j) => <li key={j} style={{ marginBottom: 2 }}>{item}</li>)}
                        </ol>
                      ) : (
                        <ul style={{ paddingLeft: 20, color: 'var(--text-dim)' }}>
                          {list.items.map((item, j) => <li key={j} style={{ marginBottom: 2 }}>{item}</li>)}
                        </ul>
                      )}
                    </div>
                  ))
                ) : <p style={{ color: 'var(--text-dim)' }}>No lists found on this page.</p>
              )}

              {/* Key-values tab */}
              {activeTab === 'key-values' && (
                result.key_value_pairs?.length > 0 ? (
                  <table className="data-table">
                    <thead><tr><th>Key</th><th>Value</th></tr></thead>
                    <tbody>
                      {result.key_value_pairs.map((kv, i) => (
                        <tr key={i}><td><strong>{kv.key}</strong></td><td>{kv.value}</td></tr>
                      ))}
                    </tbody>
                  </table>
                ) : <p style={{ color: 'var(--text-dim)' }}>No key-value pairs detected.</p>
              )}

              {/* Outline tab */}
              {activeTab === 'outline' && (
                result.headings?.length > 0 ? (
                  <div style={{ fontFamily: 'monospace' }}>
                    {result.headings.map((h, i) => (
                      <div key={i} style={{ paddingLeft: (h.level - 1) * 20, color: h.level <= 2 ? 'var(--text)' : 'var(--text-dim)', marginBottom: 4 }}>
                        <span style={{ color: 'var(--primary)', marginRight: 8 }}>{'#'.repeat(h.level)}</span>
                        {h.text}
                      </div>
                    ))}
                  </div>
                ) : <p style={{ color: 'var(--text-dim)' }}>No headings found.</p>
              )}

              {/* CSV tab */}
              {activeTab === 'csv' && (
                result.tables_csv ? (
                  <>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                      <button className="btn btn-secondary" onClick={() => handleCopy(result.tables_csv)}>
                        {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy CSV</>}
                      </button>
                      <button className="btn btn-secondary" onClick={handleDownloadCSV}>
                        <Download size={14} /> Download CSV
                      </button>
                    </div>
                    <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13 }}>
                      {result.tables_csv}
                    </pre>
                  </>
                ) : <p style={{ color: 'var(--text-dim)' }}>No table data to export as CSV.</p>
              )}
            </div>
          </div>
        </>
      )}
    </>
  )
}
