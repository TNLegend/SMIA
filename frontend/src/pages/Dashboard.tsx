import { Grid, Typography, Box, Card, CardContent, useTheme, Avatar, Button } from '@mui/material';
import { 
  BrainCircuit, 
  AlertTriangle, 
  FileText, 
  ShieldCheck, 
  CheckCircle2, 
  BarChart3,
  Lock,
  Users
} from 'lucide-react';
import StatCard from '../components/dashboard/StatCard';
import PieChart from '../components/charts/PieChart';
import LineChart from '../components/charts/LineChart';
import ProjectCard, { ProjectCardProps } from '../components/projects/ProjectCard';

const projectsData: ProjectCardProps[] = [
  {
    id: '1',
    title: 'Système de recommandation client',
    description: 'IA qui recommande des produits aux clients selon leur historique d\'achats et comportement.',
    category: 'Marketing',
    owner: 'Marie Laurent',
    createdAt: '15/04/2025',
    status: 'active',
    riskLevel: 'medium',
    complianceScore: 78,
  },
  {
    id: '2',
    title: 'Analyse prédictive de maintenance',
    description: 'Système d\'IA pour prédire les défaillances d\'équipement avant qu\'elles ne se produisent.',
    category: 'Production',
    owner: 'Thomas Dubois',
    createdAt: '02/05/2025',
    status: 'active',
    riskLevel: 'low',
    complianceScore: 92,
  },
];

const Dashboard = () => {
  const theme = useTheme();
  
  // Data for charts
  const riskDistributionData = {
    labels: ['Risque faible', 'Risque moyen', 'Risque élevé'],
    data: [12, 5, 2],
    colors: [theme.palette.success.main, theme.palette.warning.main, theme.palette.error.main],
  };
  
  const complianceTrendData = {
    labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin'],
    datasets: [
      {
        label: 'ISO/IEC 42001',
        data: [65, 68, 75, 78, 85, 87],
        color: theme.palette.primary.main,
      },
      {
        label: 'RGPD',
        data: [70, 75, 78, 80, 82, 85],
        color: theme.palette.secondary.main,
      },
      {
        label: 'AI Act',
        data: [60, 65, 68, 72, 76, 78],
        color: theme.palette.tertiary.main,
      },
    ],
  };
  
  const aiCategoryData = {
    labels: ['Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'Autre'],
    data: [8, 5, 3, 2, 1],
    colors: [
      theme.palette.primary.main,
      theme.palette.secondary.main,
      theme.palette.tertiary.main,
      theme.palette.success.main,
      theme.palette.warning.main,
    ],
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Tableau de bord
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          startIcon={<FileText size={16} />}
        >
          Générer rapport
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {/* Stats Row */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Projets IA"
            value="19"
            icon={<BrainCircuit size={20} />}
            color={theme.palette.primary.main}
            percentage={85}
            trend="up"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Risques identifiés"
            value="14"
            icon={<AlertTriangle size={20} />}
            color={theme.palette.warning.main}
            percentage={70}
            trend="down"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Conformité ISO 42001"
            value="87%"
            icon={<ShieldCheck size={20} />}
            color={theme.palette.success.main}
            percentage={87}
            progressType="circular"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Politiques actives"
            value="3"
            icon={<Lock size={20} />}
            color={theme.palette.secondary.main}
            percentage={100}
            trend="neutral"
          />
        </Grid>
        
        {/* Charts Row */}
        <Grid item xs={12} md={8}>
          <LineChart
            title="Évolution de la conformité"
            labels={complianceTrendData.labels}
            datasets={complianceTrendData.datasets}
            height={320}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <PieChart
            title="Distribution des risques"
            labels={riskDistributionData.labels}
            data={riskDistributionData.data}
            colors={riskDistributionData.colors}
            height={320}
          />
        </Grid>
        
        {/* Recent Projects */}
        <Grid item xs={12}>
          <Box sx={{ mb: 2, mt: 1 }}>
            <Typography variant="h5" fontWeight={600}>
              Projets récents
            </Typography>
          </Box>
          <Grid container spacing={3}>
            {projectsData.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <ProjectCard {...project} />
              </Grid>
            ))}
            <Grid item xs={12} sm={6} md={4}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  p: 3,
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? 'rgba(255, 255, 255, 0.05)' 
                    : 'rgba(0, 0, 0, 0.02)',
                  border: `1px dashed ${theme.palette.divider}`,
                }}
              >
                <Button 
                  variant="outlined" 
                  color="primary"
                  size="large"
                  sx={{ 
                    borderRadius: '50%', 
                    width: 60, 
                    height: 60, 
                    minWidth: 'auto',
                    mb: 2,
                  }}
                >
                  +
                </Button>
                <Typography variant="h6" align="center" fontWeight={500}>
                  Ajouter un nouveau projet
                </Typography>
                <Typography variant="body2" align="center" color="text.secondary" sx={{ mt: 1 }}>
                  Déclarez et suivez vos nouveaux projets d'IA
                </Typography>
              </Card>
            </Grid>
          </Grid>
        </Grid>
        
        {/* Bottom Row */}
        <Grid item xs={12} md={4}>
          <PieChart
            title="Catégories d'IA"
            labels={aiCategoryData.labels}
            data={aiCategoryData.data}
            colors={aiCategoryData.colors}
          />
        </Grid>
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Équipe de gouvernance
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                {[
                  { name: 'Sophie Martin', role: 'Responsable IA', avatar: 'SM' },
                  { name: 'Laurent Dupont', role: 'Analyste de risques', avatar: 'LD' },
                  { name: 'Mathilde Roux', role: 'Experte conformité', avatar: 'MR' },
                  { name: 'Jean Mercier', role: 'Architecte de solutions', avatar: 'JM' },
                ].map((member, index) => (
                  <Grid item xs={12} sm={6} key={index}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar 
                        sx={{ 
                          bgcolor: [
                            theme.palette.primary.main,
                            theme.palette.secondary.main,
                            theme.palette.tertiary.main,
                            theme.palette.success.main,
                          ][index % 4] 
                        }}
                      >
                        {member.avatar}
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle2">{member.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {member.role}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;