import React, { useState } from 'react';
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
  List,
  Grid as GridIcon,
  SlidersHorizontal
} from 'lucide-react';
import ProjectCard, { ProjectCardProps } from '../components/projects/ProjectCard';

// Extend status union to include "draft"
type ProjectStatus = 'draft' | 'active' | 'completed' | 'on-hold';

interface ProjectCardProps {
  id: string;
  title: string;
  description: string;
  category: string;
  owner: string;
  createdAt: string;
  status: ProjectStatus;
  riskLevel: 'low' | 'medium' | 'high';
  complianceScore: number;
}

// Sample data
const projectsData: ProjectCardProps[] = [ /* …same as before… */ ];

export default function Projects() {
  const theme = useTheme();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [tabValue, setTabValue] = useState(0);
  const [sortBy, setSortBy] = useState<'recent' | 'name' | 'riskHigh' | 'complianceLow'>('recent');
  const [activeFilters, setActiveFilters] = useState<string[]>([]);

  const handleChangeTab = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleViewModeChange = (mode: 'grid' | 'list') => {
    setViewMode(mode);
  };

  const handleCreateNew = () => {
    navigate('/projects/new');
  };

  const handleFilter = (filter: string) =>
    setActiveFilters(current =>
      current.includes(filter)
        ? current.filter(f => f !== filter)
        : [...current, filter]
    );

  // Apply tab/search/filter logic
  const filteredProjects = projectsData.filter(p => {
    if (tabValue === 1 && p.status !== 'active') return false;
    if (tabValue === 2 && p.status !== 'completed') return false;
    if (tabValue === 3 && p.status !== 'on-hold') return false;
    if (tabValue === 4 && p.riskLevel !== 'high') return false;

    if (
      searchQuery &&
      ![p.title, p.description, p.category, p.owner]
        .some(field => field.toLowerCase().includes(searchQuery.toLowerCase()))
    ) {
      return false;
    }

    if (activeFilters.includes('lowCompliance') && p.complianceScore >= 70) return false;
    if (activeFilters.includes('highRisk') && p.riskLevel !== 'high') return false;
    if (activeFilters.includes('marketing') && p.category !== 'Marketing') return false;

    return true;
  });

  return (
    <Box>
      {/* Header + New */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" fontWeight={700}>Projets IA</Typography>
        <Button
          variant="contained"
          startIcon={<Plus size={18} />}
          onClick={handleCreateNew}
        >
          Nouveau projet
        </Button>
      </Box>

      {/* Search / Sort / View */}
      <Box mb={3}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Rechercher…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search size={20} color={theme.palette.text.secondary} />
                  </InputAdornment>
                )
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 1,
                  backgroundColor: theme.palette.mode === 'dark'
                    ? 'rgba(255,255,255,0.05)'
                    : 'rgba(0,0,0,0.02)'
                }
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Box display="flex" justifyContent="flex-end" alignItems="center" gap={1}>
              <TextField
                select
                value={sortBy}
                onChange={e => setSortBy(e.target.value as any)}
                size="medium"
                sx={{
                  minWidth: 180,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1,
                    backgroundColor: theme.palette.mode === 'dark'
                      ? 'rgba(255,255,255,0.05)'
                      : 'rgba(0,0,0,0.02)'
                  }
                }}
              >
                <MenuItem value="recent">Plus récents</MenuItem>
                <MenuItem value="name">Nom (A-Z)</MenuItem>
                <MenuItem value="riskHigh">Risque (Élevé-Bas)</MenuItem>
                <MenuItem value="complianceLow">Conformité (Bas-Élevé)</MenuItem>
              </TextField>

              <Tooltip title="Filtres avancés">
                <Button variant="outlined" startIcon={<SlidersHorizontal size={18} />}>
                  Filtres
                </Button>
              </Tooltip>

              <Box bgcolor={theme.palette.background.paper} borderRadius={1}>
                <IconButton
                  color={viewMode === 'grid' ? 'primary' : 'default'}
                  onClick={() => handleViewModeChange('grid')}
                >
                  <GridIcon size={20} />
                </IconButton>
                <IconButton
                  color={viewMode === 'list' ? 'primary' : 'default'}
                  onClick={() => handleViewModeChange('list')}
                >
                  <List size={20} />
                </IconButton>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Tabs & Active Filters */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap">
        <Tabs value={tabValue} onChange={handleChangeTab}>
          <Tab label="Tous" />
          <Tab label="Actifs" />
          <Tab label="Terminés" />
          <Tab label="En pause" />
          <Tab label="Risque élevé" />
        </Tabs>

        <Box display="flex" gap={1} flexWrap="wrap">
          {activeFilters.map(f => (
            <Chip
              key={f}
              label={{
                lowCompliance: 'Conformité <70%',
                highRisk:      'Risque élevé',
                marketing:     'Marketing'
              }[f] || f}
              onDelete={() => handleFilter(f)}
              color="primary"
              size="small"
            />
          ))}
          {activeFilters.length > 0 && (
            <Chip label="Effacer" onClick={() => setActiveFilters([])} size="small" />
          )}
        </Box>
      </Box>

      {/* Project Grid/List */}
      {filteredProjects.length > 0 ? (
        <Grid container spacing={3}>
          {filteredProjects.map(p => (
            <Grid item xs={12} sm={viewMode === 'grid' ? 6 : 12} md={viewMode === 'grid' ? 4 : 12} key={p.id}>
              <ProjectCard {...p} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Box textAlign="center" py={8} borderRadius={1} bgcolor={theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)'}>
          <Typography variant="h6" gutterBottom>Aucun projet trouvé</Typography>
          <Typography color="text.secondary">Changez vos filtres ou créez-en un nouveau.</Typography>
          <Button variant="contained" startIcon={<Plus />} sx={{ mt: 3 }} onClick={handleCreateNew}>
            Nouveau projet
          </Button>
        </Box>
      )}
    </Box>
  );
}
