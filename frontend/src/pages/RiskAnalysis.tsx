import { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Tabs,
  Tab,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Rating,
  useTheme,
  LinearProgress,
  Divider
} from '@mui/material';
import { 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle, 
  FileText, 
  Download, 
  Eye, 
  Filter, 
  SlidersHorizontal,
  ArrowUpRight
} from 'lucide-react';
import PieChart from '../components/charts/PieChart';
import LineChart from '../components/charts/LineChart';

interface RiskData {
  id: string;
  projectId: string;
  projectName: string;
  category: string;
  description: string;
  level: 'low' | 'medium' | 'high';
  impact: number;
  probability: number;
  status: 'identified' | 'mitigated' | 'accepted';
  date: string;
  mitigation?: string;
}

const riskData: RiskData[] = [
  {
    id: 'risk1',
    projectId: '3',
    projectName: 'Détection de fraude par IA',
    category: 'Biais et discrimination',
    description: 'Risque de faux positifs plus élevés pour certains groupes d\'utilisateurs',
    level: 'high',
    impact: 4,
    probability: 3,
    status: 'identified',
    date: '25/04/2025',
  },
  {
    id: 'risk2',
    projectId: '6',
    projectName: 'IA de reconnaissance faciale',
    category: 'Vie privée',
    description: 'Stockage excessif de données biométriques sensibles',
    level: 'high',
    impact: 5,
    probability: 4,
    status: 'identified',
    date: '20/04/2025',
  },
  {
    id: 'risk3',
    projectId: '1',
    projectName: 'Système de recommandation client',
    category: 'Transparence',
    description: 'Manque d\'explicabilité des recommandations proposées',
    level: 'medium',
    impact: 3,
    probability: 4,
    status: 'mitigated',
    date: '18/04/2025',
    mitigation: 'Implémentation d\'un module d\'explication des recommandations',
  },
  {
    id: 'risk4',
    projectId: '5',
    projectName: 'Optimisation de la chaîne logistique',
    category: 'Exactitude',
    description: 'Prédictions potentiellement erronées en cas de conditions exceptionnelles',
    level: 'medium',
    impact: 4,
    probability: 2,
    status: 'mitigated',
    date: '15/04/2025',
    mitigation: 'Mise en place d\'une validation humaine des décisions critiques',
  },
  {
    id: 'risk5',
    projectId: '2',
    projectName: 'Analyse prédictive de maintenance',
    category: 'Fiabilité',
    description: 'Performances dégradées sur des équipements rares ou peu représentés dans les données',
    level: 'low',
    impact: 2,
    probability: 2,
    status: 'accepted',
    date: '10/04/2025',
  },
  {
    id: 'risk6',
    projectId: '4',
    projectName: 'Chatbot d\'assistance client',
    category: 'Sécurité',
    description: 'Vulnérabilité potentielle aux attaques par injection de prompt',
    level: 'medium',
    impact: 3,
    probability: 3,
    status: 'mitigated',
    date: '05/04/2025',
    mitigation: 'Mise en place de filtres et validation des entrées utilisateur',
  },
];

