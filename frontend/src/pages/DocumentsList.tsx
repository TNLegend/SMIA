import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Button, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, IconButton,
  CircularProgress
} from '@mui/material'
import { Plus, Eye, Edit, Trash2, History } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useAuthFetch } from '../utils/authFetch'

interface Document {
  id: number
  title: string
  version: number
  created_at: string
  updated_at: string
  created_by: string
}

export default function DocumentsList() {
  const [docs, setDocs] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>()
  const { token } = useAuth()
  const nav = useNavigate()
  const authFetch = useAuthFetch()
  const load = async () => {
    setLoading(true)
    try {
      const res = await authFetch('http://127.0.0.1:8000/documents/', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) throw new Error(await res.text())
      setDocs(await res.json())
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [token])

  const del = async (id: number) => {
    if (!confirm('Supprimer ce document ?')) return
    await authFetch(`http://127.0.0.1:8000/documents/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` }
    })
    setDocs(docs.filter(d => d.id !== id))
  }

  if (loading) return <Box textAlign="center" mt={4}><CircularProgress/></Box>
  if (error)   return <Typography color="error">{error}</Typography>

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb={2}>
        <Typography variant="h4">Documents</Typography>
        <Button
          variant="contained"
          startIcon={<Plus size={18}/>} 
          onClick={() => nav('/documents/new')}
        >
          Nouveau document
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Titre</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Créé le</TableCell>
              <TableCell>Màj le</TableCell>
              <TableCell>Créé par</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {docs.map(d => (
              <TableRow key={d.id}>
                <TableCell>{d.title}</TableCell>
                <TableCell>{d.version}</TableCell>
                <TableCell>{new Date(d.created_at).toLocaleString()}</TableCell>
                <TableCell>{new Date(d.updated_at).toLocaleString()}</TableCell>
                <TableCell>{d.created_by}</TableCell>
                <TableCell align="right">
                  <IconButton onClick={() => nav(`/documents/${d.id}`)}>
                    <Eye size={16}/>
                  </IconButton>
                  <IconButton onClick={() => nav(`/documents/${d.id}/edit`)}>
                    <Edit size={16}/>
                  </IconButton>
                  <IconButton onClick={() => nav(`/documents/${d.id}/history`)}>
                    <History size={16}/>
                  </IconButton>
                  <IconButton onClick={() => del(d.id)}>
                    <Trash2 size={16}/>
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
