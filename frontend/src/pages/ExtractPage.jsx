import { useState, useCallback } from 'react'
import { FileSearch, Play, Copy, Check } from 'lucide-react'
import { extractData } from '../api'

const EXAMPLE_SCHEMA = JSON.stringify({
  title: 'h1',
  description: 'meta[name="description"]',
  links: { _list: true, selector: 'a' },
}, null, 2)

function saveHistory(entry) {
  try {
    const h = JSON.parse(localStorage.getItem('wv_history') || '[]')
    h.push(entry)
    if (h.length > 100) h.splice(0, h.length - 100)
    localStorage.setItem('wv_history', JSON.stringify(h))
  } catch {}
}

export default function ExtractPage() {
  const [url, setUrl] = useState('')
  const [schema, setSchema] = useState(EXAMPLE_SCHEMA)
  const [useBrowser, setUseBrowser] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [copied, setCopied] = useState(false)
  const [schemaError, setSchemaError] = useState(null)

  const handleExtract = useCallback(async () => {
    if (!url.trim()) return
    setSchemaError(null)

    let parsed
    try {
      parsed = JSON.parse(schema)
    } catch (e) {
      setSchemaError('Invalid JSON: ' + e.message)
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await extractData({
        url: url.trim(),
        schema: parsed,
        use_browser: useBrowser,
      })
      setResult(data)
      saveHistory({ type: 'extract', url: url.trim(), time: Date.now(), error: null })
    } catch (e) {
      setError(e.message)
      saveHistory({ type: 'extract', url: url.trim(), time: Date.now(), error: e.message })
    } finally {
      setLoading(false)
    }
  }, [url, schema, useBrowser])

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(result?.data, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <div className="page-header">
        <h1>Extract</h1>
        <p>Pull structured data from a page using CSS / XPath selectors</p>
      </div>

      <div className="card">
        <div className="card-header"><FileSearch size={16} /> Extraction Setup</div>

        <div className="form-group">
          <label>URL</label>
          <input
            className="input"
            placeholder="https://example.com"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleExtract()}
          />
        </div>

        <div className="form-group">
          <label>
            Schema (JSON)
            {schemaError && <span style={{ color: 'var(--error)', marginLeft: 12, fontWeight: 400 }}>{schemaError}</span>}
          </label>
          <textarea
            className="input"
            rows={8}
            value={schema}
            onChange={e => { setSchema(e.target.value); setSchemaError(null) }}
            style={{ minHeight: 150 }}
          />
        </div>

        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14, lineHeight: 1.6 }}>
          <strong>Selector syntax: </strong>
          <code style={{ background: 'var(--bg-input)', padding: '2px 6px', borderRadius: 4 }}>h1</code> CSS selector &middot;
          <code style={{ background: 'var(--bg-input)', padding: '2px 6px', borderRadius: 4 }}>{'{"_list": true, "selector": ".item"}'}</code> list &middot;
          <code style={{ background: 'var(--bg-input)', padding: '2px 6px', borderRadius: 4 }}>attr::.el::href</code> attribute &middot;
          <code style={{ background: 'var(--bg-input)', padding: '2px 6px', borderRadius: 4 }}>xpath::expr</code> XPath
        </div>

        <div className="toggle-group">
          <label className="toggle-label">
            <input type="checkbox" checked={useBrowser} onChange={e => setUseBrowser(e.target.checked)} />
            Use headless browser
          </label>
        </div>

        <button className="btn btn-primary" disabled={loading || !url.trim()} onClick={handleExtract}>
          {loading ? <><span className="spinner" /> Extracting…</> : <><Play size={16} /> Extract</>}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="card-header" style={{ margin: 0 }}>Extracted Data</div>
            <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
              {copied ? <><Check size={14} /> Copied</> : <><Copy size={14} /> Copy JSON</>}
            </button>
          </div>

          <div className="result-box">
            <pre className="json-display">{JSON.stringify(result.data, null, 2)}</pre>
          </div>
        </div>
      )}
    </>
  )
}
