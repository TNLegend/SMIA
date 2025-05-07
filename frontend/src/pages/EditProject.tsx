// src/pages/EditProject.tsx
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box, Typography, Button, TextField, Grid,
  MenuItem, FormControl, InputLabel, Select,
  CircularProgress, Paper
} from '@mui/material'
import { ArrowLeft, Check, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

interface Payload {
  name: string
  description: string
  category: string
  status: 'draft'|'active'|'completed'|'on-hold'
}

export default function EditProject() {
  const { id } = useParams<{id:string}>()
  const { token, logout } = useAuth()
  const navigate = useNavigate()

  const [pl, setPl] = useState<Payload>({
    name: '', description: '', category: 'Marketing', status: 'draft'
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string|null>(null)

  // 1) fetch existing project
  useEffect(() => {
    fetch(`http://127.0.0.1:8000/projects/${id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => {
        if (r.status === 401) { logout(); throw new Error('Session expirée') }
        if (!r.ok) throw new Error(`Erreur ${r.status}`)
        return r.json()
      })
      .then(data => {
        setPl({
          name: data.name,
          description: data.description,
          category: data.category,
          status: data.status
        })
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id, token, logout])

  const handleChange = (e:any) =>
    setPl(p => ({ ...p, [e.target.name]: e.target.value }))

  // 2) submit PUT
  const submit = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`http://127.0.0.1:8000/projects/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type':'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(pl)
      })
      if (res.status === 401) { logout(); return }
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      navigate(`/projects/${data.id}`)
    } catch(err:any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={4}>
        <Button startIcon={<ArrowLeft/>}
                onClick={()=>navigate(-1)}
                sx={{mr:2}}>Retour</Button>
        <Typography variant="h4">Modifier le projet</Typography>
      </Box>

      <Paper sx={{p:4, position:'relative'}}>
        {loading && (
          <Box sx={{
            position:'absolute', inset:0, bgcolor:'rgba(255,255,255,0.7)',
            display:'flex', alignItems:'center', justifyContent:'center'
          }}>
            <CircularProgress/>
          </Box>
        )}
        {error && <Typography color="error" mb={2}>{error}</Typography>}

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              name="name" label="Nom du projet"
              fullWidth required
              value={pl.name} onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              name="description" label="Description"
              multiline rows={4} fullWidth required
              value={pl.description} onChange={handleChange}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth required>
              <InputLabel>Catégorie</InputLabel>
              <Select
                name="category" label="Catégorie"
                value={pl.category} onChange={handleChange}
              >
                <MenuItem value="Marketing">Marketing</MenuItem>
                <MenuItem value="Production">Production</MenuItem>
                <MenuItem value="Finance">Finance</MenuItem>
                <MenuItem value="Service client">Service client</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth required>
              <InputLabel>Statut</InputLabel>
              <Select
                name="status" label="Statut"
                value={pl.status} onChange={handleChange}
              >
                <MenuItem value="draft">Brouillon</MenuItem>
                <MenuItem value="active">Actif</MenuItem>
                <MenuItem value="completed">Terminé</MenuItem>
                <MenuItem value="on-hold">En pause</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <Box display="flex" justifyContent="flex-end" gap={2} mt={4}>
          <Button startIcon={<X/>}
                  disabled={loading}
                  onClick={()=>navigate(-1)}>
            Annuler
          </Button>
          <Button variant="contained"
                  endIcon={<Check/>}
                  disabled={loading}
                  onClick={submit}>
            Enregistrer
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}
