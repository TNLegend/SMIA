import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper
} from '@mui/material';
import { 
  FileCog, 
  Edit, 
  Download, 
  Check, 
  FileText, 
  Shield, 
  Users, 
  Trash2, 
  Plus,
  ChevronDown,
  History,
  Save,
  X
} from 'lucide-react';

const AIPolicy = () => {
  const theme = useTheme();
  const [editMode, setEditMode] = useState(false);
  const [activePolicy, setActivePolicy] = useState('general');

  const handlePolicyChange = (policy: string) => {
    setActivePolicy(policy);
  };

  const toggleEditMode = () => {
    setEditMode(!editMode);
  };

  const handleSave = () => {
    setEditMode(false);
    // Save logic here
  };

  const handleCancel = () => {
    setEditMode(false);
    // Reset form logic here
  };

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight={700}>
          Politique IA
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {!editMode ? (
            <>
              <Button 
                variant="outlined" 
                startIcon={<Download size={18} />}
              >
                Exporter PDF
              </Button>
              <Button 
                variant="contained" 
                startIcon={<Edit size={18} />}
                onClick={toggleEditMode}
              >
                Modifier
              </Button>
            </>
          ) : (
            <>
              <Button 
                variant="outlined" 
                startIcon={<X size={18} />}
                onClick={handleCancel}
              >
                Annuler
              </Button>
              <Button 
                variant="contained" 
                startIcon={<Save size={18} />}
                onClick={handleSave}
                color="success"
              >
                Enregistrer
              </Button>
            </>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Card 
            sx={{ 
              mb: 3, 
              position: 'sticky', 
              top: 80,
              bgcolor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.03)' 
                : 'rgba(0, 0, 0, 0.01)',
            }}
          >
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Documents
              </Typography>

              <List sx={{ '& .MuiListItem-root': { px: 1, py: 0.5 } }}>
                <ListItem 
                  button 
                  selected={activePolicy === 'general'}
                  onClick={() => handlePolicyChange('general')}
                  sx={{ 
                    borderRadius: 1, 
                    mb: 0.5,
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.mode === 'dark' 
                        ? 'rgba(67, 97, 238, 0.15)'
                        : 'rgba(67, 97, 238, 0.1)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <FileCog size={18} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Politique générale" 
                    primaryTypographyProps={{ fontSize: '0.9rem' }}
                  />
                  <Chip 
                    label="Active" 
                    size="small" 
                    color="success" 
                    sx={{ height: 20 }}
                  />
                </ListItem>

                <ListItem 
                  button 
                  selected={activePolicy === 'ethics'}
                  onClick={() => handlePolicyChange('ethics')}
                  sx={{ 
                    borderRadius: 1, 
                    mb: 0.5,
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.mode === 'dark' 
                        ? 'rgba(67, 97, 238, 0.15)'
                        : 'rgba(67, 97, 238, 0.1)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Shield size={18} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Charte éthique IA" 
                    primaryTypographyProps={{ fontSize: '0.9rem' }}
                  />
                  <Chip 
                    label="Active" 
                    size="small" 
                    color="success"
                    sx={{ height: 20 }}
                  />
                </ListItem>

                <ListItem 
                  button 
                  selected={activePolicy === 'roles'}
                  onClick={() => handlePolicyChange('roles')}
                  sx={{ 
                    borderRadius: 1, 
                    mb: 0.5,
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.mode === 'dark' 
                        ? 'rgba(67, 97, 238, 0.15)'
                        : 'rgba(67, 97, 238, 0.1)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Users size={18} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Rôles et responsabilités" 
                    primaryTypographyProps={{ fontSize: '0.9rem' }}
                  />
                  <Chip 
                    label="Draft" 
                    size="small" 
                    color="warning"
                    sx={{ height: 20 }}
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" fontWeight={500} gutterBottom>
                Archives
              </Typography>

              <List sx={{ '& .MuiListItem-root': { px: 1, py: 0.5 } }}>
                <ListItem 
                  button 
                  sx={{ borderRadius: 1, mb: 0.5 }}
                >
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <History size={18} />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Politique v1.0" 
                    secondary="10/01/2025"
                    primaryTypographyProps={{ fontSize: '0.9rem' }}
                    secondaryTypographyProps={{ fontSize: '0.75rem' }}
                  />
                </ListItem>
              </List>
              
              {editMode && (
                <Button 
                  fullWidth 
                  variant="outlined" 
                  startIcon={<Plus size={18} />}
                  sx={{ mt: 2 }}
                >
                  Nouveau document
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={9}>
          <Card>
            <CardContent sx={{ pb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <FileText size={24} color={theme.palette.primary.main} style={{ marginRight: 12 }} />
                <Typography variant="h5" fontWeight={600}>
                  {activePolicy === 'general' && 'Politique générale IA'}
                  {activePolicy === 'ethics' && 'Charte éthique IA'}
                  {activePolicy === 'roles' && 'Rôles et responsabilités'}
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', mb: 3, gap: 2 }}>
                <Chip 
                  label="v2.1" 
                  variant="outlined" 
                  size="small"
                />
                <Chip 
                  label="Mis à jour le 05/05/2025" 
                  variant="outlined" 
                  size="small"
                />
                <Chip 
                  label="Document officiel" 
                  color="primary"
                  size="small"
                  sx={{ fontWeight: 500 }}
                />
              </Box>

              <Divider sx={{ mb: 3 }} />

              {!editMode ? (
                <Box>
                  {activePolicy === 'general' && (
                    <>
                      <Typography variant="h6" gutterBottom>
                        Préambule
                      </Typography>
                      
                      <Typography paragraph>
                        ACME Corp s'engage à développer et à utiliser l'intelligence artificielle (IA) de manière 
                        responsable, éthique et conforme aux réglementations en vigueur. La présente politique s'inscrit 
                        dans notre démarche de conformité à la norme ISO/IEC 42001 et à l'AI Act européen.
                      </Typography>
                      
                      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                        Objectifs et portée
                      </Typography>
                      
                      <Typography paragraph>
                        Cette politique s'applique à tous les projets d'IA au sein de notre organisation, qu'ils soient 
                        développés en interne ou acquis auprès de tiers. Elle concerne tous les collaborateurs, 
                        prestataires et partenaires impliqués dans la conception, le développement, la mise en œuvre ou 
                        l'utilisation de systèmes d'IA.
                      </Typography>
                      
                      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                        Principes fondamentaux
                      </Typography>
                      
                      <Box component="ul" sx={{ pl: 2 }}>
                        <Box component="li" sx={{ mb: 1 }}>
                          <Typography>
                            <strong>Respect de la vie privée et protection des données personnelles :</strong> Tous les 
                            systèmes d'IA doivent être conçus et utilisés dans le respect du RGPD et des autres 
                            réglementations applicables en matière de protection des données.
                          </Typography>
                        </Box>
                        <Box component="li" sx={{ mb: 1 }}>
                          <Typography>
                            <strong>Transparence et explicabilité :</strong> Les décisions prises par nos systèmes d'IA 
                            doivent être compréhensibles et explicables aux utilisateurs concernés.
                          </Typography>
                        </Box>
                        <Box component="li" sx={{ mb: 1 }}>
                          <Typography>
                            <strong>Non-discrimination et équité :</strong> Nos systèmes d'IA ne doivent pas perpétuer ou 
                            amplifier les biais et discriminations existants.
                          </Typography>
                        </Box>
                        <Box component="li" sx={{ mb: 1 }}>
                          <Typography>
                            <strong>Supervision humaine :</strong> Un contrôle humain approprié doit être maintenu sur 
                            les systèmes d'IA, en particulier pour les décisions à fort impact.
                          </Typography>
                        </Box>
                        <Box component="li">
                          <Typography>
                            <strong>Sécurité et robustesse :</strong> Les systèmes d'IA doivent être sécurisés, fiables 
                            et résilients face aux tentatives de manipulation ou d'attaque.
                          </Typography>
                        </Box>
                      </Box>
                    </>
                  )}

                  {activePolicy === 'ethics' && (
                    <>
                      <Typography variant="h6" gutterBottom>
                        Introduction
                      </Typography>
                      
                      <Typography paragraph>
                        Cette charte éthique définit les principes et valeurs qui guident notre approche en matière 
                        d'intelligence artificielle. Elle constitue un engagement formel de notre organisation envers un 
                        développement et une utilisation responsables de l'IA.
                      </Typography>
                      
                      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                        Valeurs éthiques fondamentales
                      </Typography>
                      
                      <Box sx={{ pl: 2 }}>
                        <Typography paragraph>
                          <strong>1. Respect de la dignité humaine</strong>
                          <br />
                          Nos systèmes d'IA sont conçus pour servir l'humanité et respecter l'autonomie des personnes. 
                          Ils ne doivent jamais être utilisés d'une manière qui pourrait porter atteinte à la dignité 
                          humaine ou aux droits fondamentaux.
                        </Typography>
                        
                        <Typography paragraph>
                          <strong>2. Équité et non-discrimination</strong>
                          <br />
                          Nous nous engageons à identifier et à atténuer les biais potentiels dans les données 
                          d'entraînement et les algorithmes, afin de garantir que nos systèmes d'IA traitent tous les 
                          individus de manière équitable et sans discrimination.
                        </Typography>
                        
                        <Typography paragraph>
                          <strong>3. Transparence et explicabilité</strong>
                          <br />
                          Nous nous efforçons de rendre nos systèmes d'IA compréhensibles par les utilisateurs concernés 
                          et nous nous engageons à expliquer, dans un langage clair, comment ils fonctionnent et prennent 
                          des décisions.
                        </Typography>
                      </Box>
                    </>
                  )}

                  {activePolicy === 'roles' && (
                    <>
                      <Box sx={{ p: 2, bgcolor: theme.palette.warning.light, color: theme.palette.warning.dark, borderRadius: 1, mb: 3 }}>
                        <Typography variant="subtitle2">
                          Ce document est en cours d'élaboration (brouillon).
                        </Typography>
                      </Box>
                      
                      <Typography variant="h6" gutterBottom>
                        Gouvernance IA
                      </Typography>
                      
                      <Typography paragraph>
                        Ce document définit la structure de gouvernance, les rôles et les responsabilités associés à la 
                        gestion des systèmes d'intelligence artificielle au sein de notre organisation.
                      </Typography>
                      
                      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                        Comité IA
                      </Typography>
                      
                      <Typography paragraph>
                        Le Comité IA est responsable de la supervision stratégique de toutes les initiatives d'IA au sein 
                        de l'organisation. Il se réunit trimestriellement et est composé des membres suivants :
                      </Typography>
                      
                      <Box sx={{ pl: 2, mb: 3 }}>
                        <Typography>• Directeur des Systèmes d'Information (président)</Typography>
                        <Typography>• Directeur de l'Innovation</Typography>
                        <Typography>• Responsable de la Protection des Données</Typography>
                        <Typography>• Responsable de la Conformité</Typography>
                        <Typography>• Responsable de la Sécurité des Systèmes d'Information</Typography>
                      </Box>
                      
                      <Typography variant="h6" gutterBottom>
                        Responsable IA
                      </Typography>
                      
                      <Typography paragraph>
                        Le Responsable IA coordonne la mise en œuvre de la politique IA et supervise l'ensemble des 
                        projets d'IA. Ses principales responsabilités incluent :
                      </Typography>
                      
                      <Box sx={{ pl: 2 }}>
                        <Typography>• Assurer la conformité des projets d'IA avec la politique interne</Typography>
                        <Typography>• Évaluer les risques associés aux projets d'IA</Typography>
                        <Typography>• Coordonner les évaluations d'impact</Typography>
                        <Typography>• Conseiller les équipes projet sur les questions éthiques et réglementaires</Typography>
                      </Box>
                    </>
                  )}
                </Box>
              ) : (
                <Box>
                  <TextField
                    fullWidth
                    multiline
                    rows={20}
                    variant="outlined"
                    defaultValue={activePolicy === 'general' ? 
                      `# Préambule

ACME Corp s'engage à développer et à utiliser l'intelligence artificielle (IA) de manière responsable, éthique et conforme aux réglementations en vigueur. La présente politique s'inscrit dans notre démarche de conformité à la norme ISO/IEC 42001 et à l'AI Act européen.

# Objectifs et portée

Cette politique s'applique à tous les projets d'IA au sein de notre organisation, qu'ils soient développés en interne ou acquis auprès de tiers. Elle concerne tous les collaborateurs, prestataires et partenaires impliqués dans la conception, le développement, la mise en œuvre ou l'utilisation de systèmes d'IA.

# Principes fondamentaux

- **Respect de la vie privée et protection des données personnelles :** Tous les systèmes d'IA doivent être conçus et utilisés dans le respect du RGPD et des autres réglementations applicables en matière de protection des données.
- **Transparence et explicabilité :** Les décisions prises par nos systèmes d'IA doivent être compréhensibles et explicables aux utilisateurs concernés.
- **Non-discrimination et équité :** Nos systèmes d'IA ne doivent pas perpétuer ou amplifier les biais et discriminations existants.
- **Supervision humaine :** Un contrôle humain approprié doit être maintenu sur les systèmes d'IA, en particulier pour les décisions à fort impact.
- **Sécurité et robustesse :** Les systèmes d'IA doivent être sécurisés, fiables et résilients face aux tentatives de manipulation ou d'attaque.` : 
                      activePolicy === 'ethics' ?
                      `# Introduction

Cette charte éthique définit les principes et valeurs qui guident notre approche en matière d'intelligence artificielle. Elle constitue un engagement formel de notre organisation envers un développement et une utilisation responsables de l'IA.

# Valeurs éthiques fondamentales

**1. Respect de la dignité humaine**
Nos systèmes d'IA sont conçus pour servir l'humanité et respecter l'autonomie des personnes. Ils ne doivent jamais être utilisés d'une manière qui pourrait porter atteinte à la dignité humaine ou aux droits fondamentaux.

**2. Équité et non-discrimination**
Nous nous engageons à identifier et à atténuer les biais potentiels dans les données d'entraînement et les algorithmes, afin de garantir que nos systèmes d'IA traitent tous les individus de manière équitable et sans discrimination.

**3. Transparence et explicabilité**
Nous nous efforçons de rendre nos systèmes d'IA compréhensibles par les utilisateurs concernés et nous nous engageons à expliquer, dans un langage clair, comment ils fonctionnent et prennent des décisions.` :
                      `# Gouvernance IA

Ce document définit la structure de gouvernance, les rôles et les responsabilités associés à la gestion des systèmes d'intelligence artificielle au sein de notre organisation.

# Comité IA

Le Comité IA est responsable de la supervision stratégique de toutes les initiatives d'IA au sein de l'organisation. Il se réunit trimestriellement et est composé des membres suivants :

• Directeur des Systèmes d'Information (président)
• Directeur de l'Innovation
• Responsable de la Protection des Données
• Responsable de la Conformité
• Responsable de la Sécurité des Systèmes d'Information

# Responsable IA

Le Responsable IA coordonne la mise en œuvre de la politique IA et supervise l'ensemble des projets d'IA. Ses principales responsabilités incluent :

• Assurer la conformité des projets d'IA avec la politique interne
• Évaluer les risques associés aux projets d'IA
• Coordonner les évaluations d'impact
• Conseiller les équipes projet sur les questions éthiques et réglementaires`
                    }
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        fontFamily: 'monospace',
                        fontSize: '0.9rem',
                      },
                    }}
                  />
                  
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    Vous pouvez utiliser la syntaxe Markdown pour la mise en forme.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          <Box sx={{ mt: 3 }}>
            <Accordion>
              <AccordionSummary expandIcon={<ChevronDown size={18} />}>
                <Typography fontWeight={500}>Historique des modifications</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ width: '100%' }}>
                  <Box 
                    sx={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      py: 1,
                      borderBottom: `1px solid ${theme.palette.divider}`,
                    }}
                  >
                    <Typography variant="subtitle2">Version</Typography>
                    <Typography variant="subtitle2">Date</Typography>
                    <Typography variant="subtitle2">Auteur</Typography>
                    <Typography variant="subtitle2">Description</Typography>
                  </Box>
                  
                  <Box 
                    sx={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      py: 1.5,
                      borderBottom: `1px solid ${theme.palette.divider}`,
                    }}
                  >
                    <Typography>v2.1</Typography>
                    <Typography>05/05/2025</Typography>
                    <Typography>Marie Laurent</Typography>
                    <Typography>Mise à jour section "Principes fondamentaux"</Typography>
                  </Box>
                  
                  <Box 
                    sx={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      py: 1.5,
                      borderBottom: `1px solid ${theme.palette.divider}`,
                    }}
                  >
                    <Typography>v2.0</Typography>
                    <Typography>20/04/2025</Typography>
                    <Typography>Thomas Dubois</Typography>
                    <Typography>Révision complète pour conformité à l'AI Act</Typography>
                  </Box>
                  
                  <Box 
                    sx={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      py: 1.5,
                    }}
                  >
                    <Typography>v1.0</Typography>
                    <Typography>10/01/2025</Typography>
                    <Typography>Sophie Renard</Typography>
                    <Typography>Version initiale</Typography>
                  </Box>
                </Box>
              </AccordionDetails>
            </Accordion>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AIPolicy;