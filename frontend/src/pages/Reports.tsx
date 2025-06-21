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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Checkbox,
  ListItemButton,
  List,
  FormControlLabel,
  FormGroup,
  useTheme,
  Divider
} from '@mui/material';
import { FileBarChart2, Download, Search, Eye, Calendar, FileText, MoreVertical, UserCheck, ShieldCheck, Printer, Mail, Plus, Filter, DownloadCloud as CloudDownload, FileCheck } from 'lucide-react';

interface Report {
  id: string;
  title: string;
  type: 'conformity' | 'risk' | 'project' | 'audit';
  date: string;
  author: string;
  format: string;
  status: 'draft' | 'final' | 'archived';
  size: string;
}

const reportsData: Report[] = [
  {
    id: 'report1',
    title: 'Conformité ISO/IEC 42001 - Q2 2025',
    type: 'conformity',
    date: '10/05/2025',
    author: 'Marie Laurent',
    format: 'PDF',
    status: 'final',
    size: '2.3 MB',
  },
  {
    id: 'report2',
    title: 'Analyse de risques IA - Mai 2025',
    type: 'risk',
    date: '05/05/2025',
    author: 'Thomas Dubois',
    format: 'PDF',
    status: 'final',
    size: '1.8 MB',
  },
  {
    id: 'report3',
    title: 'Rapport projet - Système de recommandation client',
    type: 'project',
    date: '28/04/2025',
    author: 'Julie Martin',
    format: 'PDF',
    status: 'final',
    size: '3.1 MB',
  },
  {
    id: 'report4',
    title: 'Audit interne IA - Mars 2025',
    type: 'audit',
    date: '15/04/2025',
    author: 'Sophie Renard',
    format: 'PDF',
    status: 'final',
    size: '4.2 MB',
  },
  {
    id: 'report5',
    title: 'Rapport projet - Chatbot d\'assistance client',
    type: 'project',
    date: '10/04/2025',
    author: 'Éric Blanc',
    format: 'PDF',
    status: 'final',
    size: '2.8 MB',
  },
  {
    id: 'report6',
    title: 'Analyse de risques IA - Avril 2025',
    type: 'risk',
    date: '05/04/2025',
    author: 'Thomas Dubois',
    format: 'PDF',
    status: 'draft',
    size: '1.5 MB',
  },
  {
    id: 'report7',
    title: 'Conformité RGPD pour projets IA',
    type: 'conformity',
    date: '01/04/2025',
    author: 'Marie Laurent',
    format: 'PDF',
    status: 'final',
    size: '2.1 MB',
  },
  {
    id: 'report8',
    title: 'Rapport projet - Détection de fraude par IA',
    type: 'project',
    date: '25/03/2025',
    author: 'Pierre Durand',
    format: 'PDF',
    status: 'archived',
    size: '2.5 MB',
  },
];

