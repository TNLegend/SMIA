import React, { useState, useEffect } from 'react';
import { useParams, Link as RouterLink, useNavigate } from 'react-router-dom';
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
  ListItemIcon,
  ListItemText,
  CircularProgress
} from '@mui/material';
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
  MessageCircle,
  FileText,
  Clock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import PieChart from '../components/charts/PieChart';

interface Comment {
  id: string;
  author: string;
  date: string;
  content: string;
}

interface Phase {
  name: string;
  status: 'completed' | 'in-progress' | 'pending';
  date: string;
}

interface Risk {
  id: string;
  category: string;
  description: string;
  level: 'low' | 'medium' | 'high';
  impact: number;
  probability: number;
  status: 'identified' | 'mitigated' | 'accepted';
  date: string;
  mitigation?: string;
}

interface AIData {
  type: string;
  model: string;
  framework: string;
  datasetSize: string;
  featuresCount: number;
  accuracy: number;
  trainingTime: string;
}

interface ProjectDetailAPI {
  id: string;
  title: string;
  description: string;
  category: string;
  owner: string;
  created: string;
  updated: string;
  status: 'draft' | 'active' | 'completed' | 'on-hold';
  riskLevel: 'low' | 'medium' | 'high';
  complianceScore: number;
  progress: number;
  domain: string;
  tags: string[];
  phases: Phase[];
  team: { name: string; role: string; avatar: string }[];
  risks: Risk[];
  comments: Comment[];
  aiDetails: AIData;
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token, logout } = useAuth();

  const [project, setProject] = useState<ProjectDetailAPI | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string>();
  const [tab, setTab]           = useState(0);
  const [newComment, setNew]    = useState('');

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/projects/${id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => {
        if (res.status === 401) {
          logout();
          throw new Error('Session expirée');
        }
        if (!res.ok) throw new Error(`Erreur ${res.status}`);
        return res.json();
      })
      .then((data: ProjectDetailAPI) => setProject(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [id, token, logout]);

  const addComment = async () => {
    if (!newComment.trim() || !project) return;
    const res = await fetch(
      `http://127.0.0.1:8000/projects/${id}/comments`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: newComment })
      }
    );
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) {
      const created = await res.json();
      setProject(p => p && ({ ...p, comments: [...p.comments, created] }));
      setNew('');
    }
  };

  if (loading) return <Box textAlign="center" py={4}><CircularProgress/></Box>;
  if (error)   return <Typography color="error" align="center" py={4}>{error}</Typography>;
  if (!project) return null;

  // Helpers
  const getRiskColor = (lvl: string) =>
    lvl === 'high'   ? 'error.main'
    : lvl === 'medium' ? 'warning.main'
    : 'success.main';

  const riskIcon = (lvl: string) =>
    lvl === 'high'   ? <ShieldAlert size={16}/>
    : lvl === 'medium' ? <AlertTriangle size={16}/>
    : <CheckCircle2 size={16}/>;


  return (
    <Box>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 1 }}>
        <Link component={RouterLink} to="/" sx={{ display: 'flex', alignItems: 'center' }}>
          <Home size={16} style={{ marginRight: 4 }} /> Accueil
        </Link>
        <Link component={RouterLink} to="/projects">Projets</Link>
        <Typography color="text.primary">{project.title}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box display="flex" alignItems="center">
          <Button
            component={RouterLink}
            to="/projects"
            variant="outlined"
            startIcon={<ArrowLeft size={18} />}
            sx={{ mr: 2 }}
          >
            Retour
          </Button>
          <Typography variant="h4" fontWeight={700}>{project.title}</Typography>
        </Box>
        <Box>
          <Button startIcon={<Download size={18} />} sx={{ mr: 1 }}>Exporter</Button>
          <Button startIcon={<Edit size={18} />} variant="contained">Modifier</Button>
        </Box>
      </Box>

      {/* Chips */}
      <Box display="flex" flexWrap="wrap" gap={1} mb={3}>
        <Chip label={project.category} size="small" color="primary" />
        <Chip label={project.status} size="small" />
        <Chip
          icon={riskIcon(project.riskLevel)}
          label={`Risque ${project.riskLevel}`}
          size="small"
          sx={{ color: getRiskColor(project.riskLevel) }}
        />
        <Chip
          label={`Conformité ${project.complianceScore}%`}
          size="small"
          sx={{ color: project.complianceScore >= 80 ? 'success.main' : project.complianceScore >= 60 ? 'warning.main' : 'error.main' }}
        />
      </Box>

      <Grid container spacing={3}>
        {/* Left */}
        <Grid item xs={12} md={8}>
          {/* Description + Progress */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Description</Typography>
              <Typography paragraph>{project.description}</Typography>

              <Typography variant="subtitle1" gutterBottom>Progression</Typography>
              <Box display="flex" alignItems="center">
                <Box flexGrow={1} mr={2}>
                  <LinearProgress
                    variant="determinate"
                    value={project.progress}
                    sx={{
                      height: 8,
                      borderRadius: 1,
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 1
                      }
                    }}
                  />
                </Box>
                <Typography>{project.progress}%</Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Phases */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Phases du projet</Typography>
              <Stepper orientation="vertical">
                {project.phases.map((ph, i) => (
                  <Step key={i} active={ph.status !== 'pending'} completed={ph.status === 'completed'}>
                    <StepLabel icon={ph.status === 'completed' ? <CheckCircle2 size={20} color="success"/> : ph.status === 'in-progress' ? <Activity size={20}/> : <Clock size={20}/>}>
                      <Box>
                        <Typography sx={{ fontWeight: ph.status === 'pending' ? 'regular' : 'medium' }}>
                          {ph.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="flex" alignItems="center">
                          <Calendar size={14} style={{ marginRight: 4 }}/>
                          {ph.date}
                        </Typography>
                      </Box>
                    </StepLabel>
                  </Step>
                ))}
              </Stepper>
            </CardContent>
          </Card>

          {/* Tabs: Risks / Comments / AI / History */}
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
                            <Chip icon={riskIcon(r.level)} label={r.level} size="small" />
                          </TableCell>
                          <TableCell>{r.category}</TableCell>
                          <TableCell>{r.description}</TableCell>
                          <TableCell>{r.impact}/5</TableCell>
                          <TableCell>{r.probability}/5</TableCell>
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
                <Box>
                  <Box mb={2}>
                    <TextField
                      label="Ajouter un commentaire"
                      multiline
                      rows={3}
                      fullWidth
                      value={newComment}
                      onChange={e => setNew(e.target.value)}
                    />
                    <Box textAlign="right" mt={1}>
                      <Button variant="contained" onClick={addComment}>Publier</Button>
                    </Box>
                  </Box>
                  <Divider sx={{ my: 2 }}/>
                  <List>
                    {project.comments.map(c => (
                      <ListItem key={c.id} alignItems="flex-start">
                        <ListItemIcon>
                          <Avatar>{c.author[0]}</Avatar>
                        </ListItemIcon>
                        <ListItemText
                          primary={c.author}
                          secondary={
                            <>
                              <Typography variant="caption" color="text.secondary" display="block">
                                {c.date}
                              </Typography>
                              <Typography>{c.content}</Typography>
                            </>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {tab === 2 && (
                <Box>
                  <Typography variant="h6" gutterBottom>Caractéristiques IA</Typography>
                  <Grid container spacing={2}>
                    {Object.entries(project.aiDetails).map(([k, v]) => (
                      <Grid item xs={12} sm={6} key={k}>
                        <Typography variant="subtitle2" color="text.secondary">{k}</Typography>
                        <Typography>{v}</Typography>
                      </Grid>
                    ))}
                  </Grid>
                  <Box mt={4}>
                    <PieChart
                      title="Conformité"
                      labels={['Conforme','Non conforme']}
                      data={[project.complianceScore, 100 - project.complianceScore]}
                      height={200}
                    />
                  </Box>
                </Box>
              )}

              {tab === 3 && (
                <List>
                  {/* …render your history items here… */}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right Sidebar */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Infos</Typography>
              <Typography><strong>Responsable:</strong> {project.owner}</Typography>
              <Typography><strong>Créé le:</strong> {project.created}</Typography>
              <Typography><strong>Mis à jour:</strong> {project.updated}</Typography>
              <Typography><strong>Domaine:</strong> {project.domain}</Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Équipe</Typography>
              <List>
                {project.team.map(m => (
                  <ListItem key={m.name}>
                    <Avatar sx={{ mr: 1 }}>{m.avatar}</Avatar>
                    <ListItemText primary={m.name} secondary={m.role} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
