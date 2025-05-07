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
import { useAuthFetch } from "../utils/authFetch";
import { useEffect } from 'react'
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
  const authFetch = useAuthFetch()

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
      const res = await authFetch("http://127.0.0.1:8000/auth/login", {
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

      const { access_token } = await res.json();
      login(access_token);
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
