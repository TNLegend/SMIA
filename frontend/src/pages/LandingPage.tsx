import React from "react";
import { Box, Card, CardContent, Typography, Button, Switch, useTheme, useMediaQuery } from "@mui/material";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
interface LandingPageProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}


const LandingPage: React.FC<LandingPageProps> = ({ darkMode, toggleDarkMode }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard')
  }, [isAuthenticated, navigate])
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: darkMode
          ? "linear-gradient(135deg, #081229 0%, #0f1a40 100%)"
          : theme.palette.background.default,
        p: 2,
      }}
    >
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }}>
        <Card
          elevation={8}
          sx={{
            position: "relative",
            maxWidth: 600,
            width: isMobile ? "90vw" : 600,
            borderRadius: 4,
            p: { xs: 2, sm: 4 },
            bgcolor: theme.palette.mode === "dark" ? "#0F1A40" : "#FFF",
            boxShadow: theme.shadows[20],
          }}
        >
          {/* Toggle */}
          <Box sx={{ position: "absolute", top: 16, right: 16 }}>
            <Switch
              checked={darkMode}
              onChange={toggleDarkMode}
              inputProps={{ "aria-label": "Basculer thème clair/sombre" }}
            />
          </Box>

          <CardContent>
            <Typography variant="h4" align="center" gutterBottom sx={{ fontWeight: 700 }}>
              Bienvenue sur SMIA
            </Typography>
            <Typography variant="body1" align="center" paragraph>
              Gérez votre Système de Management de l’IA (SMIA) de façon simple et conforme à l’ISO 42001.
            </Typography>
            <Box sx={{ display: "flex", justifyContent: "center", gap: 2, mt: 3 }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate("/signup")}
                sx={{ minWidth: 160 }}
              >
                Créer un compte
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate("/login")}
                sx={{ minWidth: 160 }}
              >
                Se connecter
              </Button>
            </Box>
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default LandingPage;
