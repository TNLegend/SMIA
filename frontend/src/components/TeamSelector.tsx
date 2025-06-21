import React from 'react';
import { Select, MenuItem } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTeam } from '../context/TeamContext';

export default function TeamSelector() {
  const { teamId, setTeamId, teams } = useTeam();
  const navigate = useNavigate();
  const location = useLocation();

  const handleChange = (e: any) => {
    const id = Number(e.target.value);
    setTeamId(id);
    if (location.pathname.startsWith('/teams/')) {
      navigate(`/teams/${id}`, { replace: true });
    }
  };

  return (
    <Select
      value={teamId ?? ''}
      size="small"
      onChange={handleChange}
      sx={{ color: 'inherit', ml: 2 }}
      displayEmpty
      renderValue={v => teams.find(t => t.id === v)?.name || 'Sélection équipe'}
    >
      {teams.map(t => (
        <MenuItem key={t.id} value={t.id}>
          {t.name}
        </MenuItem>
      ))}
    </Select>
  );
}
