const API_BASE = import.meta.env.VITE_API_URL || '';

export async function scrapeUrl(payload) {
  const res = await fetch(`${API_BASE}/v1/scrape`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Scrape failed');
  }
  return res.json();
}

export async function crawlUrl(payload) {
  const res = await fetch(`${API_BASE}/v1/crawl`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Crawl failed');
  }
  return res.json();
}

export async function extractData(payload) {
  const res = await fetch(`${API_BASE}/v1/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Extract failed');
  }
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function formatData(payload) {
  const res = await fetch(`${API_BASE}/v1/format`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Format failed');
  }
  return res.json();
}

export async function analyzeUrl(payload) {
  const res = await fetch(`${API_BASE}/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Analyze failed');
  }
  return res.json();
}

export async function deepScan(payload) {
  const res = await fetch(`${API_BASE}/v1/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Deep scan failed');
  }
  return res.json();
}
