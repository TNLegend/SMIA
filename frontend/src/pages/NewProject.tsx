import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  FormControlLabel,
  Checkbox,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Divider,
  Autocomplete,
  IconButton,
  useTheme,
  Breadcrumbs,
  Link
} from '@mui/material';
import { 
  Plus, 
  ArrowLeft, 
  Save, 
  FileSearch, 
  Home,
  X,
  Check,
  AlertTriangle,
  User,
  Users
} from 'lucide-react';

const categoriesToOptions = [
  'Marketing',
  'Production',
  'Finance',
  'Service client',
  'Logistique',
  'Sécurité',
  'Ressources humaines',
  'Recherche et développement',
];

const domainsOptions = [
  'B2C',
  'B2B',
  'Interne',
  'Mixte',
];

const aiTypesOptions = [
  'Machine Learning',
  'Deep Learning',
  'NLP',
  'Computer Vision',
  'Système expert',
  'Réseau de neurones',
  'Apprentissage par renforcement',
];

const teamMembersOptions = [
  { id: '1', name: 'Marie Laurent', role: 'Chef de projet', department: 'Marketing' },
  { id: '2', name: 'Thomas Dubois', role: 'Data Scientist', department: 'R&D' },
  { id: '3', name: 'Julie Martin', role: 'Développeur IA', department: 'IT' },
  { id: '4', name: 'Éric Blanc', role: 'Spécialiste marketing', department: 'Marketing' },
  { id: '5', name: 'Sophie Renard', role: 'Analyste de données', department: 'Business Intelligence' },
  { id: '6', name: 'Pierre Durand', role: 'Responsable sécurité', department: 'IT' },
  { id: '7', name: 'Laure Petit', role: 'Designer UX', department: 'Design' },
  { id: '8', name: 'Alexandre Martin', role: 'Chef de produit', department: 'Produit' },
];

