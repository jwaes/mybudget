/**
 * Main application component with routing.
 *
 * Defines the route structure with public and protected routes.
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/lib/auth-context'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { SidebarLayout } from '@/components/layout/SidebarLayout'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { LoginPage } from '@/pages/Login'
import { RegisterPage } from '@/pages/Register'
import { AccountsPage } from '@/pages/Accounts'
import { TransactionsPage } from '@/pages/Transactions'
import { BudgetPage } from '@/pages/Budget'
import { NotFound } from '@/pages/NotFound'

/**
 * Dashboard placeholder page.
 */
function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome to MyBudget! This is your dashboard.</p>
    </div>
  )
}

/**
 * Redirect authenticated users away from auth pages.
 */
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        Loading...
      </div>
    )
  }

  // If already logged in, redirect to dashboard
  if (user) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

/**
 * Main application with route definitions.
 */
export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Public routes (redirect to dashboard if authenticated) */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          }
        />

        {/* Protected routes (require authentication) */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <SidebarLayout>
                <DashboardPage />
              </SidebarLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/accounts"
          element={
            <ProtectedRoute>
              <SidebarLayout>
                <AccountsPage />
              </SidebarLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/transactions"
          element={
            <ProtectedRoute>
              <SidebarLayout>
                <TransactionsPage />
              </SidebarLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/budget"
          element={
            <ProtectedRoute>
              <SidebarLayout>
                <BudgetPage />
              </SidebarLayout>
            </ProtectedRoute>
          }
        />

        {/* 404 Not Found */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ErrorBoundary>
  )
}
