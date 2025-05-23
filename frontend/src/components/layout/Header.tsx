import React, { useState, MouseEvent, useEffect, useCallback } from 'react';
import {
  AppBar, Box, Toolbar, IconButton, Typography, Menu, MenuItem,
  Badge, Tooltip, Avatar, Switch, FormControlLabel, Button
} from '@mui/material';
import { Bell } from 'lucide-react';
import { useApi } from '../../api/client';
import { useTeam } from '../../context/TeamContext';
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
import TeamSelector from '../TeamSelector';

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
  const api = useApi();
  const { token, logout } = useAuth();
  const { teamId, setTeamId } = useTeam();

  // 🆕 état pour les alertes non-lues
  const [alerts, setAlerts] = useState<{ id:number; message:string; project_id:number }[]>([]);
  const [alertsAnchor, setAlertsAnchor] = useState<null|HTMLElement>(null);

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = useState<null | HTMLElement>(null);
// invitation.id inexistant → on ne conserve que team
const [invitations, setInvitations] = useState<{ team: { id:number; name:string } }[]>([])
 
  useEffect(() => {
  // Fetch invitations globally, no teamId needed
  api('/teams/invitations', {
    headers: { Authorization: `Bearer ${token}` }
  })
    .then(r => r.ok ? r.json() : [])
    .then(setInvitations)
    .catch(console.error)
}, [api, token]);


// 🆕 Charger les alertes non-lues pour l’équipe
  useEffect(() => {
    if (!teamId) return;
    api(`/teams/${teamId}/notifications`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : [])
      .then(setAlerts)
      .catch(console.error);
  }, [api, token, teamId]);

  // 🆕 Ouvre/ferme le menu d’alertes
  const openAlertsMenu = (e: MouseEvent<HTMLElement>) => setAlertsAnchor(e.currentTarget);
  const closeAlertsMenu = () => setAlertsAnchor(null);

  // 🆕 Marque une alerte comme lue
  const markAlertRead = async (id:number) => {
    await api(`/teams/${teamId}/notifications/${id}/read`, { method: 'PUT' });
    setAlerts(a => a.filter(x => x.id !== id));
  };

  const handleProfileMenuOpen = (e: MouseEvent<HTMLElement>) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    handleMenuClose();
    logout();
    navigate('/login', { replace: true });
  };

  const handleNotificationMenuOpen = (e: MouseEvent<HTMLElement>) => setNotificationAnchorEl(e.currentTarget);
  const handleNotificationMenuClose = () => setNotificationAnchorEl(null);
const fetchInvitations = useCallback(() => {
  api('/teams/invitations', {
    headers: { Authorization: `Bearer ${token}` }
  })
    .then(r => r.ok ? r.json() : [])
    .then(setInvitations)
    .catch(console.error)
}, [api, token]);

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
           {/* 🆕 Bouton Alertes */}
        <Tooltip title="Alertes non-conformités">
          <IconButton color="inherit" onClick={openAlertsMenu} sx={{ mr: 1 }}>
            <Badge badgeContent={alerts.length} color="warning">
             <Bell size={20} />
            </Badge>
          </IconButton>
        </Tooltip>
          <Tooltip title="Invitations">
          <IconButton color="inherit" onClick={handleNotificationMenuOpen} sx={{ mr: 1 }}>
            <Badge badgeContent={invitations.length} color="error">
              <Notifications size={20} />
            </Badge>
          </IconButton>
        </Tooltip>
          <TeamSelector />
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
        onClick={() => {
       handleMenuClose()
       navigate('/settings')
     }}
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
      {/* 🆕 Menu Alertes */}
      <Menu
  anchorEl={alertsAnchor}
  open={Boolean(alertsAnchor)}
  onClose={closeAlertsMenu}
  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
  transformOrigin={{ vertical: 'top', horizontal: 'right' }}
>
  {alerts.length === 0 ? (
    <MenuItem>Aucune alerte</MenuItem>
  ) : (
    alerts.map(a => (
      <MenuItem
        key={a.id}
        onClick={() => {
          markAlertRead(a.id);
          closeAlertsMenu();
          console.log('Alert clicked:', a); // Pour debug
          // Navigation corrigée
          navigate(`/projects/${a.project_id}`);
        }}
      >
        {a.message}
      </MenuItem>
    ))
  )}
</Menu>
      {/* Menu des invitations */}
      <Menu
       anchorEl={notificationAnchorEl}
        open={Boolean(notificationAnchorEl)}
        onClose={handleNotificationMenuClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        {invitations.length === 0 && (
          <MenuItem>Aucune invitation</MenuItem>
        )}
        {invitations.map(inv => (
          <MenuItem key={inv.team.id} sx={{ whiteSpace: 'normal' }}>
            <Box flexGrow={1}>
              <Typography variant="subtitle2">
                Invitation à rejoindre <b>{inv.team.name}</b>
              </Typography>
            </Box>
            <Button
  size="small"
  onClick={async () => {
    const res = await api(`/teams/${inv.team.id}/members/me/accept`, { method:'PUT' });
    if (res.ok) {
      setTeamId(inv.team.id);  // bascule dans la nouvelle équipe
      fetchInvitations();      // recharge les invitations
    } else {
      alert('Erreur lors de l’acceptation');
    }
  }}
>
  Accepter
</Button>

    <Button
  size="small"
  color="error"
  onClick={async () => {
    const res = await api(`/teams/${inv.team.id}/members/me`, { method:'DELETE' });
    if (res.ok) {
      fetchInvitations();      // recharge les invitations
    } else {
      alert('Erreur lors du refus');
    }
  }}
>
  Refuser
</Button>
          </MenuItem>
        ))}
      </Menu>
    </AppBar>
  );
};

export default Header;
