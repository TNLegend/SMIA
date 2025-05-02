import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Button,
  TextField,
  InputAdornment,
  MenuItem,
  IconButton,
  Tabs,
  Tab,
  useTheme,
  Chip,
  Tooltip
} from '@mui/material';
import { 
  Plus, 
  Search, 
  Filter, 
  List, 
  Grid as GridIcon,
  SlidersHorizontal,
  BarChart4,
  FileSpreadsheet,
  Check 
} from 'lucide-react';
import ProjectCard, { ProjectCardProps } from '../components/projects/ProjectCard';

// Sample project data
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
  {
    id: '3',
    title: 'Détection de fraude par IA',
    description: 'Système d\'IA pour détecter les transactions frauduleuses en temps réel.',
    category: 'Finance',
    owner: 'Julie Martin',
    createdAt: '23/03/2025',
    status: 'active',
    riskLevel: 'high',
    complianceScore: 65,
  },
  {
    id: '4',
    title: 'Chatbot d\'assistance client',
    description: 'Chatbot intelligent pour répondre aux questions fréquentes des clients et les accompagner.',
    category: 'Service client',
    owner: 'Éric Blanc',
    createdAt: '10/04/2025',
    status: 'completed',
    riskLevel: 'low',
    complianceScore: 89,
  },
  {
    id: '5',
    title: 'Optimisation de la chaîne logistique',
    description: 'IA qui optimise les routes de livraison et la gestion des stocks pour réduire les coûts.',
    category: 'Logistique',
    owner: 'Sophie Renard',
    createdAt: '05/05/2025',
    status: 'on-hold',
    riskLevel: 'medium',
    complianceScore: 72,
  },
  {
    id: '6',
    title: 'IA de reconnaissance faciale',
    description: 'Système d\'analyse pour la sécurité des locaux et le contrôle d\'accès par reconnaissance faciale.',
    category: 'Sécurité',
    owner: 'Pierre Durand',
    createdAt: '18/04/2025',
    status: 'active',
    riskLevel: 'high',
    complianceScore: 58,
  },
];

const Projects = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('grid');
  const [tabValue, setTabValue] = useState(0);
  const [sortBy, setSortBy] = useState('recent');
  const [activeFilters, setActiveFilters] = useState<string[]>([]);

  const handleChangeTab = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  const handleViewModeChange = (mode: string) => {
    setViewMode(mode);
  };
  
  const handleCreateNew = () => {
    navigate('/projects/new');
  };
  
  const handleFilter = (filter: string) => {
    if (activeFilters.includes(filter)) {
      setActiveFilters(activeFilters.filter(f => f !== filter));
    } else {
      setActiveFilters([...activeFilters, filter]);
    }
  };
  
  // Filter projects based on tab, search, and filters
  const filteredProjects = projectsData.filter(project => {
    // Tab filtering
    if (tabValue === 1 && project.status !== 'active') return false;
    if (tabValue === 2 && project.status !== 'completed') return false;
    if (tabValue === 3 && project.status !== 'on-hold') return false;
    if (tabValue === 4 && project.riskLevel !== 'high') return false;
    
    // Search filtering
    if (
      searchQuery && 
      !project.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !project.description.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !project.category.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !project.owner.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    
    // Custom filters
    if (activeFilters.includes('lowCompliance') && project.complianceScore >= 70) return false;
    if (activeFilters.includes('highRisk') && project.riskLevel !== 'high') return false;
    if (activeFilters.includes('marketing') && project.category !== 'Marketing') return false;
    
    return true;
  });

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight={700}>
          Projets IA
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          startIcon={<Plus size={18} />}
          onClick={handleCreateNew}
        >
          Nouveau projet
        </Button>
      </Box>
      
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Rechercher par titre, description, catégorie..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search size={20} color={theme.palette.text.secondary} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '8px',
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? 'rgba(255, 255, 255, 0.05)' 
                    : 'rgba(0, 0, 0, 0.02)',
                },
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: { xs: 'flex-start', md: 'flex-end' } }}>
              <TextField
                select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                variant="outlined"
                size="medium"
                sx={{ 
                  minWidth: 180,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '8px',
                    backgroundColor: theme.palette.mode === 'dark' 
                      ? 'rgba(255, 255, 255, 0.05)' 
                      : 'rgba(0, 0, 0, 0.02)',
                  },
                }}
              >
                <MenuItem value="recent">Plus récents</MenuItem>
                <MenuItem value="name">Nom (A-Z)</MenuItem>
                <MenuItem value="riskHigh">Risque (Élevé-Bas)</MenuItem>
                <MenuItem value="complianceLow">Conformité (Bas-Élevé)</MenuItem>
              </TextField>
              
              <Tooltip title="Filtres avancés">
                <Button
                  variant="outlined"
                  startIcon={<SlidersHorizontal size={18} />}
                  sx={{ borderRadius: '8px' }}
                >
                  Filtres
                </Button>
              </Tooltip>
              
              <Box sx={{ display: 'flex', bgcolor: theme.palette.background.paper, borderRadius: 1, ml: 1 }}>
                <Tooltip title="Vue grille">
                  <IconButton 
                    color={viewMode === 'grid' ? 'primary' : 'default'}
                    onClick={() => handleViewModeChange('grid')}
                  >
                    <GridIcon size={20} />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Vue liste">
                  <IconButton 
                    color={viewMode === 'list' ? 'primary' : 'default'}
                    onClick={() => handleViewModeChange('list')}
                  >
                    <List size={20} />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Box>
      
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <Tabs
          value={tabValue}
          onChange={handleChangeTab}
          aria-label="project tabs"
          sx={{
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 500,
              fontSize: '0.875rem',
              minWidth: 'auto',
              px: 2,
            },
          }}
        >
          <Tab label="Tous" />
          <Tab label="Actifs" />
          <Tab label="Terminés" />
          <Tab label="En pause" />
          <Tab label="Risque élevé" />
        </Tabs>
        
        <Box sx={{ display: 'flex', gap: 1, my: 1 }}>
          {activeFilters.length > 0 && (
            <>
              {activeFilters.map((filter) => (
                <Chip 
                  key={filter}
                  label={
                    filter === 'lowCompliance' ? 'Conformité < 70%' :
                    filter === 'highRisk' ? 'Risque élevé' :
                    filter === 'marketing' ? 'Marketing' : filter
                  }
                  onDelete={() => handleFilter(filter)}
                  color="primary"
                  size="small"
                  deleteIcon={<Check size={16} />}
                  sx={{ borderRadius: '4px' }}
                />
              ))}
              <Chip 
                label="Effacer"
                onClick={() => setActiveFilters([])}
                size="small"
                variant="outlined"
                sx={{ borderRadius: '4px' }}
              />
            </>
          )}
        </Box>
      </Box>
      
      {filteredProjects.length > 0 ? (
        <Grid container spacing={3}>
          {filteredProjects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <ProjectCard {...project} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Box 
          sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center',
            py: 8,
            bgcolor: theme.palette.mode === 'dark' 
              ? 'rgba(255, 255, 255, 0.02)' 
              : 'rgba(0, 0, 0, 0.02)',
            borderRadius: 2,
          }}
        >
          <FileSpreadsheet size={48} color={theme.palette.text.secondary} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Aucun projet trouvé
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Essayez de modifier vos filtres ou de créer un nouveau projet.
          </Typography>
          <Button 
            variant="contained" 
            startIcon={<Plus size={18} />}
            sx={{ mt: 3 }}
            onClick={handleCreateNew}
          >
            Créer un nouveau projet
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default Projects;