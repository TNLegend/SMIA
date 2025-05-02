import { ReactNode, useState } from 'react';
import { Box, useMediaQuery, useTheme } from '@mui/material';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: ReactNode;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const Layout = ({ children, darkMode, toggleDarkMode }: LayoutProps) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar 
        open={sidebarOpen} 
        onClose={handleSidebarToggle}
        variant={isMobile ? 'temporary' : 'permanent'}
      />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${sidebarOpen ? 240 : 0}px)` },
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
        }}
      >
        <Header 
          sidebarOpen={sidebarOpen} 
          onSidebarToggle={handleSidebarToggle} 
          darkMode={darkMode}
          toggleDarkMode={toggleDarkMode}
        />
        <Box 
          sx={{ 
            p: 3, 
            pt: 10,
            transition: 'all 0.3s ease',
            backgroundColor: theme.palette.background.default,
            minHeight: 'calc(100vh - 64px)'
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;