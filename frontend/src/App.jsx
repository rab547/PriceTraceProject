import {useState} from 'react';

function App() {
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('http://localhost:5000/upload', {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    setMessage(data.message || data.error)
  }

  return (
    <div>
      <h1>Upload a File</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleFileChange} />
        <button type="submit">Upload</button>
      </form>
      <p>{message}</p>
    </div>
  )
}

export default App
