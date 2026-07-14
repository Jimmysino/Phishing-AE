import { useState } from 'react'
import './App.css'

const API_URL = '[https://api-phishing-ia.onrender.com/predict](https://api-phishing-ia.onrender.com/predict)'

export default function App() {
  const [url, setUrl] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | result | error
  const [result, setResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  async function handleAnalyze() {
    const trimmed = url.trim()
    if (!trimmed) return

    setStatus('loading')
    setResult(null)
    setErrorMsg('')

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: trimmed }),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Error ${res.status}: ${text}`)
      }

      const data = await res.json()
      setResult(data)
      setStatus('result')
    } catch (err) {
      if (err.name === 'TypeError') {
        setErrorMsg('No se pudo conectar con el backend. Asegúrate de que esté corriendo en http://localhost:3000.')
      } else {
        setErrorMsg(err.message || 'Ocurrió un error inesperado.')
      }
      setStatus('error')
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleAnalyze()
  }

  const isPhishing = result?.is_phishing === 1
  const confidence = result?.confidence != null ? Math.round(result.confidence * 100) : null

  return (
    <div className="card">
      <header className="card-header">
        <div className="shield-icon" aria-hidden="true">
          {isPhishing && status === 'result' ? '⚠' : '🛡'}
        </div>
        <h1>Detector de Phishing con IA</h1>
        <p className="subtitle">Analiza cualquier URL en segundos para detectar amenazas de phishing.</p>
      </header>

      <div className="input-row">
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="https://ejemplo.com"
          className="url-input"
          disabled={status === 'loading'}
          aria-label="URL a analizar"
        />
        <button
          onClick={handleAnalyze}
          disabled={status === 'loading' || !url.trim()}
          className="analyze-btn"
        >
          {status === 'loading' ? (
            <span className="btn-inner">
              <span className="spinner" aria-hidden="true" />
              Analizando…
            </span>
          ) : (
            'Analizar'
          )}
        </button>
      </div>

      {status === 'loading' && (
        <div className="status-bar">
          <span className="pulse-dot" />
          Obteniendo y analizando el sitio, esto puede tomar unos segundos…
        </div>
      )}

      {status === 'result' && result && (
        <div className={`result-card ${isPhishing ? 'danger' : 'safe'}`}>
          <div className="result-icon">{isPhishing ? '🚨' : '✅'}</div>
          <div className="result-body">
            <p className="result-verdict">
              {isPhishing ? 'Sitio de Phishing Detectado' : 'Sitio Legítimo'}
            </p>
            <p className="result-desc">
              {isPhishing
                ? 'Este sitio web muestra señales de ser fraudulento. Evita ingresar datos personales.'
                : 'No se detectaron señales de phishing en este sitio.'}
            </p>
            {confidence != null && (
              <div className="confidence-row">
                <span className="confidence-label">Confianza del modelo</span>
                <div className="confidence-bar-wrap">
                  <div
                    className={`confidence-bar ${isPhishing ? 'bar-danger' : 'bar-safe'}`}
                    style={{ width: `${confidence}%` }}
                  />
                </div>
                <span className="confidence-pct">{confidence}%</span>
              </div>
            )}
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="error-card">
          <span className="error-icon">⚡</span>
          <p>{errorMsg}</p>
        </div>
      )}
    </div>
  )
}
