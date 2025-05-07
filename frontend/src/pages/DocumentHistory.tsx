import React, { useEffect, useState } from 'react'
import { useParams, Link as RouterLink } from 'react-router-dom'
import {
  Box, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper,
  Button, IconButton, Dialog, DialogTitle,
  DialogContent, DialogActions, CircularProgress
} from '@mui/material'
import { Eye } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { useAuth } from '../context/AuthContext'
import { ProtectedImage } from "../components/ProtectedImage";
import { useAuthFetch } from '../utils/authFetch'
interface HistoryEntry {
  version:     number
  created_at:  string
  updated_at:  string
  created_by:  string
  title:       string
  content:     string
}

export default function DocumentHistory() {
  const { id } = useParams<{ id?: string }>()
  const { token } = useAuth()
  const [hist, setHist]     = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string>()
  const [open, setOpen]       = useState(false)
  const [sel, setSel]         = useState<HistoryEntry | null>(null)
  const authFetch = useAuthFetch()

  useEffect(() => {
    if (!id) return
    setLoading(true)
    authFetch(`http://127.0.0.1:8000/documents/${id}/history`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : Promise.reject(r.statusText))
      .then(setHist)
      .catch(e => setError(e as string))
      .finally(() => setLoading(false))
  }, [id, token])

  if (loading) return <Box textAlign="center"><CircularProgress/></Box>
  if (error)   return <Typography color="error">{error}</Typography>

  return (
    <>
      <Box mb={2} display="flex" alignItems="center">
        <Typography variant="h4" flexGrow={1}>
          Historique du document
        </Typography>
        <Button component={RouterLink} to="/documents">← Retour</Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Version</TableCell>
              <TableCell>Créé le</TableCell>
              <TableCell>Màj le</TableCell>
              <TableCell>Créé par</TableCell>
              <TableCell>Titre</TableCell>
              <TableCell align="right">Voir</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {hist.map(h => (
              <TableRow key={h.version}>
                <TableCell>{h.version}</TableCell>
                <TableCell>{new Date(h.created_at).toLocaleString()}</TableCell>
                <TableCell>{new Date(h.updated_at).toLocaleString()}</TableCell>
                <TableCell>{h.created_by}</TableCell>
                <TableCell>{h.title}</TableCell>
                <TableCell align="right">
                  <IconButton onClick={() => { setSel(h); setOpen(true) }}>
                    <Eye />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Version {sel?.version} — {sel?.title}
        </DialogTitle>
        <DialogContent dividers>
        <ReactMarkdown
  remarkPlugins={[remarkGfm]}
    skipHtml
   components={{
     img: ({ src = "", alt }) => (
      <ProtectedImage
         src={src.startsWith("/") ? `http://127.0.0.1:8000${src}` : src}
         alt={alt}
         style={{ display: "block", maxWidth: "100%", height: "auto", margin: "1em 0" }}
       />
     )
   }}
>
  {sel?.content || ""}
</ReactMarkdown>
</DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Fermer</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
