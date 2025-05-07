import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Button, TextField, Grid,
  MenuItem, FormControl, InputLabel, Select,
  CircularProgress, Paper
} from '@mui/material';
import { ArrowLeft, Check, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface NewProjectPayload {
  name: string;
  description: string;
  category: string;
  status: 'draft'|'active'|'completed'|'on-hold';
}

export default function NewProject() {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  const [payload, setPayload] = useState<NewProjectPayload>({
    name: '', description:'', category:'', status:'draft'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState<string|null>(null);

  const handleChange = (e:any) => {
    setPayload({ ...payload, [e.target.name]: e.target.value });
  };

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/projects/', {
        method: 'POST',
        headers: {
          'Content-Type':'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      if (res.status===401) {
        logout();
        return;
      }
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      navigate(`/projects/${data.id}`);
    } catch (err:any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={4}>
        <Button startIcon={<ArrowLeft/>} onClick={()=>navigate(-1)} sx={{mr:2}}>Retour</Button>
        <Typography variant="h4">Nouveau projet</Typography>
      </Box>

      <Paper sx={{ p:4, position:'relative' }}>
        {loading && (
          <Box
            sx={{
              position:'absolute', inset:0,
              bgcolor:'rgba(255,255,255,0.7)',
              display:'flex', alignItems:'center', justifyContent:'center'
            }}
          >
            <CircularProgress/>
          </Box>
        )}

        {error && <Typography color="error" mb={2}>{error}</Typography>}

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              name="name" label="Nom du projet"
              value={payload.name} onChange={handleChange}
              fullWidth required
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              name="description" label="Description"
              value={payload.description} onChange={handleChange}
              fullWidth multiline rows={4} required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth required>
              <InputLabel>Catégorie</InputLabel>
              <Select
                name="category"
                value={payload.category}
                label="Catégorie"
                onChange={handleChange}
              >
                <MenuItem value="Marketing">Marketing</MenuItem>
                <MenuItem value="Production">Production</MenuItem>
                <MenuItem value="Finance">Finance</MenuItem>
                <MenuItem value="Service client">Service client</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth required>
              <InputLabel>Statut</InputLabel>
              <Select
                name="status"
                value={payload.status}
                label="Statut"
                onChange={handleChange}
              >
                <MenuItem value="draft">Brouillon</MenuItem>
                <MenuItem value="active">Actif</MenuItem>
                <MenuItem value="completed">Termin&eacute;</MenuItem>
                <MenuItem value="on-hold">En pause</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <Box display="flex" justifyContent="flex-end" gap={2} mt={4}>
          <Button startIcon={<X/>} onClick={()=>navigate(-1)} disabled={loading}>
            Annuler
          </Button>
          <Button variant="contained" endIcon={<Check/>} onClick={submit} disabled={loading}>
            Créer
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
