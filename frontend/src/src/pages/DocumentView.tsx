import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box, Button, Typography, Paper, CircularProgress
} from '@mui/material'
import { ArrowLeft, Edit, History, Download } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useAuth } from '../context/AuthContext'
import { ProtectedImage } from '../components/ProtectedImage'
import { useApi } from '../api/client'

interface Document {
  id: number
  title: string
  content: string
  version: number
  created_at: string
  updated_at: string
  created_by: string
}

export default function DocumentView() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuth()
  const nav = useNavigate()

  const [doc, setDoc] = useState<Document | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()
  const api = useApi()


  useEffect(() => {
    if (!id) return
    api(`/documents/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include'
    })
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(setDoc)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [id, token])

  const downloadPdf = async () => {
    if (!doc) return
    const res = await api(
      `/documents/${doc.id}/download-pdf`,
      { headers: { Authorization: `Bearer ${token}` }, credentials: 'include' }
    )
    if (!res.ok) throw new Error(await res.text())
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${doc.title}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  if (loading) return <CircularProgress />
  if (error)   return <Typography color="error">{error}</Typography>
  if (!doc)    return <Typography>Aucun document trouvé.</Typography>

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={2}>
        <Button startIcon={<ArrowLeft />} onClick={() => nav('/documents')}>
          Retour
        </Button>
        <Typography variant="h4" ml={2}>{doc.title}</Typography>
      </Box>
      <Box mb={2}>
        <Button onClick={() => nav(`/documents/${doc.id}/edit`)} startIcon={<Edit />}>Modifier</Button>
        <Button onClick={() => nav(`/documents/${doc.id}/history`)} startIcon={<History />}>Historique</Button>
        <Button onClick={downloadPdf} startIcon={<Download />}>Télécharger PDF</Button>
      </Box>
      <Paper sx={{ p:3 }}>
        <Typography variant="caption">
          Version {doc.version} — créé par {doc.created_by} le {new Date(doc.created_at).toLocaleString()}
        </Typography>
        <Box mt={2}>
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
            img: ({ src="", alt }) => (
              <ProtectedImage
                src={src}
                alt={alt} style={{ display:'block', maxWidth:'100%', margin:'1em 0' }}
              />
            )
          }}>
            {doc.content}
          </ReactMarkdown>
        </Box>
      </Paper>
    </Box>
  )
}
