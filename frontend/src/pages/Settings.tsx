import React, { useState, useEffect, FormEvent } from 'react'
import {
  Box, TextField, Button, Typography, Alert, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogContentText,
  DialogActions
} from '@mui/material'
import { useAuth } from '../context/AuthContext'
import { useApi } from '../api/client'


interface UserProfile { username: string }

export default function Settings() {
  const api = useApi()
  const { logout } = useAuth()

  const [profile, setProfile] = useState<UserProfile>({ username: '' })
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [success, setSuccess]   = useState(false)

  // Delete confirmation dialog
  const [openDel, setOpenDel] = useState(false)
  const handleOpenDel = () => setOpenDel(true)
  const handleCloseDel = () => setOpenDel(false)

  // 1) Load current profile (only once on mount)
  useEffect(() => {
    ;(async () => {
      try {
        const res = await api(`/auth/me`)
        if (!res.ok) throw new Error(`Load failed (${res.status})`)
        const data = await res.json()
        setProfile({ username: data.username })
      } catch (e: any) {
        setError(e.message)
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 2) Update username / password
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (password && password !== confirm) {
      setError("Les mots de passe ne correspondent pas")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const body: any = { username: profile.username }
      if (password) body.password = password

      const res = await api(`/auth/me`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`Update failed (${res.status})`)
      setSuccess(true)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // 3) Delete account
  const handleDelete = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api(`/auth/me`, { method: 'DELETE' })
      if (res.status !== 204) throw new Error(`Delete failed (${res.status})`)
      logout()  // kicks back to login
    } catch (e: any) {
      setError(e.message)
      setLoading(false)
      setOpenDel(false)
    }
  }

  return (
    <Box maxWidth={480} mx="auto">
      <Typography variant="h5" mb={2}>Paramètres du profil</Typography>
      {error   && <Alert severity="error"   sx={{ mb:2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb:2 }}>Profil mis à jour !</Alert>}

      <form onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Nom d’utilisateur"
          value={profile.username}
          onChange={e => setProfile({ username: e.target.value })}
          sx={{ mb:2 }}
        />
        <TextField
          fullWidth
          type="password"
          label="Nouveau mot de passe"
          value={password}
          onChange={e => setPassword(e.target.value)}
          sx={{ mb:2 }}
        />
        <TextField
          fullWidth
          type="password"
          label="Confirmer mot de passe"
          value={confirm}
          onChange={e => setConfirm(e.target.value)}
          sx={{ mb:2 }}
        />

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Button
            onClick={handleOpenDel}
            color="error"
            disabled={loading}
          >
            Supprimer mon compte
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
          >
            {loading ? <CircularProgress size={20} /> : 'Enregistrer'}
          </Button>
        </Box>
      </form>

      {/* Confirmation Dialog */}
      <Dialog open={openDel} onClose={handleCloseDel}>
        <DialogTitle>Supprimer mon compte</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Cette action est irréversible : toutes vos données seront perdues.
            Voulez-vous vraiment supprimer votre compte ?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDel} disabled={loading}>Annuler</Button>
          <Button
            onClick={handleDelete}
            color="error"
            disabled={loading}
          >
            {loading ? <CircularProgress size={20}/> : 'Supprimer'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
