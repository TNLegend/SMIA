// src/context/AuthContext.tsx
import React,
{ createContext, useContext, useState, useEffect, ReactNode }
  from 'react'
import { useNavigate } from 'react-router-dom'
import { jwtDecode } from 'jwt-decode'

interface JwtPayload { exp?: number; sub?: string }
interface AuthContextType {
  token: string | null
  login: (jwt: string) => void
  logout: () => void
  isAuthenticated: boolean
}
const AuthContext = createContext<AuthContextType>({
  token: null, login: () => {}, logout: () => {}, isAuthenticated: false,
})

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const navigate = useNavigate()
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('smia_token')
  )

  const login = (jwt: string) => {
    localStorage.setItem('smia_token', jwt)
    setToken(jwt)
  }
  const logout = () => {
    localStorage.removeItem('smia_token')
    setToken(null)
    navigate('/login', { replace: true })
  }

  useEffect(() => {
    if (!token) {
      // no token → already logged out
      return
    }

    // 1) check expiry client-side
    try {
      const { exp } = jwtDecode<JwtPayload>(token)
      if (!exp || exp * 1000 < Date.now()) {
        // expired
        return logout()
      }
    } catch {
      // malformed
      return logout()
    }

    // 2) verify signature / still valid with server
    fetch('http://127.0.0.1:8000/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (res.status === 401) {
          // signature invalid or revoked
          logout()
        }
      })
      .catch(() => {
        // network or other issue → assume invalid
        logout()
      })
  }, [token])

  return (
    <AuthContext.Provider
      value={{
        token,
        login,
        logout,
        isAuthenticated: Boolean(token),
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
