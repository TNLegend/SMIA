import React, { ReactNode, useState } from 'react';
import Box from '@mui/material/Box';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: ReactNode;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const drawerWidth = 240;

const Layout: React.FC<LayoutProps> = ({
  children,
  darkMode,
  toggleDarkMode
}) => {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar
        open={sidebarOpen}
        onClose={handleSidebarToggle}
        variant="permanent"
      />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${sidebarOpen ? drawerWidth : 0}px)` }
        }}
      >
        <Header
          sidebarOpen={sidebarOpen}
          onSidebarToggle={handleSidebarToggle}
          darkMode={darkMode}
          toggleDarkMode={toggleDarkMode}
        />
        <Box sx={{ p: 3, pt: 10 }}>{children}</Box>
      </Box>
    </Box>
  );
};

export default Layout;