const NewProject = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [projectData, setProjectData] = useState({
    title: '',
    description: '',
    category: '',
    domain: '',
    aiTypes: [],
    tags: [],
    complianceRGPD: false,
    complianceAIAct: false,
    complianceISO: false,
    supervisedByHuman: false,
    personalData: false,
    team: [],
    riskAnalysis: false,
  });
  
  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };
  
  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };
  
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = event.target;
    setProjectData({
      ...projectData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };
  
  const handleSelectChange = (event: any) => {
    const { name, value } = event.target;
    setProjectData({
      ...projectData,
      [name]: value,
    });
  };
  
  const handleMultiSelectChange = (name: string, value: string[]) => {
    setProjectData({
      ...projectData,
      [name]: value,
    });
  };
  
  const handleTeamChange = (value: any[]) => {
    setProjectData({
      ...projectData,
      team: value,
    });
  };
  
  const handleTagsChange = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && event.currentTarget.value) {
      const newTag = event.currentTarget.value.trim();
      if (newTag && !projectData.tags.includes(newTag)) {
        setProjectData({
          ...projectData,
          tags: [...projectData.tags, newTag],
        });
        // Clear the input
        event.currentTarget.value = '';
      }
      event.preventDefault();
    }
  };
  
  const handleDeleteTag = (tagToDelete: string) => {
    setProjectData({
      ...projectData,
      tags: projectData.tags.filter((tag) => tag !== tagToDelete),
    });
  };
  
  const handleCancel = () => {
    navigate('/projects');
  };
  
  const handleFinish = () => {
    // Here you would typically submit the project data to your backend
    console.log('Project data:', projectData);
    navigate('/projects');
  };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Breadcrumbs sx={{ mb: 1 }}>
          <Link 
            href="/" 
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
            href="/projects" 
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
            Nouveau projet
          </Typography>
        </Breadcrumbs>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button 
              onClick={handleCancel}
              variant="outlined" 
              startIcon={<ArrowLeft size={18} />}
              sx={{ mr: 2 }}
            >
              Retour
            </Button>
            <Typography variant="h4" fontWeight={700}>
              Nouveau projet IA
            </Typography>
          </Box>
        </Box>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Stepper activeStep={activeStep} orientation="vertical">
                {/* Step 1: Informations générales */}
                <Step>
                  <StepLabel>
                    <Typography variant="h6" fontWeight={600}>
                      Informations générales
                    </Typography>
                  </StepLabel>
                  <StepContent>
                    <Box sx={{ mb: 2 }}>
                      <Grid container spacing={3}>
                        <Grid item xs={12}>
                          <TextField
                            name="title"
                            label="Titre du projet"
                            value={projectData.title}
                            onChange={handleChange}
                            fullWidth
                            required
                            variant="outlined"
                            placeholder="Ex: Système de recommandation client"
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            name="description"
                            label="Description"
                            value={projectData.description}
                            onChange={handleChange}
                            fullWidth
                            required
                            multiline
                            rows={4}
                            variant="outlined"
                            placeholder="Décrivez l'objectif et la portée du projet..."
                          />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth required>
                            <InputLabel>Catégorie</InputLabel>
                            <Select
                              name="category"
                              value={projectData.category}
                              label="Catégorie"
                              onChange={handleSelectChange}
                            >
                              {categoriesToOptions.map((option) => (
                                <MenuItem key={option} value={option}>
                                  {option}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth required>
                            <InputLabel>Domaine</InputLabel>
                            <Select
                              name="domain"
                              value={projectData.domain}
                              label="Domaine"
                              onChange={handleSelectChange}
                            >
                              {domainsOptions.map((option) => (
                                <MenuItem key={option} value={option}>
                                  {option}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12}>
                          <FormControl fullWidth>
                            <Autocomplete
                              multiple
                              options={aiTypesOptions}
                              value={projectData.aiTypes}
                              onChange={(event, newValue) => {
                                handleMultiSelectChange('aiTypes', newValue);
                              }}
                              renderInput={(params) => (
                                <TextField
                                  {...params}
                                  label="Types d'IA"
                                  placeholder="Sélectionnez ou saisissez des types d'IA"
                                />
                              )}
                              renderTags={(value, getTagProps) =>
                                value.map((option, index) => (
                                  <Chip
                                    label={option}
                                    {...getTagProps({ index })}
                                    sx={{ 
                                      borderRadius: '4px',
                                      backgroundColor: theme.palette.primary.main,
                                      color: '#fff',
                                      fontWeight: 500,
                                    }}
                                  />
                                ))
                              }
                            />
                          </FormControl>
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            label="Tags"
                            fullWidth
                            placeholder="Appuyez sur Entrée pour ajouter un tag"
                            onKeyDown={handleTagsChange}
                            helperText="Ajoutez des tags pertinents pour faciliter la recherche"
                          />
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                            {projectData.tags.map((tag) => (
                              <Chip
                                key={tag}
                                label={tag}
                                onDelete={() => handleDeleteTag(tag)}
                                sx={{ borderRadius: '4px' }}
                              />
                            ))}
                          </Box>
                        </Grid>
                      </Grid>
                    </Box>
                    <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
                      <Button 
                        onClick={handleCancel}
                        variant="outlined"
                        startIcon={<X size={18} />}
                      >
                        Annuler
                      </Button>
                      <Button
                        variant="contained"
                        onClick={handleNext}
                        endIcon={<Check size={18} />}
                        disabled={!projectData.title || !projectData.description || !projectData.category || !projectData.domain}
                      >
                        Continuer
                      </Button>
                    </Box>
                  </StepContent>
                </Step>
                
                {/* Step 2: Équipe */}
                <Step>
                  <StepLabel>
                    <Typography variant="h6" fontWeight={600}>
                      Équipe du projet
                    </Typography>
                  </StepLabel>
                  <StepContent>
                    <Box sx={{ mb: 2 }}>
                      <Grid container spacing={3}>
                        <Grid item xs={12}>
                          <Typography variant="subtitle1" gutterBottom>
                            Sélectionnez les membres de l'équipe
                          </Typography>
                          <Autocomplete
                            multiple
                            options={teamMembersOptions}
                            getOptionLabel={(option) => option.name}
                            value={projectData.team}
                            onChange={(event, newValue) => {
                              handleTeamChange(newValue);
                            }}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                label="Membres de l'équipe"
                                placeholder="Recherchez et sélectionnez des membres"
                              />
                            )}
                            renderTags={(value, getTagProps) =>
                              value.map((option, index) => (
                                <Chip
                                  avatar={
                                    <Box 
                                      sx={{ 
                                        width: 24, 
                                        height: 24, 
                                        borderRadius: '50%', 
                                        bgcolor: theme.palette.primary.main,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: '#fff',
                                        fontSize: '12px',
                                        fontWeight: 500,
                                      }}
                                    >
                                      {option.name.charAt(0)}
                                    </Box>
                                  }
                                  label={option.name}
                                  {...getTagProps({ index })}
                                  sx={{ 
                                    borderRadius: '4px',
                                    mr: 1,
                                    mb: 1
                                  }}
                                />
                              ))
                            }
                          />
                        </Grid>
                        
                        {projectData.team.length > 0 && (
                          <Grid item xs={12}>
                            <Typography variant="subtitle1" gutterBottom>
                              Membres sélectionnés
                            </Typography>
                            <Grid container spacing={2}>
                              {projectData.team.map((member) => (
                                <Grid item xs={12} sm={6} key={member.id}>
                                  <Paper 
                                    variant="outlined" 
                                    sx={{ 
                                      p: 2, 
                                      display: 'flex', 
                                      alignItems: 'center',
                                      '&:hover': {
                                        borderColor: theme.palette.primary.main,
                                      }
                                    }}
                                  >
                                    <Box 
                                      sx={{ 
                                        width: 40, 
                                        height: 40, 
                                        borderRadius: '50%', 
                                        bgcolor: theme.palette.primary.main,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: '#fff',
                                        fontSize: '16px',
                                        fontWeight: 500,
                                        mr: 2
                                      }}
                                    >
                                      {member.name.charAt(0)}
                                    </Box>
                                    <Box>
                                      <Typography variant="subtitle2" fontWeight={500}>
                                        {member.name}
                                      </Typography>
                                      <Typography variant="caption" color="text.secondary">
                                        {member.role} • {member.department}
                                      </Typography>
                                    </Box>
                                    <Box sx={{ ml: 'auto' }}>
                                      <IconButton 
                                        size="small"
                                        onClick={() => {
                                          handleTeamChange(projectData.team.filter(m => m.id !== member.id));
                                        }}
                                      >
                                        <X size={16} />
                                      </IconButton>
                                    </Box>
                                  </Paper>
                                </Grid>
                              ))}
                            </Grid>
                          </Grid>
                        )}
                      </Grid>
                    </Box>
                    <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                      <Button onClick={handleBack} variant="outlined">
                        Retour
                      </Button>
                      <Button
                        variant="contained"
                        onClick={handleNext}
                        endIcon={<Check size={18} />}
                      >
                        Continuer
                      </Button>
                    </Box>
                  </StepContent>
                </Step>
                
                {/* Step 3: Conformité et risques */}
                <Step>
                  <StepLabel>
                    <Typography variant="h6" fontWeight={600}>
                      Conformité et risques
                    </Typography>
                  </StepLabel>
                  <StepContent>
                    <Box sx={{ mb: 2 }}>
                      <Grid container spacing={3}>
                        <Grid item xs={12}>
                          <Typography variant="subtitle1" gutterBottom>
                            Aspects réglementaires
                          </Typography>
                          <Paper variant="outlined" sx={{ p: 2 }}>
                            <FormControlLabel
                              control={
                                <Checkbox
                                  name="complianceRGPD"
                                  checked={projectData.complianceRGPD}
                                  onChange={handleChange}
                                />
                              }
                              label="Ce projet est soumis au RGPD"
                            />
                            <FormControlLabel
                              control={
                                <Checkbox
                                  name="complianceAIAct"
                                  checked={projectData.complianceAIAct}
                                  onChange={handleChange}
                                />
                              }
                              label="Ce projet est concerné par l'AI Act européen"
                            />
                            <FormControlLabel
                              control={
                                <Checkbox
                                  name="complianceISO"
                                  checked={projectData.complianceISO}
                                  onChange={handleChange}
                                />
                              }
                              label="Ce projet doit être conforme à la norme ISO/IEC 42001"
                            />
                          </Paper>
                        </Grid>
                        
                        <Grid item xs={12}>
                          <Typography variant="subtitle1" gutterBottom>
                            Caractéristiques du système IA
                          </Typography>
                          <Paper variant="outlined" sx={{ p: 2 }}>
                            <FormControlLabel
                              control={
                                <Checkbox
                                  name="supervisedByHuman"
                                  checked={projectData.supervisedByHuman}
                                  onChange={handleChange}
                                />
                              }
                              label="Le système sera supervisé par un humain"
                            />
                            <FormControlLabel
                              control={
                                <Checkbox
                                  name="personalData"
                                  checked={projectData.personalData}
                                  onChange={handleChange}
                                />
                              }
                              label="Le système utilise des données personnelles"
                            />
                          </Paper>
                        </Grid>
                        
                        <Grid item xs={12}>
                          <Divider sx={{ my: 2 }} />
                          <FormControlLabel
                            control={
                              <Checkbox
                                name="riskAnalysis"
                                checked={projectData.riskAnalysis}
                                onChange={handleChange}
                              />
                            }
                            label={
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <AlertTriangle size={18} color={theme.palette.warning.main} style={{ marginRight: 8 }} />
                                <Typography fontWeight={500}>
                                  Je souhaite effectuer une analyse de risques complète après la création du projet
                                </Typography>
                              </Box>
                            }
                          />
                        </Grid>
                      </Grid>
                    </Box>
                    <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                      <Button onClick={handleBack} variant="outlined">
                        Retour
                      </Button>
                      <Button
                        variant="contained"
                        onClick={handleFinish}
                        endIcon={<Save size={18} />}
                      >
                        Créer le projet
                      </Button>
                    </Box>
                  </StepContent>
                </Step>
              </Stepper>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Conseils pour un bon projet IA
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                1. Définir clairement les objectifs
              </Typography>
              <Typography variant="body2" paragraph>
                Soyez précis sur ce que vous souhaitez accomplir avec votre système d'IA. Des objectifs clairement définis facilitent l'évaluation des risques et la vérification de la conformité.
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom>
                2. Constituer une équipe pluridisciplinaire
              </Typography>
              <Typography variant="body2" paragraph>
                Incluez des experts en IA, des spécialistes métier, des juristes et des responsables éthiques pour couvrir tous les aspects du projet.
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom>
                3. Anticiper les risques dès le départ
              </Typography>
              <Typography variant="body2">
                Identifiez les risques potentiels en matière de biais, de vie privée, de sécurité et d'impact sociétal avant de commencer le développement.
              </Typography>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                Statut du projet
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box 
                  sx={{ 
                    width: 12, 
                    height: 12, 
                    borderRadius: '50%', 
                    bgcolor: theme.palette.warning.main,
                    mr: 1
                  }} 
                />
                <Typography variant="body2">
                  En cours de création
                </Typography>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" gutterBottom>
                Informations complétées
              </Typography>
              
              <Box sx={{ mt: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Informations générales</Typography>
                  <Box>
                    {activeStep >= 1 ? (
                      <Check size={18} color={theme.palette.success.main} />
                    ) : (
                      <AlertTriangle size={18} color={theme.palette.warning.main} />
                    )}
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Équipe du projet</Typography>
                  <Box>
                    {activeStep >= 2 ? (
                      <Check size={18} color={theme.palette.success.main} />
                    ) : (
                      <AlertTriangle size={18} color={theme.palette.warning.main} />
                    )}
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Conformité et risques</Typography>
                  <Box>
                    {activeStep >= 3 ? (
                      <Check size={18} color={theme.palette.success.main} />
                    ) : (
                      <AlertTriangle size={18} color={theme.palette.warning.main} />
                    )}
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default NewProject;