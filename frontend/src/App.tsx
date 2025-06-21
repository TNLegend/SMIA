import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { theme } from './theme'

import { AuthProvider, useAuth } from './context/AuthContext'
import PrivateRoute from './components/PrivateRoute'

import LandingPage from './pages/LandingPage'
import Login       from './pages/Login'
import Signup      from './pages/Signup'
import NotFound    from './pages/NotFound'

import Layout        from './components/layout/Layout'
import Dashboard     from './pages/Dashboard'
import Projects      from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import NewProject    from './pages/NewProject'
import AIPolicy      from './pages/AIPolicy'


import DocumentsList   from './pages/DocumentsList'
import DocumentForm    from './pages/DocumentForm'
import DocumentHistory from './pages/DocumentHistory'
import DocumentView    from './pages/DocumentView'
import EditProject   from './pages/EditProject'
import Settings   from './pages/Settings'
import { TeamProvider } from './context/TeamContext'
import TeamsPage     from './pages/Teams'
import TeamDetailPage from './pages/TeamDetailPage'
function PublicRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children
}

function App() {
  const [darkMode, setDarkMode] = useState(true)
  const toggleDarkMode = () => setDarkMode(!darkMode)

  return (
    <ThemeProvider theme={theme(darkMode)}>
      <CssBaseline />
      <BrowserRouter>
        <AuthProvider>
          <TeamProvider>
          <Routes>
            {/* Public */}
            <Route
              path="/"
              element={
                <PublicRoute>
                  <LandingPage darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
                </PublicRoute>
              }
            />
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
                </PublicRoute>
              }
            />
            <Route
              path="/signup"
              element={
                <PublicRoute>
                  <Signup darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
                </PublicRoute>
              }
            />

            {/* Protected */}
            <Route element={<PrivateRoute />}>
              <Route
                path="/dashboard"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <Dashboard />
                  </Layout>
                }
              />
              <Route
                path="/projects"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <Projects />
                  </Layout>
                }
              />
              <Route
                path="/teams"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <TeamsPage />
                  </Layout>
                }
              />
              <Route path="/teams/:teamId" element={
                <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <TeamDetailPage />
                </Layout>
                } />
              <Route
                path="/projects/new"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <NewProject />
                  </Layout>
                }
              />
              <Route path="/projects/:id/edit" element={
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}> <EditProject/> </Layout>
                }/>
              <Route
                path="/projects/:id"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <ProjectDetail />
                  </Layout>
                }
              />


              <Route
                path="/policy"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <AIPolicy />
                  </Layout>
                }
              />
              
      
            
              {/* Documents */}
              <Route
                path="/documents"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <DocumentsList />
                  </Layout>
                }
              />
              <Route
                path="/documents/new"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <DocumentForm />
                  </Layout>
                }
              />
              <Route
                path="/documents/:id/edit"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <DocumentForm />
                  </Layout>
                }
              />
              <Route
                path="/documents/:id/history"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <DocumentHistory />
                  </Layout>
                }
              />
              <Route
                path="/documents/:id"
                element={
                  <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                    <DocumentView />
                  </Layout>
                }
              />
              <Route
               path="/settings"
              element={
                 <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                   <Settings />
                 </Layout>
               }
             />
            </Route>

            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
          </TeamProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
