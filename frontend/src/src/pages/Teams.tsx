import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  IconButton,
  CircularProgress,
  Alert
} from '@mui/material';
import { Plus, Check, X } from 'lucide-react';
import { useApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { useTeam } from '../context/TeamContext';

// --- Types TS ---
interface Team { id: number; name: string; }
interface Invitation { team: Team; }

export default function TeamsPage() {
  const api = useApi();
  const { logout } = useAuth();

  // Récupération du contexte teams global
  const { teams, setTeams } = useTeam();

  const [tab, setTab] = useState(0);
  const [invites, setInvites] = useState<Invitation[]>([]);
  const [loadingInvites, setLoadingInvites] = useState(true);
  const [loadingTeams, setLoadingTeams] = useState(teams.length === 0);
  const [error, setError] = useState<string | null>(null);

  // création d'équipe
  const [openCreate, setOpenCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  // Fonction pour charger la liste des équipes
  const loadTeams = async () => {
    setLoadingTeams(true);
    setError(null);
    try {
      const r = await api('/teams');
      if (r.status === 401) {
        logout();
        return;
      }
      if (!r.ok) throw new Error('Erreur de chargement des équipes');
      const data = await r.json();
      setTeams(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoadingTeams(false);
    }
  };

  // Charger la liste des équipes seulement si non déjà chargée dans le contexte
  useEffect(() => {
    if (teams.length === 0) {
      loadTeams();
    } else {
      setLoadingTeams(false);
    }
  }, [teams.length]);

  // Charger uniquement les invitations (teams sont chargées dans TeamProvider)
  useEffect(() => {
    setLoadingInvites(true);
    api('/teams/invitations')
      .then(async (r) => {
        if (r.status === 401) {
          logout();
          return;
        }
        if (!r.ok) throw new Error('Erreur de chargement des invitations');
        setInvites(await r.json());
      })
      .catch((e: any) => setError(e.message))
      .finally(() => setLoadingInvites(false));
  }, [api, logout]);

  /** Accepte ou refuse mon invitation via les nouvelles routes */
  const respond = async (teamId: number, accept: boolean) => {
    const url = accept
      ? `/teams/${teamId}/members/me/accept`
      : `/teams/${teamId}/members/me`;
    const res = await api(url, { method: accept ? 'PUT' : 'DELETE' });
    if (res.status === 401) { logout(); return; }
    if (!res.ok) return alert('Impossible de répondre');
    setInvites(invites.filter(i => i.team.id !== teamId));
  };

  // création équipe
  const createTeam = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const res = await api('/teams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName }),
      });
      if (res.status === 401) { logout(); return; }
      if (!res.ok) throw new Error('Erreur création');
      // const newTeam = await res.json(); // plus nécessaire de stocker ici
      setNewName('');
      setOpenCreate(false);
      setTab(0); // Optionnel : revenir à l'onglet "Mes équipes" après création
      await loadTeams(); // Recharge la liste des équipes pour être à jour
    } catch (e: any) {
      alert(e.message);
    } finally {
      setCreating(false);
    }
  };

  if (loadingTeams || loadingInvites) {
    return (
      <Box textAlign="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Équipes</Typography>
        <Button
          startIcon={<Plus />}
          variant="contained"
          onClick={() => setOpenCreate(true)}
        >
          Créer une équipe
        </Button>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Mes équipes" />
        <Tab label="Invitations" />
      </Tabs>

      {tab === 0 && (
        teams.length > 0
          ? (
            <List>
              {teams.map(t => (
                <ListItem
                  key={t.id}
                  button
                  component={Link}
                  to={`/teams/${t.id}`}
                >
                  <ListItemText primary={t.name} />
                </ListItem>
              ))}
            </List>
          )
          : <Typography>Aucune équipe</Typography>
      )}

      {tab === 1 && (
        invites.length > 0
          ? (
            <List>
              {invites.map(i => (
                <ListItem
                  key={i.team.id}
                  secondaryAction={
                    <>
                      <IconButton onClick={() => respond(i.team.id, true)}><Check /></IconButton>
                      <IconButton onClick={() => respond(i.team.id, false)}><X /></IconButton>
                    </>
                  }
                >
                  <ListItemText primary={i.team.name} secondary="Invitation en attente" />
                </ListItem>
              ))}
            </List>
          )
          : <Typography>Aucune invitation</Typography>
      )}

      <Dialog open={openCreate} onClose={() => setOpenCreate(false)}>
        <DialogTitle>Créer une équipe</DialogTitle>
        <DialogContent>
          <TextField
            label="Nom de l’équipe"
            fullWidth
            value={newName}
            onChange={e => setNewName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button disabled={creating} onClick={() => setOpenCreate(false)}>Annuler</Button>
          <Button
            variant="contained"
            disabled={!newName.trim() || creating}
            onClick={createTeam}
          >
            {creating ? '…' : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
