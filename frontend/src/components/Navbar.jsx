import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../api/client';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      navigate('/login');
    }
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center space-x-2">
            <svg className="w-8 h-8 text-indigo-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 14l9-5-9-5-9 5 9 5z" />
              <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
            </svg>
            <span className="text-xl font-bold text-white">ScholarClaw</span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            <Link
              to="/dashboard"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                isActive('/dashboard')
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/profile"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                isActive('/profile')
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              Profile
            </Link>
            <Link
              to="/audit"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                isActive('/audit')
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              Audit Log
            </Link>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Logout
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden pb-4">
          <div className="flex space-x-2">
            <Link
              to="/dashboard"
              className={`flex-1 text-center px-3 py-2 rounded-lg text-sm font-medium transition ${
                isActive('/dashboard')
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 bg-gray-700'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/profile"
              className={`flex-1 text-center px-3 py-2 rounded-lg text-sm font-medium transition ${
                isActive('/profile')
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 bg-gray-700'
              }`}
            >
              Profile
            </Link>
            <Link
              to="/audit"
              className={`flex-1 text-center px-3 py-2 rounded-lg text-sm font-medium transition ${
                isActive('/audit')
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 bg-gray-700'
              }`}
            >
              Audit
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
