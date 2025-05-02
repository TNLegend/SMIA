import { useNavigate } from 'react-router-dom';
import { Box, Typography, Button, useTheme } from '@mui/material';
import { Home, ArrowLeft } from 'lucide-react';

const NotFound = () => {
  const theme = useTheme();
  const navigate = useNavigate();

  return (
    <Box 
      sx={{ 
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 'calc(100vh - 200px)',
        textAlign: 'center',
        p: 3
      }}
    >
      <Typography 
        variant="h1" 
        sx={{ 
          fontSize: '120px', 
          fontWeight: 700,
          background: `linear-gradient(to right, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          mb: 2
        }}
      >
        404
      </Typography>
      
      <Typography variant="h4" sx={{ mb: 2, fontWeight: 600 }}>
        Page non trouvée
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500 }}>
        La page que vous recherchez n'existe pas ou a été déplacée.
        Veuillez vérifier l'URL ou retourner à la page d'accueil.
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button 
          variant="outlined" 
          startIcon={<ArrowLeft size={18} />}
          onClick={() => navigate(-1)}
        >
          Retour
        </Button>
        <Button 
          variant="contained" 
          startIcon={<Home size={18} />}
          onClick={() => navigate('/')}
        >
          Accueil
        </Button>
      </Box>
    </Box>
  );
};

export default NotFound;