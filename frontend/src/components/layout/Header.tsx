import { useState } from 'react';
import { 
  AppBar, 
  Box, 
  Toolbar, 
  IconButton, 
  Typography, 
  Menu, 
  MenuItem, 
  Badge, 
  Tooltip, 
  Avatar,
  Switch,
  FormControlLabel
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { Menu as MenuIcon, Captions as Notifications, Search, HelpCircle, Settings, User } from 'lucide-react';

interface HeaderProps {
  sidebarOpen: boolean;
  onSidebarToggle: () => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const Header = ({ 
  sidebarOpen, 
  onSidebarToggle, 
  darkMode, 
  toggleDarkMode 
}: HeaderProps) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationMenuClose = () => {
    setNotificationAnchorEl(null);
  };

  return (
    <AppBar 
      position="fixed" 
      elevation={0}
      sx={{
        zIndex: theme.zIndex.drawer + 1,
        transition: 'all 0.3s ease',
        backdropFilter: 'blur(8px)',
        backgroundColor: darkMode 
          ? 'rgba(10, 17, 40, 0.8)' 
          : 'rgba(255, 255, 255, 0.8)',
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onSidebarToggle}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>
        
        <Typography
          variant="h6"
          noWrap
          component="div"
          sx={{ display: { xs: 'none', sm: 'block' }, fontWeight: 600 }}
        >
          SMIA
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title="Rechercher">
            <IconButton color="inherit" sx={{ mr: 1 }}>
              <Search size={20} />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Aide">
            <IconButton color="inherit" sx={{ mr: 1 }}>
              <HelpCircle size={20} />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Notifications">
            <IconButton 
              color="inherit"
              onClick={handleNotificationMenuOpen}
              sx={{ mr: 1 }}
            >
              <Badge badgeContent={3} color="error">
                <Notifications size={20} />
              </Badge>
            </IconButton>
          </Tooltip>
          
          <FormControlLabel
            control={
              <Switch
                checked={darkMode}
                onChange={toggleDarkMode}
                size="small"
                color="default"
              />
            }
            label=""
          />
          
          <Tooltip title="Profil">
            <IconButton
              edge="end"
              aria-label="account of current user"
              aria-haspopup="true"
              onClick={handleProfileMenuOpen}
              color="inherit"
            >
              <Avatar 
                sx={{ 
                  width: 32, 
                  height: 32, 
                  bgcolor: theme.palette.primary.main 
                }}
              >
                <User size={18} />
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
      
      <Menu
        anchorEl={anchorEl}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>Mon profil</MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Settings size={16} style={{ marginRight: 8 }} />
          Paramètres
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>Déconnexion</MenuItem>
      </Menu>
      
      <Menu
        anchorEl={notificationAnchorEl}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        open={Boolean(notificationAnchorEl)}
        onClose={handleNotificationMenuClose}
      >
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography variant="subtitle2">Nouveau projet créé</Typography>
            <Typography variant="caption" color="text.secondary">
              Il y a 5 minutes
            </Typography>
          </Box>
        </MenuItem>
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography variant="subtitle2">Alerte de risque élevé</Typography>
            <Typography variant="caption" color="text.secondary">
              Il y a 1 heure
            </Typography>
          </Box>
        </MenuItem>
        <MenuItem onClick={handleNotificationMenuClose}>
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography variant="subtitle2">Mise à jour de politique</Typography>
            <Typography variant="caption" color="text.secondary">
              Hier à 14:00
            </Typography>
          </Box>
        </MenuItem>
      </Menu>
    </AppBar>
  );
};

export default Header;