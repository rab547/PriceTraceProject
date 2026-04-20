import { useState } from 'react'
import './App.css'

const API = 'http://localhost:5001'

function ResultsGrid({ results }) {
  if (results.length === 0) {
    return <p>No similar images found above the similarity threshold.</p>
  }
  return (
    <div className="results-grid">
      {results.map((r, i) => (
        <div className="result-card" key={i}>
          <img
            src={`${API}/image?path=${encodeURIComponent(r.image_path)}`}
            alt={`Result ${i + 1}`}
          />
          <div className="similarity">{(r.similarity * 100).toFixed(1)}% match</div>
        </div>
      ))}
    </div>
  )
}

function UploadTab() {
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    formData.append('use_dino', 'false')
    const res = await fetch(`${API}/upload`, { method: 'POST', body: formData })
    const data = await res.json()
    setMessage(data.message || data.error)
  }

  return (
    <div>
      <h2>Index an Image</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="image/*" onChange={e => setFile(e.target.files[0])} />
        <button type="submit">Upload</button>
      </form>
      {message && <p>{message}</p>}
    </div>
  )
}

function SearchTab() {
  const [file, setFile] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setError('')
    setResults(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('k', '10')
      formData.append('min_similarity', '0.5')
      const res = await fetch(`${API}/search`, { method: 'POST', body: formData })
      const data = await res.json()
      if (data.error) {
        setError(data.error)
      } else {
        setResults(data.results)
      }
    } catch {
      setError('Failed to connect to backend.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Search by Image</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="image/*" onChange={e => setFile(e.target.files[0])} />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {results !== null && <ResultsGrid results={results} />}
    </div>
  )
}

function App() {
  const [tab, setTab] = useState('upload')

  return (
    <div style={{ padding: '32px', maxWidth: '960px', margin: '0 auto' }}>
      <h1>PriceTrace Visual Search</h1>
      <div className="tabs">
        <button className={`tab-btn${tab === 'upload' ? ' active' : ''}`} onClick={() => setTab('upload')}>
          Upload
        </button>
        <button className={`tab-btn${tab === 'search' ? ' active' : ''}`} onClick={() => setTab('search')}>
          Search
        </button>
      </div>
      {tab === 'upload' ? <UploadTab /> : <SearchTab />}
    </div>
  )
}

export default App
