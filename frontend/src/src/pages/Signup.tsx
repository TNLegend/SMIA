import React, { useState, FormEvent, useMemo } from "react";
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
  LinearProgress,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import { motion } from "framer-motion";
import { useApi } from "../api/client";
import { useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { Api } from "@mui/icons-material";


interface SignupProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const USERNAME_REGEX = /^[A-Za-z0-9_]{3,30}$/;
const MIN_PASSWORD_LENGTH = 8;

const scorePassword = (pwd: string): number => {
  let score = 0;
  if (pwd.length >= MIN_PASSWORD_LENGTH) score++;
  if (/[A-Z]/.test(pwd)) score++;
  if (/[a-z]/.test(pwd)) score++;
  if (/\d/.test(pwd)) score++;
  if (/[^A-Za-z0-9]/.test(pwd)) score++;
  return score;
};



const strengthColor = (score: number) =>
  score <= 2 ? "error" : score === 3 ? "warning" : "success";

const Signup: React.FC<SignupProps> = ({ darkMode, toggleDarkMode }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth()
useEffect(() => {
  if (isAuthenticated) navigate('/dashboard')
}, [isAuthenticated, navigate])
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const pwdScore = useMemo(() => scorePassword(password), [password]);
  const isFormValid = USERNAME_REGEX.test(username) && pwdScore >= 4;
  const api = useApi();


  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!isFormValid) {
      setError("Veuillez corriger les champs avant d’envoyer");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const body = new URLSearchParams({ username, password });
      const res = await api("/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      if (res.status === 201) {
        navigate("/login");
      } else {
        const payload = await res.json();
        throw new Error(
          Array.isArray(payload.detail)
            ? payload.detail.map((d: any) => d.msg).join(", ")
            : payload.detail || "Erreur lors de l’inscription"
        );
      }
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
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
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
            <Switch checked={darkMode} onChange={toggleDarkMode} inputProps={{ "aria-label": "Basculer thème clair/sombre" }} />
          </Box>

          <CardContent>
            <Typography variant="h5" align="center" gutterBottom>
              Créer un compte
            </Typography>

            <Box component="form" onSubmit={handleSubmit} noValidate>
              <TextField
                fullWidth
                margin="normal"
                label="Nom d’utilisateur"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                error={Boolean(error) || !USERNAME_REGEX.test(username)}
                helperText={
                  username && !USERNAME_REGEX.test(username)
                    ? "3–30 caractères alphanumériques ou _"
                    : undefined
                }
              />

              <TextField
                fullWidth
                margin="normal"
                type="password"
                label="Mot de passe"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={Boolean(error) || pwdScore < 4}
              />

              {/* Barre de force */}
              {password && (
                <Box sx={{ mt: 1 }}>
                  <LinearProgress variant="determinate" value={(pwdScore / 5) * 100} color={strengthColor(pwdScore)} />
                  <Typography variant="caption" sx={{ color: theme.palette.text.secondary }}>
                    Force :{" "}
                    {["Très faible", "Faible", "Moyenne", "Bonne", "Excellente"][Math.min(pwdScore, 4)]}
                  </Typography>
                </Box>
              )}

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
                disabled={loading || !isFormValid}
                sx={{
                  mt: 1,
                  transition: "transform 0.2s",
                  "&:hover": { transform: "scale(1.02)" },
                }}
              >
                {loading ? "Inscription..." : "S’inscrire"}
              </Button>
            </Box>

            {/* Liens secondaires */}
            <Box textAlign="center" mt={1}>
              <Typography variant="caption" component="div" sx={{ fontSize: "0.85rem", color: theme.palette.text.secondary }}>
                Déjà un compte ?{" "}
                <Button onClick={() => navigate("/login")} size="small" sx={{ p: 0, minWidth: 0, fontSize: "0.85rem" }}>
                  Connectez-vous
                </Button>
              </Typography>
              <Button
                onClick={() => navigate("/")}
                size="small"
                sx={{ mt: 0.5, p: 0, minWidth: 0, fontSize: "0.85rem", color: theme.palette.text.secondary }}
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

export default Signup;
