/**
 * Application layout component.
 *
 * Provides the main layout structure with navigation header and logout button.
 * Per FR-AUTH-006.
 */

import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/lib/auth-context'

interface AppLayoutProps {
  children: React.ReactNode
}

/**
 * Main application layout with header navigation.
 */
export function AppLayout({ children }: AppLayoutProps) {
  const { user, logout, isLoading } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-layout">
      <header className="app-header">
        <nav className="nav-container">
          <div className="nav-brand">
            <Link to="/">MyBudget</Link>
          </div>

          <div className="nav-links">
            <Link to="/budget">Budget</Link>
            <Link to="/accounts">Accounts</Link>
            <Link to="/transactions">Transactions</Link>
          </div>

          <div className="nav-user">
            {user && (
              <>
                <span className="user-email">{user.email}</span>
                <button
                  onClick={handleLogout}
                  disabled={isLoading}
                  className="logout-button"
                  aria-label="Log out"
                >
                  {isLoading ? 'Logging out...' : 'Log Out'}
                </button>
              </>
            )}
          </div>
        </nav>
      </header>

      <main className="app-main">{children}</main>

      <style>{`
        .app-layout {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        .app-header {
          background-color: #0066cc;
          color: white;
          padding: 0 1rem;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .nav-container {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          align-items: center;
          justify-content: space-between;
          height: 60px;
        }

        .nav-brand a {
          color: white;
          text-decoration: none;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .nav-brand a:hover {
          opacity: 0.9;
        }

        .nav-links {
          display: flex;
          gap: 1.5rem;
        }

        .nav-links a {
          color: white;
          text-decoration: none;
          font-size: 0.9rem;
          opacity: 0.9;
          transition: opacity 0.2s;
        }

        .nav-links a:hover {
          opacity: 1;
        }

        .nav-user {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .user-email {
          font-size: 0.875rem;
          opacity: 0.9;
        }

        .logout-button {
          background-color: transparent;
          border: 1px solid rgba(255, 255, 255, 0.5);
          color: white;
          padding: 0.4rem 0.75rem;
          border-radius: 4px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: background-color 0.2s, border-color 0.2s;
        }

        .logout-button:hover:not(:disabled) {
          background-color: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.8);
        }

        .logout-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .app-main {
          flex: 1;
          padding: 1.5rem;
          background-color: #f5f5f5;
        }

        @media (max-width: 768px) {
          .nav-container {
            flex-wrap: wrap;
            height: auto;
            padding: 0.75rem 0;
          }

          .nav-links {
            order: 3;
            width: 100%;
            justify-content: center;
            padding-top: 0.75rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 0.75rem;
          }

          .user-email {
            display: none;
          }
        }
      `}</style>
    </div>
  )
}

export default AppLayout
