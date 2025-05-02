import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Toolbar,
  Typography,
  useTheme
} from '@mui/material';
import { 
  LayoutDashboard, 
  FileSearch, 
  ShieldAlert, 
  FileBarChart2, 
  FileCog,
  Settings,
  LogOut,
  BrainCircuit
} from 'lucide-react';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  variant: 'permanent' | 'temporary';
}

const drawerWidth = 240;

const Sidebar = ({ open, onClose, variant }: SidebarProps) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  
  const menuItems = [
    { text: 'Tableau de bord', icon: <LayoutDashboard size={20} />, path: '/' },
    { text: 'Projets IA', icon: <FileSearch size={20} />, path: '/projects' },
    { text: 'Politique IA', icon: <FileCog size={20} />, path: '/policy' },
    { text: 'Analyse des risques', icon: <ShieldAlert size={20} />, path: '/risk-analysis' },
    { text: 'Rapports', icon: <FileBarChart2 size={20} />, path: '/reports' },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
    if (variant === 'temporary') {
      onClose();
    }
  };

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const drawer = (
    <>
      <Toolbar 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          py: 2
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BrainCircuit 
            size={28} 
            color={theme.palette.primary.main} 
          />
          <Typography variant="h5" fontWeight={700} color="primary">
            SMIA
          </Typography>
        </Box>
      </Toolbar>
      
      <Divider />
      
      <List sx={{ pt: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton 
              onClick={() => handleNavigation(item.path)}
              selected={isActive(item.path)}
              sx={{
                mx: 1,
                borderRadius: 2,
                '&.Mui-selected': {
                  bgcolor: theme.palette.mode === 'dark' 
                    ? 'rgba(67, 97, 238, 0.15)'
                    : 'rgba(67, 97, 238, 0.1)',
                  color: theme.palette.primary.main,
                  '&:hover': {
                    bgcolor: theme.palette.mode === 'dark' 
                      ? 'rgba(67, 97, 238, 0.25)'
                      : 'rgba(67, 97, 238, 0.15)',
                  },
                  '& .MuiListItemIcon-root': {
                    color: theme.palette.primary.main,
                  },
                },
                '&:hover': {
                  bgcolor: theme.palette.mode === 'dark' 
                    ? 'rgba(255, 255, 255, 0.05)'
                    : 'rgba(0, 0, 0, 0.05)',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      
      <Box sx={{ flexGrow: 1 }} />
      
      <List sx={{ mt: 'auto' }}>
        <Divider sx={{ mb: 1 }} />
        <ListItem disablePadding>
          <ListItemButton sx={{ mx: 1, borderRadius: 2 }}>
            <ListItemIcon sx={{ minWidth: 40 }}>
              <Settings size={20} />
            </ListItemIcon>
            <ListItemText primary="Paramètres" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton sx={{ mx: 1, borderRadius: 2 }}>
            <ListItemIcon sx={{ minWidth: 40 }}>
              <LogOut size={20} />
            </ListItemIcon>
            <ListItemText primary="Déconnexion" />
          </ListItemButton>
        </ListItem>
      </List>
    </>
  );

  return (
    <Box
      component="nav"
      sx={{
        width: { sm: open ? drawerWidth : 0 },
        flexShrink: { sm: 0 },
      }}
    >
      {variant === 'temporary' ? (
        <Drawer
          variant="temporary"
          open={open}
          onClose={onClose}
          ModalProps={{ keepMounted: true }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: 'none',
              boxShadow: 3,
            },
          }}
        >
          {drawer}
        </Drawer>
      ) : (
        <Drawer
          variant="persistent"
          sx={{
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
              borderRight: `1px solid ${theme.palette.divider}`,
              transition: theme.transitions.create(['width', 'margin'], {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
              ...(!open && {
                width: 0,
              }),
            },
          }}
          open={open}
        >
          {drawer}
        </Drawer>
      )}
    </Box>
  );
};

export default Sidebar;