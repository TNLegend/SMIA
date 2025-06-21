//api/client.ts

import { useAuth } from '../context/AuthContext';
import { useTeam } from '../context/TeamContext';
import { useCallback } from 'react';
/**
 * Hook centralisant tous les appels HTTP à l'API.
 * Injecte automatiquement le token et le teamId.
 */
export const useApi = () => {
  const { token } = useAuth();
  const { teamId } = useTeam();

   return useCallback((path: string, opts: RequestInit = {}) => {
    // Pas de préfixe pour les endpoints publics :
    //  - /auth          → login / signup / me
    //  - /templates     → téléchargement de gabarits
    //  - /teams         → liste/création des équipes
    const isTeamsRoot     = path === '/teams' || path === '/teams/';
    const isTeamEndpoint  = path.startsWith('/teams/');
    const isGlobalInvites = path === '/invitations'
                       || path.startsWith('/teams/invitations/');


  const isPublic =
    path.startsWith('/auth')      ||
    path.startsWith('/templates') ||
    isTeamsRoot                   ||   // liste / création d’équipes
    isTeamEndpoint                ||   // toutes les routes /teams/:id/*
    isGlobalInvites;                   // invitations globales
    const prefix   = isPublic || teamId == null ? '' : `/teams/${teamId ?? 0}`;
    const API_HOST = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const url = `${API_HOST}${prefix}${path}`;

    return fetch(url, {
      ...opts,
      headers: {
        ...(opts.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: 'include',
    });
  }, [token, teamId]);
};
