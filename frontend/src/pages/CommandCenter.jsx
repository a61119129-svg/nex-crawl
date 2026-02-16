import { useState, useCallback } from 'react'
import {
  Zap, Play, Globe, Camera, Radar, CreditCard, Bug, FileSearch,
  Table, Brain, Copy, Check, Download, ChevronDown, ChevronUp,
  Image, Eye, Loader2, AlertCircle, CheckCircle2, Settings2,
  Monitor, Shield, ShieldCheck, Cookie
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import {
  scrapeUrl, crawlUrl, extractData, formatData, analyzeUrl,
  deepScan, scrapePlans, takeScreenshot
} from '../api'

/* ── Feature definitions ─────────────────────────────────────── */
const FEATURES = [
  { id: 'scrape', label: 'Scrape', icon: Globe, color: '#a78bfa', desc: 'Fetch & clean page content' },
  { id: 'screenshot', label: 'Screenshot', icon: Camera, color: '#f472b6', desc: 'Capture page screenshot' },
  { id: 'scan', label: 'Deep Scan', icon: Radar, color: '#38bdf8', desc: 'Full pipeline analysis' },
  { id: 'format', label: 'Format', icon: Table, color: '#34d399', desc: 'Extract structured data' },
  { id: 'ai', label: 'AI Analyze', icon: Brain, color: '#fbbf24', desc: 'AI-powered insights' },
  { id: 'plans', label: 'Plans Scraper', icon: CreditCard, color: '#fb923c', desc: 'Scrape pricing pages' },
  { id: 'extract', label: 'Extract', icon: FileSearch, color: '#c084fc', desc: 'CSS/XPath extraction' },
  { id: 'crawl', label: 'Crawl', icon: Bug, color: '#4ade80', desc: 'Multi-page site crawl' },
]

function saveHistory(entry) {
  try {
    const h = JSON.parse(localStorage.getItem('wv_history') || '[]')
    h.push(entry)
    if (h.length > 100) h.splice(0, h.length - 100)
    localStorage.setItem('wv_history', JSON.stringify(h))
  } catch { }
}

/* ── Collapsible result section ──────────────────────────────── */
function ResultSection({ title, icon: Icon, color, open, onToggle, badge, children }) {
  return (
    <div className="card" style={{ borderLeft: `3px solid ${color}` }}>
      <div
        className="card-header"
        style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        onClick={onToggle}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Icon size={16} style={{ color }} /> {title}
          {badge && <span className="badge" style={{ background: color, color: '#fff', fontSize: 11, padding: '2px 8px', borderRadius: 99 }}>{badge}</span>}
        </span>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </div>
      {open && <div style={{ padding: '12px 0 0' }}>{children}</div>}
    </div>
  )
}

export default function CommandCenter() {
  /* ── State ─────────────────────────────────────────────────── */
  const [url, setUrl] = useState('')
  const [selected, setSelected] = useState({ scrape: true, screenshot: true })
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Common options
  const [acceptCookies, setAcceptCookies] = useState(true)
  const [stealth, setStealth] = useState(false)
  const [bypassCaptcha, setBypassCaptcha] = useState(false)
  const [useBrowser, setUseBrowser] = useState(true)
  const [mainContent, setMainContent] = useState(true)
  const [waitFor, setWaitFor] = useState(0)

  // Scrape options
  const [scrapeFormat, setScrapeFormat] = useState('markdown')

  // Screenshot options
  const [fullPage, setFullPage] = useState(true)
  const [vpWidth, setVpWidth] = useState(1280)
  const [vpHeight, setVpHeight] = useState(800)

  // Scan options
  const [scanInstruction, setScanInstruction] = useState('')
  const [scanIncludeAi, setScanIncludeAi] = useState(true)

  // AI options
  const [aiInstruction, setAiInstruction] = useState('')

  // Plans options
  const [plansIncludeAi, setPlansIncludeAi] = useState(true)

  // Extract options
  const [extractSchema, setExtractSchema] = useState('{\n  "title": "h1",\n  "price": ".price"\n}')

  // Crawl options
  const [crawlDepth, setCrawlDepth] = useState(2)
  const [crawlMaxPages, setCrawlMaxPages] = useState(20)

  // Results & UI state
  const [loading, setLoading] = useState(false)
  const [runningFeatures, setRunningFeatures] = useState({})
  const [results, setResults] = useState({})
  const [errors, setErrors] = useState({})
  const [openSections, setOpenSections] = useState({})
  const [copied, setCopied] = useState('')

  const toggleFeature = (id) => setSelected(prev => ({ ...prev, [id]: !prev[id] }))
  const toggleSection = (id) => setOpenSections(prev => ({ ...prev, [id]: !prev[id] }))
  const selectedFeatures = FEATURES.filter(f => selected[f.id])

  /* ── Run all selected features ────────────────────────────── */
  const handleRun = useCallback(async () => {
    if (!url.trim() || selectedFeatures.length === 0) return
    setLoading(true)
    setResults({})
    setErrors({})
    const opens = {}
    selectedFeatures.forEach(f => { opens[f.id] = true })
    setOpenSections(opens)

    const tasks = selectedFeatures.map(async (feature) => {
      setRunningFeatures(prev => ({ ...prev, [feature.id]: true }))
      try {
        let data
        switch (feature.id) {
          case 'scrape':
            data = await scrapeUrl({
              url: url.trim(),
              formats: [scrapeFormat],
              use_browser: true,
              only_main_content: mainContent,
              wait_for: waitFor,
              stealth, bypass_captcha: bypassCaptcha,
              accept_cookies: acceptCookies,
            })
            saveHistory({ type: 'scrape', url: url.trim(), time: Date.now(), error: null })
            break

          case 'screenshot':
            data = await takeScreenshot({
              url: url.trim(),
              full_page: fullPage,
              wait_for: waitFor,
              stealth, bypass_captcha: bypassCaptcha,
              viewport_width: vpWidth,
              viewport_height: vpHeight,
            })
            break

          case 'scan':
            data = await deepScan({
              url: url.trim(),
              use_browser: true,
              only_main_content: mainContent,
              include_ai: scanIncludeAi,
              stealth, bypass_captcha: bypassCaptcha,
              accept_cookies: acceptCookies,
              ...(scanInstruction.trim() ? { instruction: scanInstruction.trim() } : {}),
            })
            break

          case 'format':
            data = await formatData({
              url: url.trim(),
              use_browser: true,
              wait_for: waitFor,
              only_main_content: mainContent,
            })
            break

          case 'ai':
            data = await analyzeUrl({
              url: url.trim(),
              use_browser: true,
              wait_for: waitFor,
              only_main_content: mainContent,
              ...(aiInstruction.trim() ? { instruction: aiInstruction.trim() } : {}),
            })
            break

          case 'plans':
            data = await scrapePlans({
              url: url.trim(),
              include_ai: plansIncludeAi,
              wait_for: waitFor > 0 ? waitFor : 2000,
            })
            break

          case 'extract': {
            let schemaObj
            try { schemaObj = JSON.parse(extractSchema) } catch { schemaObj = { title: 'h1' } }
            data = await extractData({
              url: url.trim(),
              schema: schemaObj,
              use_browser: true,
              wait_for: waitFor,
            })
            break
          }

          case 'crawl':
            data = await crawlUrl({
              url: url.trim(),
              max_depth: crawlDepth,
              max_pages: crawlMaxPages,
              formats: ['markdown'],
              use_browser: true,
            })
            break

          default:
            break
        }
        setResults(prev => ({ ...prev, [feature.id]: data }))
      } catch (e) {
        setErrors(prev => ({ ...prev, [feature.id]: e.message }))
      } finally {
        setRunningFeatures(prev => ({ ...prev, [feature.id]: false }))
      }
    })

    await Promise.allSettled(tasks)
    setLoading(false)
  }, [url, selectedFeatures, scrapeFormat, useBrowser, mainContent, waitFor, stealth, bypassCaptcha, acceptCookies, fullPage, vpWidth, vpHeight, scanInstruction, scanIncludeAi, aiInstruction, plansIncludeAi, extractSchema, crawlDepth, crawlMaxPages])

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(''), 2000)
  }

  const handleDownloadScreenshot = (b64) => {
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${b64}`
    link.download = `screenshot-${Date.now()}.png`
    link.click()
  }

  const handleDownloadText = (text, ext = 'md') => {
    const blob = new Blob([text], { type: 'text/plain' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `nexcrawl-${Date.now()}.${ext}`
    a.click()
  }

  /* ── Render ────────────────────────────────────────────────── */
  return (
    <>
      <div className="page-header">
        <h1><Zap size={24} style={{ color: '#a78bfa' }} /> Command Center</h1>
        <p>All features in one place — everything runs in a real browser with cookie consent, JS rendering & formatted output.</p>
      </div>

      {/* ── URL Input ─────────────────────────────────────────── */}
      <div className="card">
        <div className="card-header"><Globe size={16} /> Target URL</div>
        <div className="form-group">
          <input
            className="input"
            placeholder="https://example.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleRun()}
            style={{ fontSize: 16 }}
          />
        </div>

        {/* ── Feature Picker ──────────────────────────────────── */}
        <div style={{ marginTop: 12 }}>
          <label style={{ fontSize: 13, color: '#94a3b8', marginBottom: 8, display: 'block' }}>Select features to run:</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {FEATURES.map(f => {
              const Icon = f.icon
              const active = selected[f.id]
              return (
                <button
                  key={f.id}
                  onClick={() => toggleFeature(f.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '8px 14px', borderRadius: 8,
                    border: active ? `2px solid ${f.color}` : '2px solid #334155',
                    background: active ? `${f.color}15` : '#0f172a',
                    color: active ? f.color : '#64748b',
                    cursor: 'pointer', fontSize: 13, fontWeight: 500,
                    transition: 'all 0.2s',
                  }}
                >
                  <Icon size={15} /> {f.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Common Options ──────────────────────────────────── */}
        <div style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <Monitor size={14} style={{ color: '#38bdf8' }} />
            <span style={{ fontSize: 12, color: '#38bdf8', fontWeight: 600 }}>Browser-first mode — all scraping opens a real browser for cookies, JS & full content</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
          <label className="toggle-label">
            <input type="checkbox" checked={acceptCookies} onChange={e => setAcceptCookies(e.target.checked)} />
            <Cookie size={14} /> Accept Cookies
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={stealth} onChange={e => setStealth(e.target.checked)} />
            <Shield size={14} /> Stealth Mode
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={bypassCaptcha} onChange={e => setBypassCaptcha(e.target.checked)} />
            <ShieldCheck size={14} /> Bypass CAPTCHA
          </label>
          <label className="toggle-label">
            <input type="checkbox" checked={mainContent} onChange={e => setMainContent(e.target.checked)} />
            <Eye size={14} /> Main Content Only
          </label>
          </div>
        </div>

        {/* ── Advanced / Feature-specific options ───────────── */}
        <div style={{ marginTop: 12 }}>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            style={{
              background: 'none', border: 'none', color: '#64748b', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, padding: 4,
            }}
          >
            <Settings2 size={14} /> Advanced Options
            {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {showAdvanced && (
            <div style={{ marginTop: 12, padding: 16, background: '#0f172a', borderRadius: 10, border: '1px solid #1e293b' }}>
              {/* Wait for */}
              <div className="form-row" style={{ gap: 16, flexWrap: 'wrap' }}>
                <div className="form-group" style={{ flex: '1 1 200px' }}>
                  <label>Wait After Load (ms)</label>
                  <input className="input" type="number" value={waitFor} onChange={e => setWaitFor(Number(e.target.value))} min={0} step={500} />
                </div>
              </div>

              {/* Scrape format */}
              {selected.scrape && (
                <div className="form-group" style={{ marginTop: 12 }}>
                  <label>Scrape Output Format</label>
                  <select className="input" value={scrapeFormat} onChange={e => setScrapeFormat(e.target.value)}>
                    {['markdown', 'html', 'text', 'raw_html'].map(f => <option key={f} value={f}>{f}</option>)}
                  </select>
                </div>
              )}

              {/* Screenshot options */}
              {selected.screenshot && (
                <div style={{ marginTop: 12 }}>
                  <label style={{ fontSize: 12, color: '#64748b', marginBottom: 6, display: 'block' }}>Screenshot Options</label>
                  <div className="form-row" style={{ gap: 12, flexWrap: 'wrap' }}>
                    <label className="toggle-label">
                      <input type="checkbox" checked={fullPage} onChange={e => setFullPage(e.target.checked)} />
                      Full Page
                    </label>
                    <div className="form-group" style={{ flex: '0 0 120px' }}>
                      <label>Width</label>
                      <input className="input" type="number" value={vpWidth} onChange={e => setVpWidth(Number(e.target.value))} min={320} max={3840} />
                    </div>
                    <div className="form-group" style={{ flex: '0 0 120px' }}>
                      <label>Height</label>
                      <input className="input" type="number" value={vpHeight} onChange={e => setVpHeight(Number(e.target.value))} min={240} max={2160} />
                    </div>
                  </div>
                </div>
              )}

              {/* Deep Scan options */}
              {selected.scan && (
                <div style={{ marginTop: 12 }}>
                  <label style={{ fontSize: 12, color: '#64748b', marginBottom: 6, display: 'block' }}>Deep Scan Options</label>
                  <div className="form-group">
                    <label>Custom AI Instruction</label>
                    <input className="input" placeholder="Focus on pricing, competitors, etc." value={scanInstruction} onChange={e => setScanInstruction(e.target.value)} />
                  </div>
                  <label className="toggle-label" style={{ marginTop: 8 }}>
                    <input type="checkbox" checked={scanIncludeAi} onChange={e => setScanIncludeAi(e.target.checked)} />
                    Include AI Analysis
                  </label>
                </div>
              )}

              {/* AI options */}
              {selected.ai && (
                <div className="form-group" style={{ marginTop: 12 }}>
                  <label>AI Custom Question</label>
                  <input className="input" placeholder="What are the key takeaways?" value={aiInstruction} onChange={e => setAiInstruction(e.target.value)} />
                </div>
              )}

              {/* Plans options */}
              {selected.plans && (
                <div style={{ marginTop: 12 }}>
                  <label className="toggle-label">
                    <input type="checkbox" checked={plansIncludeAi} onChange={e => setPlansIncludeAi(e.target.checked)} />
                    AI Analyze Plans
                  </label>
                </div>
              )}

              {/* Extract schema */}
              {selected.extract && (
                <div className="form-group" style={{ marginTop: 12 }}>
                  <label>Extraction Schema (JSON)</label>
                  <textarea
                    className="input"
                    rows={4}
                    style={{ fontFamily: 'monospace', fontSize: 13 }}
                    value={extractSchema}
                    onChange={e => setExtractSchema(e.target.value)}
                  />
                </div>
              )}

              {/* Crawl options */}
              {selected.crawl && (
                <div className="form-row" style={{ marginTop: 12, gap: 12 }}>
                  <div className="form-group" style={{ flex: '0 0 140px' }}>
                    <label>Max Depth</label>
                    <input className="input" type="number" value={crawlDepth} onChange={e => setCrawlDepth(Number(e.target.value))} min={0} max={10} />
                  </div>
                  <div className="form-group" style={{ flex: '0 0 140px' }}>
                    <label>Max Pages</label>
                    <input className="input" type="number" value={crawlMaxPages} onChange={e => setCrawlMaxPages(Number(e.target.value))} min={1} max={500} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Run Button ──────────────────────────────────────── */}
        <button
          className="btn btn-primary"
          onClick={handleRun}
          disabled={loading || !url.trim() || selectedFeatures.length === 0}
          style={{ marginTop: 16, width: '100%', padding: '14px', fontSize: 15 }}
        >
          {loading ? (
            <><Loader2 size={18} className="spin" /> Running {selectedFeatures.length} feature{selectedFeatures.length > 1 ? 's' : ''}…</>
          ) : (
            <><Play size={18} /> Run {selectedFeatures.length} Feature{selectedFeatures.length > 1 ? 's' : ''}</>
          )}
        </button>
      </div>

      {/* ── Progress Indicators ───────────────────────────────── */}
      {loading && (
        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
            {selectedFeatures.map(f => {
              const Icon = f.icon
              const running = runningFeatures[f.id]
              const done = results[f.id] || errors[f.id]
              const failed = errors[f.id]
              return (
                <div key={f.id} style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px',
                  borderRadius: 8, fontSize: 13, fontWeight: 500,
                  background: failed ? '#7f1d1d20' : done ? '#06523020' : running ? '#1e1b4b30' : '#1e293b',
                  color: failed ? '#ef4444' : done ? '#22c55e' : running ? f.color : '#64748b',
                  border: `1px solid ${failed ? '#7f1d1d' : done ? '#065230' : running ? f.color + '40' : '#334155'}`,
                }}>
                  {running && !done ? <Loader2 size={14} className="spin" /> : done ? (failed ? <AlertCircle size={14} /> : <CheckCircle2 size={14} />) : <Icon size={14} />}
                  {f.label}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Results ───────────────────────────────────────────── */}

      {/* Screenshot Result */}
      {(results.screenshot || errors.screenshot) && (
        <ResultSection
          title="Screenshot"
          icon={Camera}
          color="#f472b6"
          open={openSections.screenshot !== false}
          onToggle={() => toggleSection('screenshot')}
          badge={results.screenshot?.success ? results.screenshot.title : null}
        >
          {errors.screenshot ? (
            <div className="error-box">{errors.screenshot}</div>
          ) : (
            <div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <button className="btn btn-secondary btn-sm" onClick={() => handleDownloadScreenshot(results.screenshot.screenshot_base64)}>
                  <Download size={14} /> Download PNG
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => handleCopy(results.screenshot.screenshot_base64, 'ss-b64')}>
                  {copied === 'ss-b64' ? <Check size={14} /> : <Copy size={14} />} Copy Base64
                </button>
                {results.screenshot.title && (
                  <span style={{ color: '#94a3b8', fontSize: 13, marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
                    {results.screenshot.title} &middot; {results.screenshot.viewport?.width}x{results.screenshot.viewport?.height}
                  </span>
                )}
              </div>
              <div style={{ borderRadius: 10, overflow: 'hidden', border: '1px solid #1e293b', maxHeight: 600, overflowY: 'auto' }}>
                <img
                  src={`data:image/png;base64,${results.screenshot.screenshot_base64}`}
                  alt="Screenshot"
                  style={{ width: '100%', display: 'block' }}
                />
              </div>
            </div>
          )}
        </ResultSection>
      )}

      {/* Scrape Result */}
      {(results.scrape || errors.scrape) && (
        <ResultSection
          title="Scrape"
          icon={Globe}
          color="#a78bfa"
          open={openSections.scrape !== false}
          onToggle={() => toggleSection('scrape')}
          badge={results.scrape?.status_code ? `${results.scrape.status_code}` : null}
        >
          {errors.scrape ? (
            <div className="error-box">{errors.scrape}</div>
          ) : (() => {
            const content = results.scrape.markdown || results.scrape.html || results.scrape.text || results.scrape.raw_html || ''
            return (
              <div>
                <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => handleCopy(content, 'scrape')}>
                    {copied === 'scrape' ? <Check size={14} /> : <Copy size={14} />} Copy
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={() => handleDownloadText(content, scrapeFormat === 'markdown' ? 'md' : 'html')}>
                    <Download size={14} /> Download
                  </button>
                  {results.scrape.metadata?.title && (
                    <span style={{ color: '#94a3b8', fontSize: 13, marginLeft: 'auto' }}>{results.scrape.metadata.title}</span>
                  )}
                </div>
                <div className="result-box" style={{ maxHeight: 500, overflow: 'auto' }}>
                  {scrapeFormat === 'markdown' ? <ReactMarkdown>{content}</ReactMarkdown> : <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{content}</pre>}
                </div>
              </div>
            )
          })()}
        </ResultSection>
      )}

      {/* Deep Scan Result */}
      {(results.scan || errors.scan) && (
        <ResultSection
          title="Deep Scan"
          icon={Radar}
          color="#38bdf8"
          open={openSections.scan !== false}
          onToggle={() => toggleSection('scan')}
          badge={results.scan?.site_detection?.type || null}
        >
          {errors.scan ? (
            <div className="error-box">{errors.scan}</div>
          ) : (
            <div>
              {/* Summary stats */}
              <div className="stats-row" style={{ marginBottom: 12 }}>
                {results.scan.site_detection?.type && (
                  <div className="stat-card mini">
                    <div className="stat-label">Site Type</div>
                    <div className="stat-value" style={{ fontSize: 16 }}>{results.scan.site_detection.type}</div>
                  </div>
                )}
                {results.scan.scrape?.word_count != null && (
                  <div className="stat-card mini">
                    <div className="stat-label">Words</div>
                    <div className="stat-value" style={{ fontSize: 16 }}>{results.scan.scrape.word_count}</div>
                  </div>
                )}
                {results.scan.timing?.total != null && (
                  <div className="stat-card mini">
                    <div className="stat-label">Time</div>
                    <div className="stat-value" style={{ fontSize: 16 }}>{results.scan.timing.total}s</div>
                  </div>
                )}
              </div>

              {/* Smart extraction */}
              {results.scan.smart_extraction && Object.keys(results.scan.smart_extraction).length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 6, fontWeight: 600 }}>Smart Extraction</div>
                  <pre className="result-box" style={{ fontSize: 12, maxHeight: 300, overflow: 'auto' }}>
                    {JSON.stringify(results.scan.smart_extraction, null, 2)}
                  </pre>
                </div>
              )}

              {/* AI Analysis */}
              {results.scan.ai_analysis && Object.keys(results.scan.ai_analysis).length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 6, fontWeight: 600 }}>AI Analysis</div>
                  {results.scan.ai_analysis.summary && (
                    <p style={{ color: '#e2e8f0', fontSize: 14, lineHeight: 1.6 }}>{results.scan.ai_analysis.summary}</p>
                  )}
                  {results.scan.ai_analysis.key_insights && (
                    <ul style={{ color: '#cbd5e1', fontSize: 13 }}>
                      {results.scan.ai_analysis.key_insights.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                  )}
                </div>
              )}

              {/* Full JSON */}
              <details>
                <summary style={{ cursor: 'pointer', color: '#64748b', fontSize: 13 }}>Full Scan JSON</summary>
                <pre className="result-box" style={{ fontSize: 11, maxHeight: 400, overflow: 'auto', marginTop: 8 }}>
                  {JSON.stringify(results.scan, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </ResultSection>
      )}

      {/* Format Result */}
      {(results.format || errors.format) && (
        <ResultSection
          title="Structured Data"
          icon={Table}
          color="#34d399"
          open={openSections.format !== false}
          onToggle={() => toggleSection('format')}
          badge={results.format?.summary?.total_items != null ? `${results.format.summary.total_items} items` : null}
        >
          {errors.format ? (
            <div className="error-box">{errors.format}</div>
          ) : (
            <div>
              {/* Tables */}
              {results.format.tables?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>Tables ({results.format.tables.length})</div>
                  {results.format.tables.map((t, i) => (
                    <div key={i} style={{ overflowX: 'auto', marginBottom: 8 }}>
                      <table className="data-table">
                        <thead>
                          <tr>{(t.headers || []).map((h, j) => <th key={j}>{h}</th>)}</tr>
                        </thead>
                        <tbody>
                          {(t.rows || []).slice(0, 10).map((row, ri) => (
                            <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{cell}</td>)}</tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              )}

              {/* Lists */}
              {results.format.lists?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>Lists ({results.format.lists.length})</div>
                  {results.format.lists.slice(0, 5).map((lst, i) => (
                    <ul key={i} style={{ color: '#cbd5e1', fontSize: 13 }}>
                      {(lst.items || []).slice(0, 10).map((item, j) => <li key={j}>{item}</li>)}
                    </ul>
                  ))}
                </div>
              )}

              {/* KV Pairs */}
              {results.format.key_value_pairs?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>Key-Value Pairs</div>
                  <div className="kv-grid">
                    {results.format.key_value_pairs.slice(0, 20).map((kv, i) => (
                      <div key={i} className="kv-row">
                        <span className="kv-key">{kv.key}</span>
                        <span className="kv-val">{kv.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </ResultSection>
      )}

      {/* AI Analyze Result */}
      {(results.ai || errors.ai) && (
        <ResultSection
          title="AI Analysis"
          icon={Brain}
          color="#fbbf24"
          open={openSections.ai !== false}
          onToggle={() => toggleSection('ai')}
        >
          {errors.ai ? (
            <div className="error-box">{errors.ai}</div>
          ) : (
            <div>
              {results.ai.analysis?.summary && (
                <p style={{ color: '#e2e8f0', fontSize: 14, lineHeight: 1.7, marginBottom: 12 }}>{results.ai.analysis.summary}</p>
              )}
              {results.ai.analysis?.key_insights && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>Key Insights</div>
                  <ul style={{ color: '#cbd5e1', fontSize: 13 }}>
                    {results.ai.analysis.key_insights.map((item, i) => <li key={i} style={{ marginBottom: 4 }}>{item}</li>)}
                  </ul>
                </div>
              )}
              {results.ai.analysis?.entities && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>Entities</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {results.ai.analysis.entities.map((e, i) => (
                      <span key={i} className="badge" style={{ background: '#fbbf2420', color: '#fbbf24', padding: '4px 10px', borderRadius: 6, fontSize: 12 }}>{e}</span>
                    ))}
                  </div>
                </div>
              )}
              <details>
                <summary style={{ cursor: 'pointer', color: '#64748b', fontSize: 13 }}>Full AI JSON</summary>
                <pre className="result-box" style={{ fontSize: 11, maxHeight: 300, overflow: 'auto', marginTop: 8 }}>
                  {JSON.stringify(results.ai.analysis, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </ResultSection>
      )}

      {/* Plans Result */}
      {(results.plans || errors.plans) && (
        <ResultSection
          title="Plans / Pricing"
          icon={CreditCard}
          color="#fb923c"
          open={openSections.plans !== false}
          onToggle={() => toggleSection('plans')}
          badge={results.plans?.total_plans_found ? `${results.plans.total_plans_found} plans` : null}
        >
          {errors.plans ? (
            <div className="error-box">{errors.plans}</div>
          ) : (
            <div>
              {/* Plans cards */}
              {results.plans.all_plans?.length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12, marginBottom: 12 }}>
                  {results.plans.all_plans.map((plan, i) => (
                    <div key={i} style={{
                      background: plan.highlighted ? '#1e1b4b' : '#0f172a',
                      border: plan.highlighted ? '2px solid #a78bfa' : '1px solid #1e293b',
                      borderRadius: 10, padding: 16,
                    }}>
                      <div style={{ fontWeight: 700, fontSize: 16, color: '#e2e8f0' }}>{plan.name || `Plan ${i + 1}`}</div>
                      {plan.price && <div style={{ fontSize: 22, fontWeight: 800, color: '#fb923c', marginTop: 4 }}>{plan.price}</div>}
                      {plan.period && <div style={{ fontSize: 12, color: '#64748b' }}>{plan.period}</div>}
                      {plan.description && <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>{plan.description}</p>}
                      {plan.features?.length > 0 && (
                        <ul style={{ marginTop: 8, fontSize: 12, color: '#cbd5e1' }}>
                          {plan.features.slice(0, 6).map((f, j) => <li key={j}>{f}</li>)}
                          {plan.features.length > 6 && <li style={{ color: '#64748b' }}>+{plan.features.length - 6} more</li>}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Markdown */}
              {results.plans.markdown && (
                <details>
                  <summary style={{ cursor: 'pointer', color: '#64748b', fontSize: 13 }}>Plans Markdown</summary>
                  <div className="result-box" style={{ marginTop: 8 }}>
                    <ReactMarkdown>{results.plans.markdown}</ReactMarkdown>
                  </div>
                </details>
              )}
            </div>
          )}
        </ResultSection>
      )}

      {/* Extract Result */}
      {(results.extract || errors.extract) && (
        <ResultSection
          title="Extraction"
          icon={FileSearch}
          color="#c084fc"
          open={openSections.extract !== false}
          onToggle={() => toggleSection('extract')}
          badge={results.extract?.data ? `${Object.keys(results.extract.data).length} fields` : null}
        >
          {errors.extract ? (
            <div className="error-box">{errors.extract}</div>
          ) : (
            <div>
              <div className="kv-grid">
                {Object.entries(results.extract.data || {}).map(([k, v]) => (
                  <div key={k} className="kv-row">
                    <span className="kv-key">{k}</span>
                    <span className="kv-val">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 8 }}>
                <button className="btn btn-secondary btn-sm" onClick={() => handleCopy(JSON.stringify(results.extract.data, null, 2), 'extract')}>
                  {copied === 'extract' ? <Check size={14} /> : <Copy size={14} />} Copy JSON
                </button>
              </div>
            </div>
          )}
        </ResultSection>
      )}

      {/* Crawl Result */}
      {(results.crawl || errors.crawl) && (
        <ResultSection
          title="Crawl"
          icon={Bug}
          color="#4ade80"
          open={openSections.crawl !== false}
          onToggle={() => toggleSection('crawl')}
          badge={results.crawl?.completed != null ? `${results.crawl.completed}/${results.crawl.total} pages` : null}
        >
          {errors.crawl ? (
            <div className="error-box">{errors.crawl}</div>
          ) : (
            <div>
              <div className="stats-row" style={{ marginBottom: 12 }}>
                <div className="stat-card mini">
                  <div className="stat-label">Status</div>
                  <div className="stat-value" style={{ fontSize: 14, color: results.crawl.status === 'completed' ? '#22c55e' : '#fbbf24' }}>{results.crawl.status}</div>
                </div>
                <div className="stat-card mini">
                  <div className="stat-label">Pages</div>
                  <div className="stat-value" style={{ fontSize: 16 }}>{results.crawl.completed}/{results.crawl.total}</div>
                </div>
              </div>

              {results.crawl.pages?.length > 0 && (
                <div className="page-list">
                  {results.crawl.pages.slice(0, 20).map((p, i) => (
                    <div key={i} className="page-list-item">
                      <div>
                        <div className="page-title">{p.metadata?.title || p.url}</div>
                        <div className="page-url">{p.url}</div>
                      </div>
                      <span className={`page-status ${p.error ? 'error' : ''}`}>
                        {p.error ? 'Failed' : p.status_code || 'OK'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </ResultSection>
      )}

      {/* Spacer at bottom */}
      <div style={{ height: 40 }} />
    </>
  )
}
