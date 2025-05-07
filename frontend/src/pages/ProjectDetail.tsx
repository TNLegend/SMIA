import React, { useState, useEffect } from 'react'
import { useParams, Link as RouterLink, useNavigate } from 'react-router-dom'
import {
  Box,
  Breadcrumbs,
  Link,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TableContainer,
  Divider,
  Avatar,
  Tabs,
  Tab,
  TextField,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  CircularProgress,
  Chip
} from '@mui/material'
import {
  Home,
  ArrowLeft,
  Download,
  Edit,
  Calendar,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Activity,
  FileText,
  Clock
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import PieChart from '../components/charts/PieChart'

/** Types matching the JSON you expect from your /projects/:id endpoint */
interface Phase {
  name: string
  status: 'pending' | 'in-progress' | 'completed'
  date:   string
}

interface Risk {
  id:          string
  category:    string
  description: string
  level:       'low' | 'medium' | 'high'
  impact:      number
  probability: number
  status:      'identified' | 'mitigated' | 'accepted'
  date:        string
  mitigation?: string
}

interface Comment {
  id:      string
  author:  string
  date:    string
  content: string
}

interface AIData {
  type:          string
  model:         string
  framework:     string
  datasetSize:   string
  featuresCount: number
  accuracy:      number
  trainingTime:  string
}

interface ProjectDetailAPI {
  id:              string
  title:           string
  description:     string
  category:        string
  owner:           string
  created:         string
  updated:         string
  status:          'draft' | 'active' | 'completed' | 'on-hold'
  riskLevel:       'low' | 'medium' | 'high'
  complianceScore: number
  progress:        number
  domain:          string
  tags:            string[]
  phases:          Phase[]
  team:            { name: string; role: string; avatar: string }[]
  risks:           Risk[]
  comments:        Comment[]
  aiDetails:       AIData
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { token, logout } = useAuth()

  const [project, setProject] = useState<ProjectDetailAPI | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()
  const [tab, setTab] = useState(0)
  const [newComment, setNewComment] = useState('')

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/projects/${id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => {
        if (res.status === 401) {
          logout()
          throw new Error('Session expirée')
        }
        if (!res.ok) throw new Error(`Erreur ${res.status}`)
        return res.json()
      })
      .then((data: ProjectDetailAPI) => setProject(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [id, token, logout])

  const addComment = async () => {
    if (!newComment.trim() || !project) return
    const res = await fetch(
      `http://127.0.0.1:8000/projects/${id}/comments`, // ← you need to implement this endpoint
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: newComment })
      }
    )
    if (res.status === 401) {
      logout()
      return
    }
    if (res.ok) {
      const created: Comment = await res.json()
      setProject(p => p && { ...p, comments: [...p.comments, created] })
      setNewComment('')
    }
  }

  if (loading)
    return <Box textAlign="center" py={4}><CircularProgress/></Box>
  if (error)
    return <Typography color="error" align="center" py={4}>{error}</Typography>
  if (!project) return null

  const getRiskIcon = (lvl: ProjectDetailAPI['riskLevel']) =>
    lvl === 'high'    ? <ShieldAlert size={16}/>
    : lvl === 'medium'? <AlertTriangle size={16}/>
                       : <CheckCircle2 size={16}/>

  return (
    <Box>
      {/* Breadcrumb */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link component={RouterLink} to="/" sx={{ display:'flex', alignItems:'center' }}>
          <Home size={16} style={{ marginRight:4 }} /> Accueil
        </Link>
        <Link component={RouterLink} to="/projects">Projets</Link>
        <Typography color="text.primary">{project.title}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <Button
            component={RouterLink}
            to="/projects"
            variant="outlined"
            startIcon={<ArrowLeft size={18}/>}
            sx={{ mr:2 }}
          >
            Retour
          </Button>
          <Typography variant="h4">{project.title}</Typography>
        </Box>
        <Box>
          <Button startIcon={<Download size={18}/>}>Exporter</Button>
          <Button
            startIcon={<Edit size={18}/>}
            variant="contained"
            sx={{ ml:1 }}
            onClick={() => navigate(`/projects/${id}/edit`)}
          >
            Modifier
          </Button>
        </Box>
      </Box>

      {/* Chips */}
      <Box display="flex" flexWrap="wrap" gap={1} mb={3}>
        <Chip label={project.category} size="small" color="primary"/>
        <Chip label={project.status} size="small"/>
        <Chip icon={getRiskIcon(project.riskLevel)} label={`Risque ${project.riskLevel}`} size="small"/>
        <Chip label={`Conformité ${project.complianceScore}%`} size="small"/>
      </Box>

      <Grid container spacing={3}>
        {/* Left column */}
        <Grid item xs={12} md={8}>

          {/* Description + progress */}
          <Card sx={{ mb:3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Description</Typography>
              <Typography paragraph>{project.description}</Typography>
              <Typography variant="subtitle1" gutterBottom>Progression</Typography>
              <Box display="flex" alignItems="center">
                <Box flexGrow={1} mr={2}>
                  <LinearProgress variant="determinate" value={project.progress} />
                </Box>
                <Typography>{project.progress}%</Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Phases */}
          <Card sx={{ mb:3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Phases du projet</Typography>
              <Stepper orientation="vertical">
                {project.phases.map((ph, i) => (
                  <Step
                    key={i}
                    active={ph.status !== 'pending'}
                    completed={ph.status === 'completed'}
                  >
                    <StepLabel
                      icon={
                        ph.status === 'completed'     ? <CheckCircle2 size={20} color="success" />
                        : ph.status === 'in-progress'  ? <Activity size={20}/>
                        : <Clock size={20}/>
                      }
                    >
                      <Box>
                        <Typography
                          sx={{ fontWeight: ph.status === 'pending' ? 'regular' : 'medium' }}
                        >
                          {ph.name}
                        </Typography>
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          display="flex"
                          alignItems="center"
                        >
                          <Calendar size={14} style={{ marginRight:4 }}/>
                          {ph.date}
                        </Typography>
                      </Box>
                    </StepLabel>
                  </Step>
                ))}
              </Stepper>
            </CardContent>
          </Card>

          {/* Tabs: risks / comments / IA details / history */}
          <Card>
            <Tabs value={tab} onChange={(_, v) => setTab(v)}>
              <Tab label="Risques"/>
              <Tab label="Commentaires"/>
              <Tab label="Détails IA"/>
              <Tab label="Historique"/>
            </Tabs>
            <Divider/>
            <CardContent>
              {tab === 0 && (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Niveau</TableCell>
                        <TableCell>Catégorie</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>Impact</TableCell>
                        <TableCell>Probabilité</TableCell>
                        <TableCell>Statut</TableCell>
                        <TableCell>Date</TableCell>
                        <TableCell>Action</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {project.risks.map(r => (
                        <TableRow key={r.id}>
                          <TableCell>
                            <Chip icon={getRiskIcon(r.level)} label={r.level} size="small"/>
                          </TableCell>
                          <TableCell>{r.category}</TableCell>
                          <TableCell>{r.description}</TableCell>
                          <TableCell>{r.impact}</TableCell>
                          <TableCell>{r.probability}</TableCell>
                          <TableCell>{r.status}</TableCell>
                          <TableCell>{r.date}</TableCell>
                          <TableCell><FileText size={16}/></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {tab === 1 && (
                <>
                  <Box mb={2}>
                    <TextField
                      label="Ajouter un commentaire"
                      multiline
                      rows={3}
                      fullWidth
                      value={newComment}
                      onChange={e => setNewComment(e.target.value)}
                    />
                    <Box textAlign="right" mt={1}>
                      <Button variant="contained" onClick={addComment}>
                        Publier
                      </Button>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 2 }}/>
                  <List>
                    {project.comments.map(c => (
                      <ListItem key={c.id} alignItems="flex-start">
                        <ListItemAvatar>
                          <Avatar>{c.author.charAt(0)}</Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={c.author}
                          secondary={
                            <>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                display="block"
                              >
                                {c.date}
                              </Typography>
                              {c.content}
                            </>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}

              {tab === 2 && (
                <Box>
                  <Typography variant="h6" gutterBottom>Détails IA</Typography>
                  <Grid container spacing={2}>
                    {Object.entries(project.aiDetails).map(([k, v]) => (
                      <Grid item xs={12} sm={6} key={k}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {k}
                        </Typography>
                        <Typography>{v as string}</Typography>
                      </Grid>
                    ))}
                  </Grid>
                  <Box mt={4}>
                    <PieChart
                      title="Conformité"
                      labels={['OK', 'Écart']}
                      data={[project.complianceScore, 100 - project.complianceScore]}
                      height={200}
                    />
                  </Box>
                </Box>
              )}

              {tab === 3 && (
                <Typography>Pas encore d’historique à afficher.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb:3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Informations</Typography>
              <Typography><strong>Responsable :</strong> {project.owner}</Typography>
              <Typography><strong>Créé le :</strong> {project.created}</Typography>
              <Typography><strong>MàJ :</strong> {project.updated}</Typography>
              <Typography><strong>Domaine :</strong> {project.domain}</Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Équipe</Typography>
              <List>
                {project.team.map(m => (
                  <ListItem key={m.name}>
                    <ListItemAvatar>
                      <Avatar>{m.avatar}</Avatar>
                    </ListItemAvatar>
                    <ListItemText primary={m.name} secondary={m.role} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
