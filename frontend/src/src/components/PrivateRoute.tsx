import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function PrivateRoute() {
  const { isAuthenticated } = useAuth()

  // if not logged in (or token just got invalidated), redirect to login
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}
