import React, { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Switch,
  FormHelperText,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { useApi } from "../api/client";
import { useEffect } from 'react'
import { useTeam } from '../context/TeamContext';

interface LoginProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const Login: React.FC<LoginProps> = ({ darkMode, toggleDarkMode }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const api = useApi()
  const { setTeamId } = useTeam();

  const { isAuthenticated } = useAuth()
    useEffect(() => {
      if (isAuthenticated) navigate('/dashboard')
    }, [isAuthenticated, navigate])


  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError("Veuillez remplir tous les champs");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const body = new URLSearchParams({ username, password });
      const res = await api("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      if (!res.ok) {
        const payload = await res.json();
        throw new Error(
          Array.isArray(payload.detail)
            ? payload.detail.map((d: any) => d.msg).join(", ")
            : payload.detail || "Erreur d’authentification"
        );
      }

     // 1) on récupère le token et on l’enregistre
      const { access_token } = await res.json();
      login(access_token);

      // 2) on charge la première équipe disponible
      try {
        const teamsRes = await api("/teams/", {
          headers: { Authorization: `Bearer ${access_token}` }
        });
        if (teamsRes.ok) {
          const teams = await teamsRes.json();
          if (teams.length > 0) {
            setTeamId(teams[0].id);            // ← on stocke la 1ʳᵉ équipe
          }
        }
      } catch (e) {
        console.error("Impossible de récupérer la liste des équipes", e);
      }

      // 3) redirection finale
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

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
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Card
          elevation={6}
          sx={{
            position: "relative",
            maxWidth: 600,
            width: isMobile ? "90vw" : 600,
            borderRadius: 3,
            p: { xs: 2, sm: 4 },
            bgcolor: theme.palette.mode === "dark" ? "#0F1A40" : "#FFF",
            boxShadow: theme.shadows[12],
          }}
        >
          {/* Switch thème */}
          <Box sx={{ position: "absolute", top: 16, right: 16 }}>
            <Switch
              checked={darkMode}
              onChange={toggleDarkMode}
              inputProps={{ "aria-label": "Basculer thème clair/sombre" }}
            />
          </Box>

          <CardContent>
            <Typography variant="h5" align="center" gutterBottom>
              Connexion
            </Typography>

            <Box component="form" onSubmit={handleSubmit} noValidate>
              <TextField
                fullWidth
                margin="normal"
                label="Nom d’utilisateur"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                error={Boolean(error)}
              />
              <TextField
                fullWidth
                margin="normal"
                type="password"
                label="Mot de passe"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={Boolean(error)}
              />
              {error && (
                <FormHelperText error sx={{ mb: 2 }}>
                  {error}
                </FormHelperText>
              )}
              <Button
                type="submit"
                variant="contained"
                color="primary"
                fullWidth
                size="large"
                disabled={loading}
                sx={{
                  mt: 1,
                  transition: "transform 0.2s",
                  "&:hover": { transform: "scale(1.02)" },
                }}
              >
                {loading ? "Connexion..." : "Se connecter"}
              </Button>
            </Box>

            {/* Liens secondaires */}
            <Box textAlign="center" mt={1}>
              <Typography
                variant="caption"
                component="div"
                sx={{
                  fontSize: "0.85rem",
                  color: theme.palette.text.secondary,
                }}
              >
                Pas encore de compte ?{" "}
                <Button
                  onClick={() => navigate("/signup")}
                  size="small"
                  sx={{ p: 0, minWidth: 0, fontSize: "0.85rem" }}
                >
                  Inscrivez-vous
                </Button>
              </Typography>
              <Button
                onClick={() => navigate("/")}
                size="small"
                sx={{
                  mt: 0.5,
                  p: 0,
                  minWidth: 0,
                  fontSize: "0.85rem",
                  color: theme.palette.text.secondary,
                }}
              >
                ← Retour à l’accueil
              </Button>
            </Box>
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default Login;
