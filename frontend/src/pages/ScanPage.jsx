import { useState, useCallback } from 'react'
import {
  Radar, Play, Copy, Check, Sparkles, Target, Tag,
  Clock, Globe, Table2, List, KeyRound, Brain, ChevronDown, ChevronUp
} from 'lucide-react'
import { deepScan } from '../api'

const SITE_ICONS = {
  yelp: '🍽️', directory: '📒', ecommerce: '🛒', news: '📰',
  realestate: '🏠', recipe: '🧑‍🍳', blog: '✍️', amazon: '📦',
  ebay: '🏷️', shopify: '🛍️', tripadvisor: '✈️', yellowpages: '📞',
  indeed: '💼', linkedin: '💼', google_maps: '📍', generic: '🌐',
}

export default function ScanPage() {
  const [url, setUrl] = useState('')
  const [instruction, setInstruction] = useState('')
  const [useBrowser, setUseBrowser] = useState(false)
  const [mainContent, setMainContent] = useState(true)
  const [includeAi, setIncludeAi] = useState(true)
  const [stealth, setStealth] = useState(false)
  const [bypassCaptcha, setBypassCaptcha] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [copied, setCopied] = useState(false)
  const [expandedSections, setExpandedSections] = useState({})

  const toggleSection = (key) => setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }))

  const handleScan = useCallback(async () => {
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setActiveTab('overview')
    try {
      const payload = {
        url: url.trim(),
        use_browser: useBrowser,
        only_main_content: mainContent,
        include_ai: includeAi,
        stealth,
        bypass_captcha: bypassCaptcha,
      }
      if (instruction.trim()) payload.instruction = instruction.trim()
      const data = await deepScan(payload)
      if (data.error && !data.success) throw new Error(data.error)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [url, instruction, useBrowser, mainContent, includeAi, stealth, bypassCaptcha])

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const summary = result?.scan_summary || {}
  const scrape = result?.scrape || {}
  const detection = result?.site_detection || {}
  const smart = result?.smart_extraction || {}
  const structured = result?.structured_data || {}
  const ai = result?.ai_analysis || {}
  const timing = result?.timing || {}

  const sentimentColor = {
    positive: '#22c55e', negative: '#ef4444',
    neutral: '#94a3b8', mixed: '#f59e0b',
  }

  return (
    <>
      <div className="page-header">
        <h1>Deep Scan</h1>
        <p>One URL — full pipeline: scrape, detect, extract, format, AI analyze</p>
      </div>

      {/* Input card */}
      <div className="card">
        <div className="card-header"><Radar size={16} /> Scan URL</div>

        <div className="form-group">
          <label>URL</label>
          <input
            className="input"
            placeholder="https://www.yelp.com/biz/some-restaurant or any URL..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleScan()}
          />
        </div>

        <div className="form-group">
          <label>Custom AI Instruction <span style={{ color: 'var(--text-dim)', fontWeight: 400 }}>(optional)</span></label>
          <textarea
            className="input"
            placeholder="e.g. Compare pricing tiers, extract all contact info, summarize reviews..."
            value={instruction}
            onChange={e => setInstruction(e.target.value)}
            rows={2}
            style={{ resize: 'vertical', fontFamily: 'inherit' }}
          />
        </div>

        <div className="toggle-group">
          <label className="toggle-label">
            <input type="checkbox" checked={mainContent} onChange={e => setMainContent(e.target.checked)} />
            Main content only
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={useBrowser} onChange={e => setUseBrowser(e.target.checked)} />
            Headless browser
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={includeAi} onChange={e => setIncludeAi(e.target.checked)} />
            Include AI analysis
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

        <button className="btn btn-primary" disabled={loading || !url.trim()} onClick={handleScan}>
          {loading
            ? <><span className="spinner" /> Running deep scan…</>
            : <><Radar size={16} /> Deep Scan</>
          }
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && result.success && (
        <>
          {/* Summary banner */}
          <div className="card" style={{ borderLeft: '3px solid var(--primary)' }}>
            <div className="card-header"><Globe size={16} /> Scan Summary</div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 12 }}>
              <span className="badge" style={{ fontSize: 14 }}>
                {SITE_ICONS[detection.type] || '🌐'} {detection.type?.replace('_', ' ')}
              </span>
              <span className="badge" style={{
                background: detection.confidence === 'high' ? '#22c55e22' : detection.confidence === 'medium' ? '#f59e0b22' : '#94a3b822',
                color: detection.confidence === 'high' ? '#22c55e' : detection.confidence === 'medium' ? '#f59e0b' : '#94a3b8',
              }}>
                {detection.confidence} confidence
              </span>
              {scrape.metadata?.title && (
                <span style={{ color: 'var(--text)', fontSize: 14, fontWeight: 500 }}>
                  {scrape.metadata.title}
                </span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 12 }}>
              {[
                { label: 'Words', value: summary.word_count, icon: '📝' },
                { label: 'Tables', value: summary.tables_found, icon: '📊' },
                { label: 'Lists', value: summary.lists_found, icon: '📋' },
                { label: 'Fields', value: summary.fields_extracted, icon: '🔑' },
                { label: 'AI Ready', value: summary.ai_available ? 'Yes' : 'No', icon: '🤖' },
                { label: 'Time', value: `${summary.total_time}s`, icon: '⏱️' },
              ].map(s => (
                <div key={s.label} style={{ background: 'var(--bg)', padding: '10px 14px', borderRadius: 8, textAlign: 'center' }}>
                  <div style={{ fontSize: 20 }}>{s.icon}</div>
                  <div style={{ color: 'var(--text)', fontWeight: 600, fontSize: 18 }}>{s.value}</div>
                  <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Timing breakdown */}
            <div style={{ marginTop: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {Object.entries(timing).filter(([k]) => k !== 'total').map(([step, t]) => (
                <span key={step} className="badge" style={{ fontSize: 11 }}>
                  <Clock size={10} style={{ marginRight: 4 }} />
                  {step}: {t}s
                </span>
              ))}
            </div>
          </div>

          {/* Tabs */}
          <div className="card">
            <div className="tab-bar">
              {['overview', 'extracted', 'tables', 'ai', 'content', 'json'].map(tab => (
                <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
                  {tab === 'ai' ? 'AI Insights' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            <div className="result-box" style={{ minHeight: 300 }}>

              {/* ===== Overview ===== */}
              {activeTab === 'overview' && (
                <div>
                  {/* Smart-extracted fields */}
                  {Object.keys(smart.extracted_fields || {}).length > 0 && (
                    <div style={{ marginBottom: 24 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <KeyRound size={16} /> Smart-Extracted Fields
                        <span className="badge" style={{ fontSize: 11 }}>{detection.type}</span>
                      </h3>
                      <table className="data-table">
                        <thead><tr><th>Field</th><th>Value</th></tr></thead>
                        <tbody>
                          {Object.entries(smart.extracted_fields).map(([k, v]) => (
                            <tr key={k}>
                              <td><strong>{k.replace(/_/g, ' ')}</strong></td>
                              <td>{Array.isArray(v) ? v.join(', ') : String(v)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* AI Summary */}
                  {ai.summary && (
                    <div style={{ marginBottom: 20 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Sparkles size={16} /> AI Summary
                      </h3>
                      <p style={{ color: 'var(--text-dim)', lineHeight: 1.7 }}>{ai.summary}</p>
                      <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                        {ai.content_type && <span className="badge">{ai.content_type}</span>}
                        {ai.sentiment && (
                          <span className="badge" style={{
                            background: (sentimentColor[ai.sentiment] || '#94a3b8') + '22',
                            color: sentimentColor[ai.sentiment] || '#94a3b8'
                          }}>
                            {ai.sentiment}
                          </span>
                        )}
                        {ai.quality_score !== undefined && (
                          <span className="badge" style={{
                            background: ai.quality_score >= 7 ? '#22c55e22' : ai.quality_score >= 4 ? '#f59e0b22' : '#ef444422',
                            color: ai.quality_score >= 7 ? '#22c55e' : ai.quality_score >= 4 ? '#f59e0b' : '#ef4444'
                          }}>
                            Quality: {ai.quality_score}/10
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Structured data summary */}
                  {structured.summary && (
                    <div style={{ background: 'var(--bg)', padding: 16, borderRadius: 8 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 8 }}>📊 Data Found</h3>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 8 }}>
                        <div style={{ color: 'var(--text-dim)' }}>Tables: <strong style={{ color: 'var(--text)' }}>{structured.summary.tables_found}</strong> ({structured.summary.total_rows} rows)</div>
                        <div style={{ color: 'var(--text-dim)' }}>Lists: <strong style={{ color: 'var(--text)' }}>{structured.summary.lists_found}</strong> ({structured.summary.total_list_items} items)</div>
                        <div style={{ color: 'var(--text-dim)' }}>Key-Value Pairs: <strong style={{ color: 'var(--text)' }}>{structured.summary.key_value_pairs_found}</strong></div>
                        <div style={{ color: 'var(--text-dim)' }}>Headings: <strong style={{ color: 'var(--text)' }}>{structured.summary.headings_found}</strong></div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ===== Extracted (smart + lists) ===== */}
              {activeTab === 'extracted' && (
                <div>
                  {Object.keys(smart.extracted_fields || {}).length > 0 ? (
                    <div style={{ marginBottom: 24 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 10 }}>
                        <KeyRound size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                        Fields ({detection.type})
                      </h3>
                      <table className="data-table">
                        <thead><tr><th>Field</th><th>Value</th></tr></thead>
                        <tbody>
                          {Object.entries(smart.extracted_fields).map(([k, v]) => (
                            <tr key={k}>
                              <td><strong>{k.replace(/_/g, ' ')}</strong></td>
                              <td style={{ maxWidth: 400, wordBreak: 'break-word' }}>{Array.isArray(v) ? v.join(', ') : String(v)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p style={{ color: 'var(--text-dim)', marginBottom: 16 }}>No site-specific fields extracted.</p>
                  )}

                  {/* Smart-extracted lists (reviews, listings, etc.) */}
                  {Object.entries(smart.extracted_lists || {}).map(([listName, items]) => (
                    items.length > 0 && (
                      <div key={listName} style={{ marginBottom: 24 }}>
                        <h3 style={{ color: 'var(--text)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                          <List size={16} /> {listName.charAt(0).toUpperCase() + listName.slice(1)} ({items.length})
                        </h3>
                        {items.slice(0, 10).map((item, idx) => (
                          <div key={idx} style={{ background: 'var(--bg)', padding: 12, borderRadius: 8, marginBottom: 8 }}>
                            {Object.entries(item).map(([k, v]) => (
                              <div key={k} style={{ marginBottom: 4 }}>
                                <span style={{ color: 'var(--text-dim)', fontSize: 12, textTransform: 'uppercase' }}>{k}: </span>
                                <span style={{ color: 'var(--text)' }}>{v}</span>
                              </div>
                            ))}
                          </div>
                        ))}
                        {items.length > 10 && (
                          <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>...and {items.length - 10} more</p>
                        )}
                      </div>
                    )
                  ))}

                  {/* Key-value pairs from formatter */}
                  {structured.key_value_pairs?.length > 0 && (
                    <div>
                      <h3 style={{ color: 'var(--text)', marginBottom: 10 }}>
                        Detected Key-Value Pairs
                      </h3>
                      <table className="data-table">
                        <thead><tr><th>Key</th><th>Value</th></tr></thead>
                        <tbody>
                          {structured.key_value_pairs.map((pair, i) => (
                            <tr key={i}><td><strong>{pair.key}</strong></td><td>{pair.value}</td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* ===== Tables ===== */}
              {activeTab === 'tables' && (
                <div>
                  {structured.tables?.length > 0 ? (
                    structured.tables.map((table, idx) => (
                      <div key={idx} style={{ marginBottom: 24 }}>
                        <div
                          onClick={() => toggleSection(`table-${idx}`)}
                          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}
                        >
                          {expandedSections[`table-${idx}`] !== false ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          <h4 style={{ color: 'var(--text)', margin: 0 }}>
                            <Table2 size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                            {table.caption} ({table.row_count} rows × {table.col_count} cols)
                          </h4>
                        </div>
                        {expandedSections[`table-${idx}`] !== false && (
                          <div style={{ overflowX: 'auto' }}>
                            <table className="data-table">
                              {table.headers?.length > 0 && (
                                <thead><tr>{table.headers.map((h, i) => <th key={i}>{h}</th>)}</tr></thead>
                              )}
                              <tbody>
                                {table.rows.slice(0, 50).map((row, ri) => (
                                  <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{cell}</td>)}</tr>
                                ))}
                              </tbody>
                            </table>
                            {table.rows.length > 50 && (
                              <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>Showing first 50 of {table.row_count} rows</p>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p style={{ color: 'var(--text-dim)' }}>No tables found on this page.</p>
                  )}

                  {/* Lists */}
                  {structured.lists?.length > 0 && (
                    <div style={{ marginTop: 24 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 12 }}>
                        <List size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                        Lists ({structured.lists.length})
                      </h3>
                      {structured.lists.slice(0, 10).map((list, idx) => (
                        <div key={idx} style={{ marginBottom: 16, background: 'var(--bg)', padding: 12, borderRadius: 8 }}>
                          <div style={{ color: 'var(--text-dim)', fontSize: 12, marginBottom: 6 }}>
                            {list.type === 'ol' ? 'Ordered' : 'Unordered'} list • {list.count} items
                          </div>
                          <ul style={{ paddingLeft: 20, margin: 0 }}>
                            {list.items.slice(0, 8).map((item, i) => (
                              <li key={i} style={{ color: 'var(--text)', marginBottom: 4, fontSize: 13 }}>{item}</li>
                            ))}
                          </ul>
                          {list.items.length > 8 && (
                            <p style={{ color: 'var(--text-dim)', fontSize: 12, marginTop: 4 }}>...and {list.items.length - 8} more</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Headings */}
                  {structured.headings?.length > 0 && (
                    <div style={{ marginTop: 24 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 12 }}>Content Outline</h3>
                      {structured.headings.map((h, i) => (
                        <div key={i} style={{
                          paddingLeft: (h.level - 1) * 16,
                          color: h.level <= 2 ? 'var(--text)' : 'var(--text-dim)',
                          fontSize: Math.max(12, 16 - h.level),
                          fontWeight: h.level <= 2 ? 600 : 400,
                          marginBottom: 4,
                        }}>
                          {'#'.repeat(h.level)} {h.text}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ===== AI Insights ===== */}
              {activeTab === 'ai' && (
                <div>
                  {ai.skipped ? (
                    <p style={{ color: 'var(--text-dim)' }}>AI analysis was skipped. Enable "Include AI analysis" to get insights.</p>
                  ) : ai.error ? (
                    <div className="error-banner">{ai.error}</div>
                  ) : ai.answer ? (
                    /* Custom instruction response */
                    <div>
                      <div style={{ color: 'var(--text)', lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: 16 }}>
                        {ai.answer}
                      </div>
                      {ai.data && Object.keys(ai.data).length > 0 && (
                        <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13, background: 'var(--bg)', padding: 12, borderRadius: 8 }}>
                          {JSON.stringify(ai.data, null, 2)}
                        </pre>
                      )}
                    </div>
                  ) : (
                    /* Standard analysis */
                    <div>
                      {ai.summary && (
                        <div style={{ marginBottom: 20 }}>
                          <h3 style={{ color: 'var(--text)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Sparkles size={16} /> Summary
                          </h3>
                          <p style={{ color: 'var(--text-dim)', lineHeight: 1.7 }}>{ai.summary}</p>
                        </div>
                      )}

                      {ai.key_insights?.length > 0 && (
                        <div style={{ marginBottom: 20 }}>
                          <h3 style={{ color: 'var(--text)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Target size={16} /> Key Insights
                          </h3>
                          <ul style={{ paddingLeft: 20 }}>
                            {ai.key_insights.map((insight, i) => (
                              <li key={i} style={{ color: 'var(--text-dim)', marginBottom: 6, lineHeight: 1.5 }}>{insight}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {ai.topics?.length > 0 && (
                        <div style={{ marginBottom: 20 }}>
                          <h3 style={{ color: 'var(--text)', marginBottom: 8 }}><Tag size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />Topics</h3>
                          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {ai.topics.map((t, i) => <span key={i} className="badge">{t}</span>)}
                          </div>
                        </div>
                      )}

                      {ai.entities && Object.entries(ai.entities).some(([, items]) => items?.length > 0) && (
                        <div style={{ marginBottom: 20 }}>
                          <h3 style={{ color: 'var(--text)', marginBottom: 8 }}>Entities</h3>
                          {Object.entries(ai.entities).map(([type, items]) => (
                            items?.length > 0 && (
                              <div key={type} style={{ marginBottom: 12 }}>
                                <h4 style={{ color: 'var(--text-dim)', marginBottom: 6, textTransform: 'capitalize', fontSize: 13 }}>{type}</h4>
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                  {items.map((item, i) => <span key={i} className="badge">{item}</span>)}
                                </div>
                              </div>
                            )
                          ))}
                        </div>
                      )}

                      {ai.important_data?.length > 0 && (
                        <div style={{ marginBottom: 20 }}>
                          <h3 style={{ color: 'var(--text)', marginBottom: 8 }}>Important Data</h3>
                          <table className="data-table">
                            <thead><tr><th>Data Point</th><th>Value</th></tr></thead>
                            <tbody>
                              {ai.important_data.map((d, i) => (
                                <tr key={i}><td><strong>{d.label}</strong></td><td>{d.value}</td></tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {ai.action_items?.length > 0 && (
                        <div>
                          <h3 style={{ color: 'var(--text)', marginBottom: 8 }}>Action Items</h3>
                          <ul style={{ paddingLeft: 20 }}>
                            {ai.action_items.map((item, i) => (
                              <li key={i} style={{ color: 'var(--text-dim)', marginBottom: 4 }}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* ===== Content (scraped text/markdown) ===== */}
              {activeTab === 'content' && (
                <div>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                    <span className="badge">📝 {scrape.word_count} words</span>
                    {scrape.status_code && <span className="badge">HTTP {scrape.status_code}</span>}
                  </div>
                  {scrape.markdown ? (
                    <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13, lineHeight: 1.6, maxHeight: 500, overflow: 'auto' }}>
                      {scrape.markdown}
                    </pre>
                  ) : scrape.text ? (
                    <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13, lineHeight: 1.6, maxHeight: 500, overflow: 'auto' }}>
                      {scrape.text}
                    </pre>
                  ) : (
                    <p style={{ color: 'var(--text-dim)' }}>No content available.</p>
                  )}
                </div>
              )}

              {/* ===== Raw JSON ===== */}
              {activeTab === 'json' && (
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <button className="btn btn-secondary" onClick={handleCopy}>
                      {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy Full JSON</>}
                    </button>
                  </div>
                  <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 12, maxHeight: 600, overflow: 'auto' }}>
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </>
  )
}
