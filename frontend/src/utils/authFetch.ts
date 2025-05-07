import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

export function useAuthFetch() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()

  return async (input: RequestInfo, init: RequestInit = {}) => {
    const headers = new Headers(init.headers || {})
    if (token) headers.set('Authorization', `Bearer ${token}`)

    const res = await fetch(input, { ...init, headers, credentials: 'include' })
    if (res.status === 401) {
      // token invalide ou expiré côté API
      logout()
      return Promise.reject(new Error('Unauthorized'))
    }
    return res
  }
}