const Reports = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [openGenerateDialog, setOpenGenerateDialog] = useState(false);
  
  const handleChangeTab = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>, reportId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedReport(reportId);
  };
  
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  
  const handleGenerateDialog = () => {
    setOpenGenerateDialog(!openGenerateDialog);
  };
  
  // Filter reports based on tab and search
  const filteredReports = reportsData.filter(report => {
    // Tab filtering
    if (tabValue === 1 && report.type !== 'conformity') return false;
    if (tabValue === 2 && report.type !== 'risk') return false;
    if (tabValue === 3 && report.type !== 'project') return false;
    if (tabValue === 4 && report.type !== 'audit') return false;
    
    // Search filtering
    if (
      searchQuery && 
      !report.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !report.author.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !report.date.includes(searchQuery)
    ) {
      return false;
    }
    
    return true;
  });
  
  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'conformity':
        return 'Conformité';
      case 'risk':
        return 'Risque';
      case 'project':
        return 'Projet';
      case 'audit':
        return 'Audit';
      default:
        return type;
    }
  };
  
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'conformity':
        return theme.palette.primary.main;
      case 'risk':
        return theme.palette.error.main;
      case 'project':
        return theme.palette.success.main;
      case 'audit':
        return theme.palette.secondary.main;
      default:
        return theme.palette.grey[500];
    }
  };
  
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'conformity':
        return <ShieldCheck size={16} />;
      case 'risk':
        return <FileBarChart2 size={16} />;
      case 'project':
        return <FileText size={16} />;
      case 'audit':
        return <UserCheck size={16} />;
      default:
        return null;
    }
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return theme.palette.warning.main;
      case 'final':
        return theme.palette.success.main;
      case 'archived':
        return theme.palette.grey[500];
      default:
        return theme.palette.grey[500];
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight={700}>
          Rapports
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<Plus size={18} />}
          onClick={handleGenerateDialog}
        >
          Générer un rapport
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ShieldCheck 
                  size={20} 
                  color={theme.palette.primary.main} 
                  style={{ marginRight: 8 }} 
                />
                <Typography variant="h6" fontWeight={600}>
                  Conformité
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ my: 1 }}>
                {reportsData.filter(r => r.type === 'conformity').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Rapports de conformité
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <FileBarChart2 
                  size={20} 
                  color={theme.palette.error.main} 
                  style={{ marginRight: 8 }} 
                />
                <Typography variant="h6" fontWeight={600}>
                  Risques
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ my: 1 }}>
                {reportsData.filter(r => r.type === 'risk').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analyses de risques
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <FileText 
                  size={20} 
                  color={theme.palette.success.main} 
                  style={{ marginRight: 8 }} 
                />
                <Typography variant="h6" fontWeight={600}>
                  Projets
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ my: 1 }}>
                {reportsData.filter(r => r.type === 'project').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Rapports de projets
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <UserCheck 
                  size={20} 
                  color={theme.palette.secondary.main} 
                  style={{ marginRight: 8 }} 
                />
                <Typography variant="h6" fontWeight={600}>
                  Audits
                </Typography>
              </Box>
              <Typography variant="h3" fontWeight={700} sx={{ my: 1 }}>
                {reportsData.filter(r => r.type === 'audit').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Rapports d'audit
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Reports Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
              <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Tabs 
                  value={tabValue} 
                  onChange={handleChangeTab}
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
                  <Tab label="Tous les rapports" />
                  <Tab label="Conformité" />
                  <Tab label="Risques" />
                  <Tab label="Projets" />
                  <Tab label="Audits" />
                </Tabs>
                
                <TextField
                  placeholder="Rechercher..."
                  size="small"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search size={18} color={theme.palette.text.secondary} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    width: 250,
                    '& .MuiOutlinedInput-root': {
                      borderRadius: '8px',
                    },
                  }}
                />
              </Box>
              
              <Divider />
              
              <TableContainer>
                <Table sx={{ minWidth: 650 }} size="medium">
                  <TableHead>
                    <TableRow>
                      <TableCell>Type</TableCell>
                      <TableCell>Titre</TableCell>
                      <TableCell>Date</TableCell>
                      <TableCell>Auteur</TableCell>
                      <TableCell>Format</TableCell>
                      <TableCell>Statut</TableCell>
                      <TableCell>Taille</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredReports.map((report) => (
                      <TableRow
                        key={report.id}
                        sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                      >
                        <TableCell>
                          <Chip 
                            icon={getTypeIcon(report.type)}
                            label={getTypeLabel(report.type)} 
                            size="small" 
                            sx={{ 
                              backgroundColor: theme.palette.mode === 'dark' 
                                ? 'rgba(255, 255, 255, 0.05)' 
                                : 'rgba(0, 0, 0, 0.05)',
                              color: getTypeColor(report.type),
                              fontWeight: 500,
                              '& .MuiChip-icon': {
                                color: getTypeColor(report.type),
                              },
                            }} 
                          />
                        </TableCell>
                        <TableCell sx={{ fontWeight: 500 }}>{report.title}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Calendar size={14} style={{ marginRight: 4 }} />
                            {report.date}
                          </Box>
                        </TableCell>
                        <TableCell>{report.author}</TableCell>
                        <TableCell>{report.format}</TableCell>
                        <TableCell>
                          <Chip 
                            label={
                              report.status === 'draft' ? 'Brouillon' :
                              report.status === 'final' ? 'Final' : 'Archivé'
                            } 
                            size="small" 
                            sx={{ 
                              backgroundColor: theme.palette.mode === 'dark' 
                                ? 'rgba(255, 255, 255, 0.05)' 
                                : 'rgba(0, 0, 0, 0.05)',
                              color: getStatusColor(report.status),
                              fontWeight: 500,
                            }} 
                          />
                        </TableCell>
                        <TableCell>{report.size}</TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <IconButton 
                              size="small" 
                              sx={{ mr: 1 }}
                              color="primary"
                            >
                              <Eye size={18} />
                            </IconButton>
                            <IconButton 
                              size="small"
                              sx={{ mr: 1 }}
                            >
                              <Download size={18} />
                            </IconButton>
                            <IconButton 
                              size="small"
                              onClick={(e) => handleMenuClick(e, report.id)}
                            >
                              <MoreVertical size={18} />
                            </IconButton>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              
              {filteredReports.length === 0 && (
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    py: 4,
                  }}
                >
                  <FileText size={40} color={theme.palette.text.secondary} />
                  <Typography variant="h6" sx={{ mt: 2 }}>
                    Aucun rapport trouvé
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Modifiez vos critères de recherche ou générez un nouveau rapport.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Report Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            boxShadow: theme.shadows[3],
            minWidth: 180,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <Eye size={18} />
          </ListItemIcon>
          <ListItemText>Voir le rapport</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <Download size={18} />
          </ListItemIcon>
          <ListItemText>Télécharger</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <Mail size={18} />
          </ListItemIcon>
          <ListItemText>Envoyer par email</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <Printer size={18} />
          </ListItemIcon>
          <ListItemText>Imprimer</ListItemText>
        </MenuItem>
      </Menu>
      
      {/* Generate Report Dialog */}
      <Dialog
        open={openGenerateDialog}
        onClose={handleGenerateDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <FileBarChart2 size={22} style={{ marginRight: 8 }} color={theme.palette.primary.main} />
            <Typography variant="h6" component="div" fontWeight={600}>
              Générer un nouveau rapport
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                label="Titre du rapport"
                fullWidth
                variant="outlined"
                placeholder="Ex: Conformité ISO/IEC 42001 - Q2 2025"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Type de rapport</InputLabel>
                <Select
                  label="Type de rapport"
                  defaultValue="conformity"
                >
                  <MenuItem value="conformity">Conformité</MenuItem>
                  <MenuItem value="risk">Analyse de risques</MenuItem>
                  <MenuItem value="project">Rapport de projet</MenuItem>
                  <MenuItem value="audit">Audit</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Format</InputLabel>
                <Select
                  label="Format"
                  defaultValue="pdf"
                >
                  <MenuItem value="pdf">PDF</MenuItem>
                  <MenuItem value="docx">Word (DOCX)</MenuItem>
                  <MenuItem value="xlsx">Excel (XLSX)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom fontWeight={500}>
                Contenu à inclure
              </Typography>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <FormGroup>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Résumé exécutif"
                      />
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Analyse de conformité"
                      />
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Statistiques et graphiques"
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Liste des écarts"
                      />
                      <FormControlLabel
                        control={<Checkbox defaultChecked />}
                        label="Recommandations"
                      />
                      <FormControlLabel
                        control={<Checkbox />}
                        label="Annexes techniques"
                      />
                    </Grid>
                  </Grid>
                </FormGroup>
              </Paper>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom fontWeight={500}>
                Projets concernés
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                <List dense>
                  <ListItemButton>
                    <Checkbox />
                    <ListItemText 
                      primary="Système de recommandation client" 
                      secondary="Marketing - Marie Laurent"
                    />
                  </ListItemButton>
                  <ListItemButton>
                    <Checkbox />
                    <ListItemText 
                      primary="Analyse prédictive de maintenance" 
                      secondary="Production - Thomas Dubois"
                    />
                  </ListItemButton>
                  <ListItemButton>
                    <Checkbox />
                    <ListItemText 
                      primary="Détection de fraude par IA" 
                      secondary="Finance - Julie Martin"
                    />
                  </ListItemButton>
                  <ListItemButton>
                    <Checkbox />
                    <ListItemText 
                      primary="Chatbot d'assistance client" 
                      secondary="Service client - Éric Blanc"
                    />
                  </ListItemButton>
                  <ListItemButton>
                    <Checkbox />
                    <ListItemText 
                      primary="Optimisation de la chaîne logistique" 
                      secondary="Logistique - Sophie Renard"
                    />
                  </ListItemButton>
                </List>
              </Paper>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="Notes supplémentaires"
                fullWidth
                multiline
                rows={3}
                variant="outlined"
                placeholder="Informations ou instructions supplémentaires pour ce rapport..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={handleGenerateDialog} variant="outlined">
            Annuler
          </Button>
          <Button 
            onClick={handleGenerateDialog} 
            variant="contained" 
            startIcon={<CloudDownload size={18} />}
          >
            Générer le rapport
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Reports;