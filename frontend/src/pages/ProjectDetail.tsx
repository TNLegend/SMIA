import { useState } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Tabs,
  Tab,
  Divider,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Paper,
  LinearProgress,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Rating,
  Tooltip,
  useTheme,
  Breadcrumbs,
  Link,
  StepLabel,
  Step,
  Stepper
} from '@mui/material';
import { 
  FileSearch, 
  User, 
  Calendar, 
  Tag, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle,
  FileBarChart2,
  Edit,
  ArrowLeft,
  Home,
  Activity,
  History,
  Download,
  MessageCircle,
  Clock,
  FileText,
  Eye
} from 'lucide-react';
import PieChart from '../components/charts/PieChart';

interface Comment {
  id: string;
  author: string;
  date: string;
  content: string;
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

const projectData = {
  id: '1',
  title: 'Système de recommandation client',
  description: 'Ce système utilise l\'intelligence artificielle pour recommander des produits aux clients en fonction de leur historique d\'achats, de leur comportement de navigation et de leurs préférences. Il vise à améliorer l\'expérience client et à augmenter les ventes croisées.',
  category: 'Marketing',
  owner: 'Marie Laurent',
  created: '15/04/2025',
  updated: '02/05/2025',
  status: 'active',
  riskLevel: 'medium',
  complianceScore: 78,
  progress: 65,
  domain: 'B2C',
  tags: ['Machine Learning', 'Recommandation', 'Données client'],
  phases: [
    { name: 'Définition et planification', status: 'completed', date: '15/04/2025' },
    { name: 'Collecte et préparation des données', status: 'completed', date: '22/04/2025' },
    { name: 'Développement du modèle', status: 'in-progress', date: '02/05/2025' },
    { name: 'Test et évaluation', status: 'pending', date: '-' },
    { name: 'Déploiement', status: 'pending', date: '-' },
    { name: 'Monitoring et amélioration', status: 'pending', date: '-' },
  ],
  team: [
    { name: 'Marie Laurent', role: 'Chef de projet', avatar: 'ML' },
    { name: 'Thomas Dubois', role: 'Data Scientist', avatar: 'TD' },
    { name: 'Julie Martin', role: 'Développeur IA', avatar: 'JM' },
    { name: 'Éric Blanc', role: 'Spécialiste marketing', avatar: 'EB' },
  ],
  risks: [
    {
      id: 'risk1',
      category: 'Biais et discrimination',
      description: 'Risque de recommandations biaisées pour certains segments de clientèle',
      level: 'medium',
      impact: 3,
      probability: 4,
      status: 'identified',
      date: '20/04/2025',
    },
    {
      id: 'risk2',
      category: 'Transparence',
      description: 'Manque d\'explicabilité des recommandations proposées',
      level: 'medium',
      impact: 3,
      probability: 4,
      status: 'mitigated',
      date: '22/04/2025',
      mitigation: 'Implémentation d\'un module d\'explication des recommandations',
    },
    {
      id: 'risk3',
      category: 'Vie privée',
      description: 'Utilisation de données personnelles sensibles sans consentement explicite',
      level: 'high',
      impact: 4,
      probability: 3,
      status: 'mitigated',
      date: '25/04/2025',
      mitigation: 'Révision du processus de consentement et anonymisation des données',
    },
  ],
  comments: [
    {
      id: 'comment1',
      author: 'Sophie Renard',
      date: '02/05/2025',
      content: 'Excellents progrès sur le développement du modèle. La précision des recommandations s\'est améliorée de 15% avec la nouvelle approche.',
    },
    {
      id: 'comment2',
      author: 'Thomas Dubois',
      date: '28/04/2025',
      content: 'Le module d\'explication des recommandations est maintenant fonctionnel. Chaque recommandation est accompagnée d\'une brève explication pour l\'utilisateur.',
    },
    {
      id: 'comment3',
      author: 'Julie Martin',
      date: '25/04/2025',
      content: 'Les mesures d\'atténuation des risques liés à la vie privée ont été implémentées. Toutes les données sont maintenant anonymisées avant traitement.',
    },
  ],
  aiDetails: {
    type: 'Apprentissage supervisé',
    model: 'Réseau de neurones collaboratif',
    framework: 'TensorFlow',
    datasetSize: '1.2 To',
    featuresCount: 48,
    accuracy: 87,
    trainingTime: '72 heures',
  },
};

const ProjectDetail = () => {
  const theme = useTheme();
  const { id } = useParams<{ id: string }>();
  const [tabValue, setTabValue] = useState(0);
  const [commentText, setCommentText] = useState('');
  
  const handleChangeTab = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  const handleAddComment = () => {
    // Add comment logic
    setCommentText('');
  };
  
  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'high':
        return theme.palette.error.main;
      case 'medium':
        return theme.palette.warning.main;
      case 'low':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };
  
