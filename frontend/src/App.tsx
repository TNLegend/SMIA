import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme } from './theme';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import NewProject from './pages/NewProject';
import AIPolicy from './pages/AIPolicy';
import RiskAnalysis from './pages/RiskAnalysis';
import Reports from './pages/Reports';
import NotFound from './pages/NotFound';

function App() {
  const [darkMode, setDarkMode] = useState<boolean>(true);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={theme(darkMode)}>
      <CssBaseline />
      <Router>
        <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/new" element={<NewProject />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/policy" element={<AIPolicy />} />
            <Route path="/risk-analysis" element={<RiskAnalysis />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;