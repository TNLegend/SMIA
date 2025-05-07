import React, { useState, MouseEvent } from 'react';
import {
  AppBar, Box, Toolbar, IconButton, Typography, Menu, MenuItem,
  Badge, Tooltip, Avatar, Switch, FormControlLabel
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import {
  Menu as MenuIcon,
  Captions as Notifications,
  Search,
  HelpCircle,
  Settings as SettingsIcon,
  User as UserIcon,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  sidebarOpen: boolean;
  onSidebarToggle: () => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const Header: React.FC<HeaderProps> = ({
  sidebarOpen,
  onSidebarToggle,
  darkMode,
  toggleDarkMode
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (e: MouseEvent<HTMLElement>) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    handleMenuClose();
    logout();
    navigate('/login', { replace: true });
  };

  const handleNotificationMenuOpen = (e: MouseEvent<HTMLElement>) => setNotificationAnchorEl(e.currentTarget);
  const handleNotificationMenuClose = () => setNotificationAnchorEl(null);

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        zIndex: theme.zIndex.drawer + 1,
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
            <IconButton color="inherit" onClick={handleNotificationMenuOpen} sx={{ mr: 1 }}>
              <Badge badgeContent={3} color="error">
                <Notifications size={20} />
              </Badge>
            </IconButton>
          </Tooltip>
          <FormControlLabel
            control={<Switch checked={darkMode} onChange={toggleDarkMode} size="small" color="default" />}
            label=""
          />
          <Tooltip title="Profil">
            <IconButton edge="end" onClick={handleProfileMenuOpen} color="inherit">
              <Avatar sx={{ width: 32, height: 32, bgcolor: theme.palette.primary.main }}>
                <UserIcon size={18} />
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleMenuClose}>Mon profil</MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <SettingsIcon size={16} style={{ marginRight: 8 }} />
          Paramètres
        </MenuItem>
        <MenuItem onClick={handleLogout} sx={{ color: theme.palette.error.main }}>
          Déconnexion
        </MenuItem>
      </Menu>

      <Menu
        anchorEl={notificationAnchorEl}
        open={Boolean(notificationAnchorEl)}
        onClose={handleNotificationMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleNotificationMenuClose}>
          <Typography variant="subtitle2">Nouveau projet créé</Typography>
          <Typography variant="caption" color="text.secondary">
            Il y a 5 minutes
          </Typography>
        </MenuItem>
        {/* … autres notifications … */}
      </Menu>
    </AppBar>
  );
};

export default Header;