const RiskAnalysis = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  
  const handleChangeTab = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // Filter risks based on tab value
  const filteredRisks = riskData.filter(risk => {
    if (tabValue === 0) return true; // All risks
    if (tabValue === 1) return risk.level === 'high'; // High risks
    if (tabValue === 2) return risk.level === 'medium'; // Medium risks
    if (tabValue === 3) return risk.level === 'low'; // Low risks
    if (tabValue === 4) return risk.status === 'mitigated'; // Mitigated risks
    return false;
  });
  
  // Data for charts
  const riskLevelData = {
    labels: ['Risque élevé', 'Risque moyen', 'Risque faible'],
    data: [
      riskData.filter(r => r.level === 'high').length,
      riskData.filter(r => r.level === 'medium').length,
      riskData.filter(r => r.level === 'low').length
    ],
    colors: [theme.palette.error.main, theme.palette.warning.main, theme.palette.success.main],
  };
  
  const riskCategoryData = {
    labels: ['Biais', 'Vie privée', 'Transparence', 'Exactitude', 'Fiabilité', 'Sécurité'],
    data: [1, 1, 1, 1, 1, 1], // Example data
  };
  
  const riskTrendData = {
    labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai'],
    datasets: [
      {
        label: 'Risques identifiés',
        data: [5, 8, 12, 15, 19],
        color: theme.palette.primary.main,
      },
      {
        label: 'Risques mitigés',
        data: [2, 4, 6, 9, 12],
        color: theme.palette.success.main,
      },
    ],
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
        return <CheckCircle size={16} />;
      default:
        return null;
    }
  };
  
  const getRiskStatusColor = (status: string) => {
    switch (status) {
      case 'identified':
        return theme.palette.error.main;
      case 'mitigated':
        return theme.palette.success.main;
      case 'accepted':
        return theme.palette.info.main;
      default:
        return theme.palette.grey[500];
    }
  };
  
  const calculateRiskScore = (impact: number, probability: number) => {
    return (impact * probability) / 25 * 100; // Scale to 0-100
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight={700}>
          Analyse des risques
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            variant="outlined" 
            startIcon={<Download size={18} />}
          >
            Exporter PDF
          </Button>
          <Button 
            variant="contained" 
            color="primary"
            startIcon={<SlidersHorizontal size={18} />}
          >
            Évaluer un risque
          </Button>
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ShieldAlert size={20} color={theme.palette.error.main} style={{ marginRight: 8 }} />
                <Typography variant="h6" fontWeight={600}>
                  Risques élevés
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ my: 1 }}>
                {riskData.filter(r => r.level === 'high').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Nécessitent une attention immédiate
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AlertTriangle size={20} color={theme.palette.warning.main} style={{ marginRight: 8 }} />
                <Typography variant="h6" fontWeight={600}>
                  Risques moyens
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ my: 1 }}>
                {riskData.filter(r => r.level === 'medium').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                À surveiller régulièrement
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircle size={20} color={theme.palette.success.main} style={{ marginRight: 8 }} />
                <Typography variant="h6" fontWeight={600}>
                  Risques mitigés
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ my: 1 }}>
                {riskData.filter(r => r.status === 'mitigated').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Des mesures ont été mises en place
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Charts */}
        <Grid item xs={12} md={4}>
          <PieChart
            title="Distribution par niveau de risque"
            labels={riskLevelData.labels}
            data={riskLevelData.data}
            colors={riskLevelData.colors}
            height={260}
          />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <PieChart
            title="Distribution par catégorie"
            labels={riskCategoryData.labels}
            data={riskCategoryData.data}
            height={260}
          />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <LineChart
            title="Évolution des risques"
            labels={riskTrendData.labels}
            datasets={riskTrendData.datasets}
            height={260}
          />
        </Grid>
        
        {/* Risk Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
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
                  <Tab label="Tous les risques" />
                  <Tab 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <span>Risques élevés</span>
                        <Chip 
                          label={riskData.filter(r => r.level === 'high').length} 
                          size="small" 
                          sx={{ ml: 1, height: 20, minWidth: 20 }}
                        />
                      </Box>
                    } 
                  />
                  <Tab 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <span>Risques moyens</span>
                        <Chip 
                          label={riskData.filter(r => r.level === 'medium').length} 
                          size="small" 
                          sx={{ ml: 1, height: 20, minWidth: 20 }}
                        />
                      </Box>
                    } 
                  />
                  <Tab 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <span>Risques faibles</span>
                        <Chip 
                          label={riskData.filter(r => r.level === 'low').length} 
                          size="small" 
                          sx={{ ml: 1, height: 20, minWidth: 20 }}
                        />
                      </Box>
                    } 
                  />
                  <Tab 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <span>Risques mitigés</span>
                        <Chip 
                          label={riskData.filter(r => r.status === 'mitigated').length} 
                          size="small" 
                          sx={{ ml: 1, height: 20, minWidth: 20 }}
                        />
                      </Box>
                    } 
                  />
                </Tabs>
              </Box>
              
              <TableContainer>
                <Table sx={{ minWidth: 650 }} size="medium">
                  <TableHead>
                    <TableRow>
                      <TableCell>Niveau</TableCell>
                      <TableCell>Projet</TableCell>
                      <TableCell>Catégorie</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell align="center">Impact</TableCell>
                      <TableCell align="center">Probabilité</TableCell>
                      <TableCell>Score</TableCell>
                      <TableCell>Statut</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredRisks.map((risk) => (
                      <TableRow
                        key={risk.id}
                        sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                      >
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
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontWeight: 500,
                              display: 'flex',
                              alignItems: 'center',
                              '&:hover': {
                                color: theme.palette.primary.main,
                                cursor: 'pointer',
                              },
                            }}
                          >
                            {risk.projectName}
                            <ArrowUpRight size={14} style={{ marginLeft: 4 }} />
                          </Typography>
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
                                maxWidth: 250,
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
                                  maxWidth: 250,
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
                            icon={<AlertTriangle size={16} style={{ color: theme.palette.warning.main }} />}
                            emptyIcon={<AlertTriangle size={16} style={{ color: theme.palette.divider }} />}
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
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box sx={{ width: 60 }}>
                              <LinearProgress 
                                variant="determinate" 
                                value={calculateRiskScore(risk.impact, risk.probability)} 
                                sx={{ 
                                  height: 6,
                                  borderRadius: 5,
                                  backgroundColor: theme.palette.mode === 'dark' 
                                    ? 'rgba(255, 255, 255, 0.1)' 
                                    : 'rgba(0, 0, 0, 0.1)',
                                  '& .MuiLinearProgress-bar': {
                                    backgroundColor: getRiskLevelColor(risk.level),
                                    borderRadius: 5,
                                  }
                                }}
                              />
                            </Box>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {Math.round(calculateRiskScore(risk.impact, risk.probability))}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={
                              risk.status === 'identified' ? 'Identifié' :
                              risk.status === 'mitigated' ? 'Mitigé' : 'Accepté'
                            } 
                            size="small" 
                            sx={{ 
                              backgroundColor: theme.palette.mode === 'dark' 
                                ? 'rgba(255, 255, 255, 0.05)' 
                                : 'rgba(0, 0, 0, 0.05)',
                              color: getRiskStatusColor(risk.status),
                              fontWeight: 500,
                            }} 
                          />
                        </TableCell>
                        <TableCell>{risk.date}</TableCell>
                        <TableCell align="right">
                          <Tooltip title="Voir détails">
                            <IconButton size="small">
                              <Eye size={18} />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default RiskAnalysis;