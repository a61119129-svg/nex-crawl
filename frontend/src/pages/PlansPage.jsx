import { useState, useCallback } from 'react'
import {
  CreditCard, Play, Copy, Check, Sparkles, Star, Clock,
  Filter, ChevronDown, ChevronUp, Shield, Brain, Tag
} from 'lucide-react'
import { scrapePlans } from '../api'

export default function PlansPage() {
  const [url, setUrl] = useState('')
  const [clickSelectors, setClickSelectors] = useState('')
  const [includeAi, setIncludeAi] = useState(true)
  const [loadPages, setLoadPages] = useState(false)
  const [nextSelector, setNextSelector] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('plans')
  const [copied, setCopied] = useState(false)
  const [expandedPlans, setExpandedPlans] = useState({})
  const [showAdvanced, setShowAdvanced] = useState(false)

  const togglePlan = (idx) => setExpandedPlans(prev => ({ ...prev, [idx]: !prev[idx] }))

  const handleScrape = useCallback(async () => {
    if (!url.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setActiveTab('plans')
    try {
      const payload = {
        url: url.trim(),
        include_ai: includeAi,
        load_all_pages: loadPages,
      }
      if (clickSelectors.trim()) {
        payload.click_selectors = clickSelectors.split(',').map(s => s.trim()).filter(Boolean)
      }
      if (loadPages && nextSelector.trim()) {
        payload.next_button_selector = nextSelector.trim()
      }
      const data = await scrapePlans(payload)
      if (data.error && !data.success) throw new Error(data.error)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [url, clickSelectors, includeAi, loadPages, nextSelector])

  const handleCopy = (text) => {
    navigator.clipboard.writeText(typeof text === 'string' ? text : JSON.stringify(text, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const ai = result?.ai_analysis || {}

  return (
    <>
      <div className="page-header">
        <h1>Plans Scraper</h1>
        <p>Scrape pricing pages with filter interactions, CAPTCHA bypass &amp; stealth mode</p>
      </div>

      {/* Input card */}
      <div className="card">
        <div className="card-header"><CreditCard size={16} /> Scrape Pricing Page</div>

        <div className="form-group">
          <label>URL</label>
          <input
            className="input"
            placeholder="https://example.com/pricing"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleScrape()}
          />
        </div>

        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12,
          padding: '8px 12px', background: 'rgba(139,92,246,0.08)', borderRadius: 8,
          border: '1px solid rgba(139,92,246,0.2)', fontSize: 13, color: 'var(--text-dim)'
        }}>
          <Shield size={14} style={{ color: '#8b5cf6', flexShrink: 0 }} />
          <span>Stealth browser + reCAPTCHA/hCaptcha/Cloudflare bypass enabled automatically</span>
        </div>

        <div className="toggle-group">
          <label className="toggle-label">
            <input type="checkbox" checked={includeAi} onChange={e => setIncludeAi(e.target.checked)} />
            AI analysis of plans
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={loadPages} onChange={e => setLoadPages(e.target.checked)} />
            Load paginated results
          </label>
        </div>

        <div style={{ marginBottom: 12 }}>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            style={{
              background: 'none', border: 'none', color: 'var(--text-dim)',
              cursor: 'pointer', fontSize: 13, display: 'flex', alignItems: 'center', gap: 4, padding: 0,
            }}
          >
            {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            Advanced filter options
          </button>
        </div>

        {showAdvanced && (
          <div style={{ background: 'var(--bg)', padding: 16, borderRadius: 8, marginBottom: 12 }}>
            <div className="form-group">
              <label>Click selectors <span style={{ color: 'var(--text-dim)', fontWeight: 400 }}>(comma-separated CSS selectors for filter buttons)</span></label>
              <input
                className="input"
                placeholder='e.g. .pricing-toggle button, [data-billing="yearly"]'
                value={clickSelectors}
                onChange={e => setClickSelectors(e.target.value)}
              />
            </div>

            {loadPages && (
              <div className="form-group">
                <label>Next page button selector</label>
                <input
                  className="input"
                  placeholder='e.g. .pagination .next, button:has-text("Next")'
                  value={nextSelector}
                  onChange={e => setNextSelector(e.target.value)}
                />
              </div>
            )}
          </div>
        )}

        <button className="btn btn-primary" disabled={loading || !url.trim()} onClick={handleScrape}>
          {loading
            ? <><span className="spinner" /> Scraping plans…</>
            : <><CreditCard size={16} /> Scrape Plans</>
          }
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && result.success && (
        <>
          {/* Summary banner */}
          <div className="card" style={{ borderLeft: '3px solid #8b5cf6' }}>
            <div className="card-header"><Tag size={16} /> Results Summary</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 12 }}>
              {[
                { icon: '💰', label: 'Plans Found', value: result.total_plans_found },
                { icon: '🔁', label: 'Filter States', value: result.filter_states_scraped },
                { icon: '📄', label: 'Pages Loaded', value: result.pages_loaded },
                { icon: '⏱️', label: 'Time', value: `${result.timing}s` },
              ].map(s => (
                <div key={s.label} style={{ background: 'var(--bg)', padding: '10px 14px', borderRadius: 8, textAlign: 'center' }}>
                  <div style={{ fontSize: 20 }}>{s.icon}</div>
                  <div style={{ color: 'var(--text)', fontWeight: 600, fontSize: 18 }}>{s.value}</div>
                  <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>{s.label}</div>
                </div>
              ))}
            </div>

            {result.billing_options?.length > 0 && (
              <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>Billing options:</span>
                {result.billing_options.map((opt, i) => (
                  <span key={i} className="badge">{opt}</span>
                ))}
              </div>
            )}
          </div>

          {/* Tabs */}
          <div className="card">
            <div className="tab-bar">
              {['plans', 'compare', 'ai', 'markdown', 'json'].map(tab => (
                <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
                  {tab === 'ai' ? 'AI Analysis' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            <div className="result-box" style={{ minHeight: 300 }}>

              {/* ===== Plans Cards ===== */}
              {activeTab === 'plans' && (
                <div>
                  {result.all_plans?.length > 0 ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                      {result.all_plans.map((plan, idx) => (
                        <div key={idx} style={{
                          border: plan.highlighted ? '2px solid #8b5cf6' : '1px solid var(--border)',
                          borderRadius: 12, padding: 20, position: 'relative',
                          background: plan.highlighted ? 'rgba(139,92,246,0.05)' : 'var(--surface)',
                        }}>
                          {plan.highlighted && (
                            <div style={{
                              position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)',
                              background: '#8b5cf6', color: '#fff', padding: '2px 12px', borderRadius: 10, fontSize: 11
                            }}>
                              <Star size={10} style={{ marginRight: 4 }} />RECOMMENDED
                            </div>
                          )}

                          <h3 style={{ color: 'var(--text)', marginBottom: 4, fontSize: 18 }}>{plan.name || 'Unnamed Plan'}</h3>

                          {plan.price && (
                            <div style={{ fontSize: 28, fontWeight: 700, color: '#8b5cf6', marginBottom: 4 }}>
                              {plan.price}
                            </div>
                          )}
                          {plan.period && (
                            <div style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 8 }}>{plan.period}</div>
                          )}
                          {plan.filter_source && plan.filter_source !== 'initial' && plan.filter_source !== 'final' && (
                            <span className="badge" style={{ fontSize: 11, marginBottom: 8, display: 'inline-block' }}>
                              {plan.filter_source}
                            </span>
                          )}
                          {plan.description && (
                            <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 12, lineHeight: 1.5 }}>{plan.description}</p>
                          )}

                          {plan.features?.length > 0 && (
                            <>
                              <div
                                onClick={() => togglePlan(idx)}
                                style={{ cursor: 'pointer', color: 'var(--primary)', fontSize: 13, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}
                              >
                                {expandedPlans[idx] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                                {plan.features.length} features
                              </div>
                              {expandedPlans[idx] && (
                                <ul style={{ paddingLeft: 16, margin: 0 }}>
                                  {plan.features.map((f, fi) => (
                                    <li key={fi} style={{ color: 'var(--text-dim)', fontSize: 12, marginBottom: 4, lineHeight: 1.4 }}>{f}</li>
                                  ))}
                                </ul>
                              )}
                            </>
                          )}

                          {plan.cta_text && (
                            <div style={{ marginTop: 12, padding: '8px 0', borderTop: '1px solid var(--border)', color: 'var(--text-dim)', fontSize: 12 }}>
                              CTA: {plan.cta_text}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: 'var(--text-dim)' }}>No plans could be extracted. Try providing custom filter selectors.</p>
                  )}
                </div>
              )}

              {/* ===== Comparison Table ===== */}
              {activeTab === 'compare' && (
                result.comparison_table ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                      {result.comparison_table.headers?.length > 0 && (
                        <thead>
                          <tr>{result.comparison_table.headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
                        </thead>
                      )}
                      <tbody>
                        {result.comparison_table.rows?.map((row, ri) => (
                          <tr key={ri}>
                            {row.map((cell, ci) => (
                              <td key={ci} style={{
                                color: cell === '✓' ? '#22c55e' : cell === '✗' ? '#ef4444' : 'var(--text)',
                                fontWeight: cell === '✓' || cell === '✗' ? 700 : 400,
                                textAlign: ci === 0 ? 'left' : 'center',
                              }}>{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p style={{ color: 'var(--text-dim)' }}>No comparison table found on this page.</p>
                )
              )}

              {/* ===== AI Analysis ===== */}
              {activeTab === 'ai' && (
                <div>
                  {ai.error ? (
                    <div className="error-banner">{ai.error}</div>
                  ) : ai.answer ? (
                    <div>
                      {ai.confidence && (
                        <span className="badge" style={{ marginBottom: 12, display: 'inline-block' }}>
                          Confidence: {ai.confidence}
                        </span>
                      )}
                      <div style={{ color: 'var(--text)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                        {ai.answer}
                      </div>
                      {ai.data && Object.keys(ai.data).length > 0 && (
                        <div style={{ marginTop: 16 }}>
                          <h4 style={{ color: 'var(--text)', marginBottom: 8 }}>Extracted Data</h4>
                          <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13, background: 'var(--bg)', padding: 12, borderRadius: 8 }}>
                            {JSON.stringify(ai.data, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  ) : Object.keys(ai).length === 0 ? (
                    <p style={{ color: 'var(--text-dim)' }}>AI analysis was not included. Enable it and re-scan.</p>
                  ) : (
                    <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13 }}>
                      {JSON.stringify(ai, null, 2)}
                    </pre>
                  )}
                </div>
              )}

              {/* ===== Markdown ===== */}
              {activeTab === 'markdown' && (
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <button className="btn btn-secondary" onClick={() => handleCopy(result.markdown)}>
                      {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy Markdown</>}
                    </button>
                  </div>
                  <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-dim)', fontSize: 13, lineHeight: 1.6 }}>
                    {result.markdown || 'No markdown generated.'}
                  </pre>
                </div>
              )}

              {/* ===== Raw JSON ===== */}
              {activeTab === 'json' && (
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <button className="btn btn-secondary" onClick={() => handleCopy(result)}>
                      {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy JSON</>}
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