  const getRiskLevelIcon = (level: string) => {
    switch (level) {
      case 'high':
        return <ShieldAlert size={16} />;
      case 'medium':
        return <AlertTriangle size={16} />;
      case 'low':
        return <CheckCircle2 size={16} />;
      default:
        return null;
    }
  };
  
  const getPhaseStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={20} color={theme.palette.success.main} />;
      case 'in-progress':
        return <Activity size={20} color={theme.palette.primary.main} />;
      case 'pending':
        return <Clock size={20} color={theme.palette.grey[400]} />;
      default:
        return null;
    }
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.palette.success.main;
      case 'completed':
        return theme.palette.primary.main;
      case 'on-hold':
        return theme.palette.warning.main;
      default:
        return theme.palette.grey[500];
    }
  };
  
  const complianceData = {
    labels: ['Conforme', 'Écarts mineurs', 'Écarts majeurs'],
    data: [projectData.complianceScore, 15, 7],
    colors: [theme.palette.success.main, theme.palette.warning.main, theme.palette.error.main],
  };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Breadcrumbs sx={{ mb: 1 }}>
          <Link 
            component={RouterLink} 
            to="/" 
            color="inherit" 
            sx={{ 
              display: 'flex', 
              alignItems: 'center',
              '&:hover': { color: theme.palette.primary.main }
            }}
          >
            <Home size={16} style={{ marginRight: 4 }} />
            Accueil
          </Link>
          <Link 
            component={RouterLink} 
            to="/projects" 
            color="inherit"
            sx={{ 
              display: 'flex', 
              alignItems: 'center',
              '&:hover': { color: theme.palette.primary.main }
            }}
          >
            <FileSearch size={16} style={{ marginRight: 4 }} />
            Projets
          </Link>
          <Typography color="text.primary">
            {projectData.title}
          </Typography>
        </Breadcrumbs>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button 
              component={RouterLink} 
              to="/projects"
              variant="outlined" 
              startIcon={<ArrowLeft size={18} />}
              sx={{ mr: 2 }}
            >
              Retour
            </Button>
            <Typography variant="h4" fontWeight={700}>
              {projectData.title}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button 
              variant="outlined" 
              startIcon={<Download size={18} />}
            >
              Exporter
            </Button>
            <Button 
              variant="contained" 
              startIcon={<Edit size={18} />}
            >
              Modifier
            </Button>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
          <Chip 
            label={projectData.category} 
            size="small" 
            sx={{ 
              borderRadius: '4px',
              backgroundColor: theme.palette.primary.main,
              color: '#fff',
              fontWeight: 500,
            }} 
          />
          
          <Chip 
            label={projectData.status} 
            size="small" 
            sx={{ 
              borderRadius: '4px',
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.1)' 
                : 'rgba(0, 0, 0, 0.1)',
              color: getStatusColor(projectData.status),
              fontWeight: 500,
            }} 
          />
          
          <Chip 
            icon={getRiskLevelIcon(projectData.riskLevel)}
            label={`Risque ${projectData.riskLevel}`} 
            size="small" 
            sx={{ 
              borderRadius: '4px',
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.1)' 
                : 'rgba(0, 0, 0, 0.1)',
              color: getRiskLevelColor(projectData.riskLevel),
              fontWeight: 500,
              '& .MuiChip-icon': {
                color: getRiskLevelColor(projectData.riskLevel),
              },
            }} 
          />
          
          <Chip 
            label={`Conformité ${projectData.complianceScore}%`} 
            size="small" 
            sx={{ 
              borderRadius: '4px',
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.1)' 
                : 'rgba(0, 0, 0, 0.1)',
              color: projectData.complianceScore >= 80 
                ? theme.palette.success.main 
                : projectData.complianceScore >= 60 
                  ? theme.palette.warning.main 
                  : theme.palette.error.main,
              fontWeight: 500,
            }} 
          />
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        {/* Project Info */}
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Description
              </Typography>
              <Typography paragraph>
                {projectData.description}
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom fontWeight={600}>
                  Progression
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ flexGrow: 1, mr: 2 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={projectData.progress} 
                      sx={{ 
                        height: 8,
                        borderRadius: 5,
                        backgroundColor: theme.palette.mode === 'dark' 
                          ? 'rgba(255, 255, 255, 0.1)' 
                          : 'rgba(0, 0, 0, 0.1)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: theme.palette.primary.main,
                          borderRadius: 5,
                        }
                      }}
                    />
                  </Box>
                  <Typography variant="body2" fontWeight={500}>
                    {projectData.progress}%
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" gutterBottom fontWeight={600}>
                  Phases du projet
                </Typography>
                <Stepper orientation="vertical" sx={{ mt: 2 }}>
                  {projectData.phases.map((phase, index) => (
                    <Step key={phase.name} active={phase.status !== 'pending'} completed={phase.status === 'completed'}>
                      <StepLabel 
                        StepIconComponent={() => getPhaseStatusIcon(phase.status)}
                      >
                        <Box>
                          <Typography 
                            variant="body1" 
                            sx={{ 
                              fontWeight: 500,
                              color: phase.status === 'pending' 
                                ? theme.palette.text.disabled
                                : theme.palette.text.primary
                            }}
                          >
                            {phase.name}
                          </Typography>
                          <Typography 
                            variant="caption" 
                            color="text.secondary"
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                            }}
                          >
                            <Calendar size={14} style={{ marginRight: 4 }} />
                            {phase.date}
                          </Typography>
                        </Box>
                      </StepLabel>
                    </Step>
                  ))}
                </Stepper>
              </Box>
            </CardContent>
          </Card>
          
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={tabValue} 
                onChange={handleChangeTab}
                sx={{
                  px: 2,
                  '& .MuiTab-root': {
                    textTransform: 'none',
                    fontWeight: 500,
                    fontSize: '0.875rem',
                    minWidth: 'auto',
                    px: 2,
                  },
                }}
              >
                <Tab label="Risques" />
                <Tab label="Commentaires" />
                <Tab label="Détails IA" />
                <Tab label="Historique" />
              </Tabs>
            </Box>
            
            <CardContent>
              {/* Risks Tab */}
              {tabValue === 0 && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle1" fontWeight={600}>
                      Risques identifiés
                    </Typography>
                    <Button 
                      variant="outlined" 
                      size="small" 
                      startIcon={<ShieldAlert size={16} />}
                    >
                      Ajouter un risque
                    </Button>
                  </Box>
                  
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Niveau</TableCell>
                          <TableCell>Catégorie</TableCell>
                          <TableCell>Description</TableCell>
                          <TableCell align="center">Impact</TableCell>
                          <TableCell align="center">Probabilité</TableCell>
                          <TableCell>Statut</TableCell>
                          <TableCell>Date</TableCell>
                          <TableCell align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {projectData.risks.map((risk) => (
                          <TableRow key={risk.id}>
                            <TableCell>
                              <Chip 
                                icon={getRiskLevelIcon(risk.level)}
                                label={
                                  risk.level === 'high' ? 'Élevé' :
                                  risk.level === 'medium' ? 'Moyen' : 'Faible'
                                } 
                                size="small" 
                                sx={{ 
                                  backgroundColor: theme.palette.mode === 'dark' 
                                    ? 'rgba(255, 255, 255, 0.05)' 
                                    : 'rgba(0, 0, 0, 0.05)',
                                  color: getRiskLevelColor(risk.level),
                                  fontWeight: 500,
                                  '& .MuiChip-icon': {
                                    color: getRiskLevelColor(risk.level),
                                  },
                                }} 
                              />
                            </TableCell>
                            <TableCell>{risk.category}</TableCell>
                            <TableCell>
                              <Tooltip title={risk.description} arrow>
                                <Typography
                                  variant="body2"
                                  sx={{
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    display: '-webkit-box',
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient: 'vertical',
                                    maxWidth: 200,
                                  }}
                                >
                                  {risk.description}
                                </Typography>
                              </Tooltip>
                              {risk.mitigation && (
                                <Tooltip title={risk.mitigation} arrow>
                                  <Typography
                                    variant="caption"
                                    color="success.main"
                                    sx={{
                                      display: 'block',
                                      mt: 0.5,
                                      fontStyle: 'italic',
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap',
                                      maxWidth: 200,
                                    }}
                                  >
                                    {risk.mitigation}
                                  </Typography>
                                </Tooltip>
                              )}
                            </TableCell>
                            <TableCell align="center">
                              <Rating 
                                value={risk.impact} 
                                readOnly 
                                max={5}
                                size="small"
                                icon={<AlertTriangle size={14} style={{ color: theme.palette.warning.main }} />}
                                emptyIcon={<AlertTriangle size={14} style={{ color: theme.palette.divider }} />}
                              />
                            </TableCell>
                            <TableCell align="center">
                              <Rating 
                                value={risk.probability} 
                                readOnly 
                                max={5}
                                size="small"
                              />
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={
                                  risk.status === 'identified' ? 'Identifié' :
                                  risk.status === 'mitigated' ? 'Mitigé' : 'Accepté'
                                } 
                                size="small" 
                                sx={{ 
                                  height: 20,
                                  backgroundColor: theme.palette.mode === 'dark' 
                                    ? 'rgba(255, 255, 255, 0.05)' 
                                    : 'rgba(0, 0, 0, 0.05)',
                                  color: risk.status === 'mitigated' 
                                    ? theme.palette.success.main 
                                    : risk.status === 'accepted'
                                      ? theme.palette.info.main
                                      : theme.palette.error.main,
                                  fontWeight: 500,
                                }} 
                              />
                            </TableCell>
                            <TableCell>{risk.date}</TableCell>
                            <TableCell align="right">
                              <IconButton size="small">
                                <Eye size={16} />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              {/* Comments Tab */}
              {tabValue === 1 && (
                <Box>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      Ajouter un commentaire
                    </Typography>
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      placeholder="Écrivez votre commentaire ici..."
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      sx={{ mb: 1 }}
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <Button 
                        variant="contained"
                        disabled={!commentText}
                        onClick={handleAddComment}
                      >
                        Publier
                      </Button>
                    </Box>
                  </Box>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Commentaires récents
                  </Typography>
                  
                  {projectData.comments.map((comment) => (
                    <Box 
                      key={comment.id} 
                      sx={{ 
                        mb: 3, 
                        p: 2, 
                        backgroundColor: theme.palette.mode === 'dark' 
                          ? 'rgba(255, 255, 255, 0.03)' 
                          : 'rgba(0, 0, 0, 0.02)',
                        borderRadius: 1,
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar 
                            sx={{ 
                              width: 32, 
                              height: 32, 
                              mr: 1, 
                              bgcolor: theme.palette.primary.main 
                            }}
                          >
                            {comment.author.charAt(0)}
                          </Avatar>
                          <Typography variant="subtitle2" fontWeight={500}>
                            {comment.author}
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          <Calendar size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                          {comment.date}
                        </Typography>
                      </Box>
                      <Typography variant="body2">
                        {comment.content}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
              
              {/* AI Details Tab */}
              {tabValue === 2 && (
                <Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Caractéristiques techniques
                  </Typography>
                  
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Type d'algorithme
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {projectData.aiDetails.type}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Modèle
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {projectData.aiDetails.model}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Framework
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {projectData.aiDetails.framework}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Taille du jeu de données
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {projectData.aiDetails.datasetSize}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Nombre de caractéristiques
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {projectData.aiDetails.featuresCount}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Précision
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="body1" fontWeight={500} sx={{ mr: 1 }}>
                            {projectData.aiDetails.accuracy}%
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={projectData.aiDetails.accuracy} 
                            sx={{ 
                              flexGrow: 1,
                              height: 6,
                              borderRadius: 5,
                              backgroundColor: theme.palette.mode === 'dark' 
                                ? 'rgba(255, 255, 255, 0.1)' 
                                : 'rgba(0, 0, 0, 0.1)',
                              '& .MuiLinearProgress-bar': {
                                backgroundColor: theme.palette.success.main,
                                borderRadius: 5,
                              }
                            }}
                          />
                        </Box>
                      </Paper>
                    </Grid>
                  </Grid>
                  
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Conformité et supervision
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Transparence et explicabilité
                        </Typography>
                        <Typography variant="body2" paragraph>
                          Le système inclut un module d'explication qui permet de comprendre les raisons derrière chaque recommandation.
                        </Typography>
                        <Chip 
                          label="Conforme" 
                          size="small" 
                          color="success"
                          icon={<CheckCircle2 size={14} />}
                        />
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Utilisation des données
                        </Typography>
                        <Typography variant="body2" paragraph>
                          Toutes les données personnelles sont anonymisées et leur utilisation est conforme au RGPD.
                        </Typography>
                        <Chip 
                          label="Conforme" 
                          size="small" 
                          color="success"
                          icon={<CheckCircle2 size={14} />}
                        />
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Supervision humaine
                        </Typography>
                        <Typography variant="body2" paragraph>
                          Un processus de validation humaine est en place pour les recommandations ayant un impact significatif.
                        </Typography>
                        <Chip 
                          label="Partiellement conforme" 
                          size="small" 
                          color="warning"
                          icon={<AlertTriangle size={14} />}
                        />
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Non-discrimination
                        </Typography>
                        <Typography variant="body2" paragraph>
                          Des tests de biais sont en cours pour garantir l'équité des recommandations.
                        </Typography>
                        <Chip 
                          label="En cours d'évaluation" 
                          size="small" 
                          color="info"
                          icon={<Activity size={14} />}
                        />
                      </Paper>
                    </Grid>
                  </Grid>
                </Box>
              )}
              
              {/* History Tab */}
              {tabValue === 3 && (
                <Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    Activité récente
                  </Typography>
                  
                  <List>
                    <ListItem divider sx={{ py: 1.5 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <Activity size={20} color={theme.palette.primary.main} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Phase de développement du modèle démarrée"
                        secondary="02/05/2025 - Marie Laurent"
                      />
                    </ListItem>
                    <ListItem divider sx={{ py: 1.5 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <ShieldAlert size={20} color={theme.palette.success.main} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Risque 'Vie privée' mitigé"
                        secondary="25/04/2025 - Thomas Dubois"
                      />
                    </ListItem>
                    <ListItem divider sx={{ py: 1.5 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <MessageCircle size={20} color={theme.palette.info.main} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Nouveau commentaire ajouté"
                        secondary="25/04/2025 - Julie Martin"
                      />
                    </ListItem>
                    <ListItem divider sx={{ py: 1.5 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <ShieldAlert size={20} color={theme.palette.success.main} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Risque 'Transparence' mitigé"
                        secondary="22/04/2025 - Éric Blanc"
                      />
                    </ListItem>
                    <ListItem divider sx={{ py: 1.5 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <CheckCircle2 size={20} color={theme.palette.success.main} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Phase de collecte et préparation des données terminée"
                        secondary="22/04/2025 - Marie Laurent"
                      />
                    </ListItem>
                    <ListItem divider sx={{ py: 1.5 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <ShieldAlert size={20} color={theme.palette.error.main} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Nouveau risque identifié: 'Biais et discrimination'"
                        secondary="20/04/2025 - Sophie Renard"
                      />
                    </ListItem>
                    <ListItem sx={{ py: 1.5 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <FileText size={20} color={theme.palette.primary.main} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Projet créé"
                        secondary="15/04/2025 - Marie Laurent"
                      />
                    </ListItem>
                  </List>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Informations
              </Typography>
              
              <List disablePadding>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <User size={18} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Responsable"
                    secondary={projectData.owner}
                  />
                </ListItem>
                <Divider component="li" />
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Calendar size={18} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Créé le"
                    secondary={projectData.created}
                  />
                </ListItem>
                <Divider component="li" />
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Calendar size={18} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Dernière mise à jour"
                    secondary={projectData.updated}
                  />
                </ListItem>
                <Divider component="li" />
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Tag size={18} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Domaine"
                    secondary={projectData.domain}
                  />
                </ListItem>
              </List>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Tags
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {projectData.tags.map((tag) => (
                    <Chip 
                      key={tag} 
                      label={tag} 
                      size="small"
                      variant="outlined"
                      sx={{ borderRadius: '4px' }}
                    />
                  ))}
                </Box>
              </Box>
            </CardContent>
          </Card>
          
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Équipe
              </Typography>
              
              <List>
                {projectData.team.map((member) => (
                  <ListItem key={member.name} sx={{ px: 0, py: 1 }}>
                    <Avatar 
                      sx={{ 
                        mr: 2, 
                        bgcolor: 
                          member.role === 'Chef de projet' ? theme.palette.primary.main :
                          member.role === 'Data Scientist' ? theme.palette.secondary.main :
                          member.role === 'Développeur IA' ? theme.palette.tertiary.main :
                          theme.palette.success.main
                      }}
                    >
                      {member.avatar}
                    </Avatar>
                    <ListItemText 
                      primary={member.name}
                      secondary={member.role}
                      primaryTypographyProps={{ fontWeight: 500 }}
                    />
                  </ListItem>
                ))}
              </List>
              
              <Button 
                fullWidth 
                variant="outlined" 
                sx={{ mt: 1 }}
                size="small"
              >
                Gérer l'équipe
              </Button>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Conformité
              </Typography>
              
              <PieChart
                title=""
                labels={complianceData.labels}
                data={complianceData.data}
                colors={complianceData.colors}
                height={220}
              />
              
              <Button 
                fullWidth 
                variant="contained" 
                startIcon={<FileBarChart2 size={18} />}
                sx={{ mt: 2 }}
              >
                Rapport de conformité
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProjectDetail;