import { useState, useCallback } from 'react'
import { Brain, Play, Copy, Check, Sparkles, Target, Tag, MessageSquare } from 'lucide-react'
import { analyzeUrl } from '../api'

export default function AnalyzePage() {
  const [url, setUrl] = useState('')
  const [instruction, setInstruction] = useState('')
  const [useBrowser, setUseBrowser] = useState(false)
  const [mainContent, setMainContent] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [copied, setCopied] = useState(false)

  const handleAnalyze = useCallback(async () => {
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const payload = {
        url: url.trim(),
        use_browser: useBrowser,
        only_main_content: mainContent,
      }
      if (instruction.trim()) payload.instruction = instruction.trim()
      const data = await analyzeUrl(payload)
      if (data.error) throw new Error(data.error)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [url, instruction, useBrowser, mainContent])

  const a = result?.analysis || {}

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(a, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const sentimentColor = {
    positive: '#22c55e',
    negative: '#ef4444',
    neutral: '#94a3b8',
    mixed: '#f59e0b',
  }

  // If custom instruction was used, show the custom response view
  const isCustom = !!a.instruction || !!a.answer

  return (
    <>
      <div className="page-header">
        <h1>AI Analyze</h1>
        <p>Let AI extract insights, entities, and structured intel from any page</p>
      </div>

      <div className="card">
        <div className="card-header"><Brain size={16} /> Analyze URL</div>

        <div className="form-group">
          <label>URL</label>
          <input
            className="input"
            placeholder="https://techcrunch.com/2024/..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
          />
        </div>

        <div className="form-group">
          <label>Custom Instruction <span style={{ color: 'var(--text-dim)', fontWeight: 400 }}>(optional - leave blank for full analysis)</span></label>
          <textarea
            className="input"
            placeholder="e.g. Extract all pricing info and compare plans..."
            value={instruction}
            onChange={e => setInstruction(e.target.value)}
            rows={3}
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
            Use headless browser
          </label>
        </div>

        <button className="btn btn-primary" disabled={loading || !url.trim()} onClick={handleAnalyze}>
          {loading ? <><span className="spinner" /> Analyzing with AI…</> : <><Sparkles size={16} /> Analyze</>}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && !isCustom && (
        <>
          {/* Summary card */}
          <div className="card" style={{ borderLeft: '3px solid var(--primary)' }}>
            <div className="card-header"><Sparkles size={16} /> AI Summary</div>
            <p style={{ color: 'var(--text)', lineHeight: 1.6, fontSize: 15 }}>
              {a.summary || 'No summary available'}
            </p>
            <div style={{ display: 'flex', gap: 12, marginTop: 12, flexWrap: 'wrap' }}>
              {a.content_type && (
                <span className="badge">{a.content_type}</span>
              )}
              {a.sentiment && (
                <span className="badge" style={{ background: sentimentColor[a.sentiment] + '22', color: sentimentColor[a.sentiment] }}>
                  {a.sentiment}
                </span>
              )}
              {a.quality_score !== undefined && (
                <span className="badge" style={{ background: a.quality_score >= 7 ? '#22c55e22' : a.quality_score >= 4 ? '#f59e0b22' : '#ef444422', color: a.quality_score >= 7 ? '#22c55e' : a.quality_score >= 4 ? '#f59e0b' : '#ef4444' }}>
                  Quality: {a.quality_score}/10
                </span>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="card">
            <div className="tab-bar">
              {['overview', 'entities', 'data', 'json'].map(tab => (
                <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            <div className="result-box" style={{ minHeight: 200 }}>
              {/* Overview */}
              {activeTab === 'overview' && (
                <div>
                  {a.key_insights?.length > 0 && (
                    <div style={{ marginBottom: 20 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Target size={16} /> Key Insights
                      </h3>
                      <ul style={{ paddingLeft: 20 }}>
                        {a.key_insights.map((insight, i) => (
                          <li key={i} style={{ color: 'var(--text-dim)', marginBottom: 6, lineHeight: 1.5 }}>{insight}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {a.topics?.length > 0 && (
                    <div style={{ marginBottom: 20 }}>
                      <h3 style={{ color: 'var(--text)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Tag size={16} /> Topics
                      </h3>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {a.topics.map((topic, i) => (
                          <span key={i} className="badge">{topic}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {a.action_items?.length > 0 && (
                    <div>
                      <h3 style={{ color: 'var(--text)', marginBottom: 8 }}>Action Items</h3>
                      <ul style={{ paddingLeft: 20 }}>
                        {a.action_items.map((item, i) => (
                          <li key={i} style={{ color: 'var(--text-dim)', marginBottom: 4 }}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {a.quality_reasoning && (
                    <div style={{ marginTop: 16, padding: 12, background: 'var(--bg)', borderRadius: 8 }}>
                      <strong style={{ color: 'var(--text)' }}>Quality Assessment:</strong>
                      <p style={{ color: 'var(--text-dim)', marginTop: 4 }}>{a.quality_reasoning}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Entities */}
              {activeTab === 'entities' && (
                <div>
                  {a.entities ? (
                    Object.entries(a.entities).map(([type, items]) => (
                      items?.length > 0 && (
                        <div key={type} style={{ marginBottom: 16 }}>
                          <h4 style={{ color: 'var(--text)', marginBottom: 6, textTransform: 'capitalize' }}>{type}</h4>
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {items.map((item, i) => (
                              <span key={i} className="badge">{item}</span>
                            ))}
                          </div>
                        </div>
                      )
                    ))
                  ) : <p style={{ color: 'var(--text-dim)' }}>No entities detected.</p>}
                </div>
              )}

              {/* Important Data */}
              {activeTab === 'data' && (
                a.important_data?.length > 0 ? (
                  <table className="data-table">
                    <thead><tr><th>Data Point</th><th>Value</th></tr></thead>
                    <tbody>
                      {a.important_data.map((d, i) => (
                        <tr key={i}><td><strong>{d.label}</strong></td><td>{d.value}</td></tr>
                      ))}
                    </tbody>
                  </table>
                ) : <p style={{ color: 'var(--text-dim)' }}>No structured data points extracted.</p>
              )}

              {/* Raw JSON */}
              {activeTab === 'json' && (
                <>
                  <div style={{ marginBottom: 8 }}>
                    <button className="btn btn-secondary" onClick={handleCopy}>
                      {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy JSON</>}
                    </button>
                  </div>
                  <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13 }}>
                    {JSON.stringify(a, null, 2)}
                  </pre>
                </>
              )}
            </div>
          </div>
        </>
      )}

      {/* Custom instruction result */}
      {result && isCustom && (
        <div className="card" style={{ borderLeft: '3px solid var(--primary)' }}>
          <div className="card-header"><MessageSquare size={16} /> AI Response</div>
          {a.confidence && (
            <span className="badge" style={{ marginBottom: 12, display: 'inline-block' }}>
              Confidence: {a.confidence}
            </span>
          )}
          <div style={{ color: 'var(--text)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
            {a.answer || a.raw_response || JSON.stringify(a, null, 2)}
          </div>
          {a.data && Object.keys(a.data).length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h4 style={{ color: 'var(--text)', marginBottom: 8 }}>Extracted Data</h4>
              <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13, background: 'var(--bg)', padding: 12, borderRadius: 8 }}>
                {JSON.stringify(a.data, null, 2)}
              </pre>
            </div>
          )}
          <div style={{ marginTop: 12 }}>
            <button className="btn btn-secondary" onClick={handleCopy}>
              {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy JSON</>}
            </button>
          </div>
        </div>
      )}
    </>
  )
}
