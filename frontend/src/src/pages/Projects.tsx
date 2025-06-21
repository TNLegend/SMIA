import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Grid,
  Tabs,
  Tab,
  CircularProgress,
  useTheme,
  Pagination
} from '@mui/material'
import { Plus, Search, List as ListIcon, Grid as GridIcon } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import ProjectCard, { ProjectCardProps } from '../components/projects/ProjectCard'
import { useApi } from '../api/client'
import { useTeam } from '../context/TeamContext'

export default function Projects() {
  const theme = useTheme()
  const navigate = useNavigate()
  const { token, logout } = useAuth()
  const { teamId }        = useTeam()
  const [projects, setProjects] = useState<ProjectCardProps[]>([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState<string>()

  // UI controls
  const [search, setSearch]       = useState('')
  const [viewMode, setViewMode]   = useState<'grid'|'list'>('grid')
  const [tabValue, setTabValue]   = useState(0)
  const [page, setPage]           = useState(1)
  const perPage                   = 6
  const api = useApi();
   useEffect(() => {
    if (teamId == null) {           // ⇐ aucune équipe sélectionnée
      setLoading(false)
      return
    }
    api(`/projects?skip=${(page-1)*perPage}&limit=${perPage}`)
      .then(res => {
        if (res.status === 401) { logout(); throw new Error('Session expirée') }
        if (!res.ok) throw new Error(`Erreur ${res.status}`)
        return res.json()
      })
      .then((data: ProjectCardProps[]) => setProjects(data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [token, logout, page, teamId])

  // Reset to first page when search or tab changes
  useEffect(() => {
    setPage(1)
  }, [search, tabValue])

  const filtered = projects.filter(p => {
    if (tabValue === 1 && p.status !== 'active')    return false
    if (tabValue === 2 && p.status !== 'completed') return false
    if (tabValue === 3 && p.status !== 'on-hold')   return false
    if (search) {
      const q = search.toLowerCase()
      if (![p.title, p.description, p.category, p.owner]
            .some(f => f.toLowerCase().includes(q)))
        return false
    }
    return true
  })

  if (loading)   return <Box textAlign="center" py={4}><CircularProgress/></Box>
  if (teamId==null)
    return (
      <Typography color="text.secondary" align="center" py={4}>
        Sélectionnez d’abord une équipe (menu en‐haut à droite).
      </Typography>
    )
  if (error)   return <Typography color="error" align="center" py={4}>{error}</Typography>

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4">Projets IA</Typography>
        <Button
          variant="contained"
          startIcon={<Plus/>}
          onClick={()=>navigate('/projects/new')}
        >Nouveau projet</Button>
      </Box>

      <Box mb={2} display="flex" gap={2} flexWrap="wrap">
        <TextField
          placeholder="Rechercher…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          InputProps={{
            startAdornment: <InputAdornment position="start"><Search/></InputAdornment>
          }}
          sx={{ width: 300 }}
        />
        <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
          <Button
            variant={viewMode==='grid'?'contained':'outlined'}
            onClick={()=>setViewMode('grid')}
          ><GridIcon/></Button>
          <Button
            variant={viewMode==='list'?'contained':'outlined'}
            onClick={()=>setViewMode('list')}
          ><ListIcon/></Button>
        </Box>
      </Box>

      <Tabs value={tabValue} onChange={(_, v)=>setTabValue(v)} sx={{ mb:2 }}>
        <Tab label="Tous"/>
        <Tab label="Actifs"/>
        <Tab label="Terminés"/>
        <Tab label="En pause"/>
      </Tabs>

      <Grid container spacing={3}>
        {filtered.map(p => (
          <Grid
            item
            key={p.id}
            xs={12}
            sm={viewMode==='grid'?6:12}
            md={viewMode==='grid'?4:12}
          >
            <ProjectCard {...p}/>
          </Grid>
        ))}
      </Grid>

      {filtered.length === 0 && (
        <Box textAlign="center" py={8}>
          <Typography variant="h6">Aucun projet trouvé</Typography>
        </Box>
      )}

      {filtered.length > perPage && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Pagination
            count={Math.ceil(filtered.length / perPage)}
            page={page}
            onChange={(_, v) => setPage(v)}
            color="primary"
          />
        </Box>
      )}
    </Box>
  )
}
