import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Drawer, List, ListItem, ListItemButton, ListItemIcon,
  ListItemText, Divider, Toolbar, Typography, useTheme
} from '@mui/material';
import {
  LayoutDashboard, FileSearch, ShieldAlert, FileBarChart2,
  FileCog, FileText, LogOut as LogOutIcon, BrainCircuit,
Users } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';


interface SidebarProps {
  open: boolean;
  onClose: () => void;
  variant: 'permanent' | 'temporary';
}

const drawerWidth = 240;

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, variant }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();

  const menuItems = [
    { text: 'Tableau de bord', icon: <LayoutDashboard size={20} />, path: '/dashboard' },
    { text: 'Projets IA',      icon: <FileSearch      size={20} />, path: '/projects' },
    { text: 'Équipes',         icon: <Users           size={20} />, path: '/teams' },
    { text: 'Preuves', icon: <FileText size={20}/>, path: '/documents' },

  ];

  const isActive = (path: string) =>
    path === '/'
      ? location.pathname === '/'
      : location.pathname.startsWith(path);

  const drawerContent = (
    <>
      <Toolbar sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 2 }}>
        <BrainCircuit size={28} color={theme.palette.primary.main} />
        <Typography variant="h5" fontWeight={700} color="primary" ml={1}>
          SMIA
        </Typography>
      </Toolbar>
      <Divider />
      <List sx={{ pt: 2 }}>
        {menuItems.map(item => (
          <ListItem key={item.text} disablePadding sx={{ mb: .5 }}>
            <ListItemButton
              onClick={() => {
                navigate(item.path);
                if (variant === 'temporary') onClose();
              }}
              selected={isActive(item.path)}
              sx={{
                mx: 1, borderRadius: 2,
                '&.Mui-selected': {
                  bgcolor: theme.palette.mode === 'dark'
                    ? 'rgba(67,97,238,0.15)'
                    : 'rgba(67,97,238,0.1)',
                  color: theme.palette.primary.main,
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Box sx={{ flexGrow: 1 }} />
      <Divider sx={{ mb: 1 }} />
      <List>
        <ListItem disablePadding>
          <ListItemButton
            onClick={() => {
              logout();
              navigate('/login', { replace: true });
            }}
            sx={{ mx: 1, borderRadius: 2 }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>
              <LogOutIcon size={20} />
            </ListItemIcon>
            <ListItemText primary="Déconnexion" />
          </ListItemButton>
        </ListItem>
      </List>
    </>
  );

  return (
    <Box component="nav" sx={{ width: { sm: open ? drawerWidth : 0 }, flexShrink: { sm: 0 } }}>
      {variant === 'temporary' ? (
        <Drawer
          variant="temporary"
          open={open}
          onClose={onClose}
          ModalProps={{ keepMounted: true }}
          sx={{ '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' } }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        <Drawer
          variant="persistent"
          open={open}
          sx={{ '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' } }}
        >
          {drawerContent}
        </Drawer>
      )}
    </Box>
  );
};

export default Sidebar;
