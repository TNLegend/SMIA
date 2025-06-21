import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  TextField,
  Button,
  CircularProgress,
  Alert,
  IconButton,
} from "@mui/material";
import { Trash2 as DeleteIcon } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import { useApi } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useTeam } from "../context/TeamContext";
import { jwtDecode } from "jwt-decode";

interface Team {
  id: number;
  name: string;
  owner_id: number;
}

interface Member {
  user_id: number;
  team_id: number;
  role: string;
  invited_at: string;
  accepted_at: string | null;
  revoked_at: string | null;
  user?: { username: string };
}

export default function TeamDetailPage() {
  /* ─── Hooks & helpers ──────────────────────────────────────────────── */
  const { teamId } = useParams<{ teamId: string }>();
  const api = useApi();
  const { setTeamId } = useTeam();
  const navigate = useNavigate();
  const { token } = useAuth();

  // id du user courant (décodé depuis le JWT)
  const currentUserId = token ? Number(jwtDecode<{ sub: string }>(token).sub) : null;

  /* ─── State ────────────────────────────────────────────────────────── */
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // invitation
  const [newUser, setNewUser] = useState("");
  const [inviteError, setInviteError] = useState<string | null>(null);

  /* ─── Load team + members ──────────────────────────────────────────── */
  useEffect(() => {
    if (!teamId) return;

    setLoading(true);
    Promise.all([
      api(`/teams/${teamId}`),
      api(`/teams/${teamId}/members`),
    ])
      .then(async ([rTeam, rMembers]) => {
        if (!rTeam.ok) throw new Error("Équipe introuvable");
        if (!rMembers.ok) throw new Error("Impossible de charger les membres");

        const t = await rTeam.json();
        setTeam(t);
        setTeamId(t.id);
        setMembers(await rMembers.json());
      })
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [api, teamId]);

  /* ─── Actions propriétaires ───────────────────────────────────────── */
  const isOwner = team && currentUserId === team.owner_id;

  const deleteTeam = async () => {
    if (!isOwner) return;
    if (!confirm("Supprimer cette équipe ?")) return;

    const res = await api(`/teams/${teamId}`, { method: "DELETE" });
    if (!res.ok) return alert("Erreur suppression équipe");
    navigate("/teams");
  };

  const removeMember = async (userId: number) => {
    if (!isOwner || userId === currentUserId) return;
    if (!confirm("Retirer ce membre ?")) return;

    const res = await api(`/teams/${teamId}/members/${userId}`, {
      method: "DELETE",
    });
    if (!res.ok) return alert("Erreur suppression membre");
    setMembers((list) => list.filter((m) => m.user_id !== userId));
  };

  /* ─── Inviter un membre ────────────────────────────────────────────── */
  const inviteMember = async () => {
    if (!newUser.trim()) return;

    try {
      const res = await api(`/teams/${teamId}/members`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: newUser }),
      });

      const payload = await res.json().catch(() => null);
      if (!res.ok) throw new Error(payload?.detail ?? "Erreur d’invitation");

      setMembers((list) => [...list, payload]);
      setNewUser("");
      setInviteError(null);
    } catch (e: any) {
      setInviteError(e.message);
    }
  };

  /* ─── Render ───────────────────────────────────────────────────────── */
  if (loading) return <Box textAlign="center"><CircularProgress /></Box>;
  if (error)   return <Alert severity="error">{error}</Alert>;

  return (
    <Box p={2}>
      {/* Titre + bouton supprimer */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Équipe : {team?.name ?? `#${teamId}`}</Typography>

        {isOwner && (
          <Button color="error" variant="outlined" onClick={deleteTeam}>
            Supprimer l’équipe
          </Button>
        )}
      </Box>

      {/* Liste des membres */}
      <Typography variant="h6" gutterBottom>Membres</Typography>
      <List>
        {members.map((m) => (
          <ListItem
            key={m.user_id}
            secondaryAction={
              isOwner && m.user_id !== currentUserId && (
                <IconButton edge="end" onClick={() => removeMember(m.user_id)}>
                  <DeleteIcon size={18} />
                </IconButton>
              )
            }
          >
            <ListItemText
              primary={m.user?.username ?? `User ${m.user_id}`}
              secondary={`Rôle : ${m.role}`}
            />
          </ListItem>
        ))}
      </List>

      {/* Section invitation */}
      <Box mt={4}>
        <Typography variant="subtitle1">Inviter un membre</Typography>

        <Box display="flex" alignItems="center" mt={1}>
          <TextField
            label="Nom d’utilisateur"
            value={newUser}
            onChange={(e) => setNewUser(e.target.value)}
            size="small"
          />
          <Button variant="contained" sx={{ ml: 2 }} onClick={inviteMember}>
            Inviter
          </Button>
        </Box>

        {inviteError && (
          <Box mt={2}>
            <Alert severity="error">{inviteError}</Alert>
          </Box>
        )}
      </Box>
    </Box>
  );
}
