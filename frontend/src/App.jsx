import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import Dashboard from './pages/Dashboard';
import SchemeDetail from './pages/SchemeDetail';
import AuditLog from './pages/AuditLog';

// Protected Route Component
function ProtectedRoute({ children }) {
  const location = useLocation();
  const token = localStorage.getItem('access_token');

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

// Public Route Component (redirect to dashboard if already logged in)
function PublicRoute({ children }) {
  const token = localStorage.getItem('access_token');

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* Protected Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/scheme/:id"
          element={
            <ProtectedRoute>
              <SchemeDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit"
          element={
            <ProtectedRoute>
              <AuditLog />
            </ProtectedRoute>
          }
        />

        {/* Default Route - Redirect to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* 404 - Redirect to dashboard if logged in, else to login */}
        <Route
          path="*"
          element={
            localStorage.getItem('access_token') ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
