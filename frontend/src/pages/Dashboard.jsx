import { useState, useEffect } from 'react';
import { schemesAPI } from '../api/client';
import Navbar from '../components/Navbar';
import SchemeCard from '../components/SchemeCard';

export default function Dashboard() {
  const [schemes, setSchemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ category: '', state: '' });
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });

  useEffect(() => {
    fetchSchemes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const fetchSchemes = async () => {
    setLoading(true);
    try {
      const response = await schemesAPI.list({
        page: pagination.page,
        limit: 20,
        ...(filters.category && { category: filters.category }),
        ...(filters.state && { state: filters.state }),
      });
      setSchemes(response.data.schemes || []);
      setPagination({
        page: response.data.page,
        pages: response.data.pages,
        total: response.data.total,
      });
    } catch (err) {
      setError('Failed to load schemes');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckEligibility = async () => {
    setChecking(true);
    setError('');
    try {
      // Check eligibility for all schemes - this triggers the orchestrator
      const response = await schemesAPI.list({ page: 1, limit: 50 });
      setSchemes(response.data.schemes || []);
      setPagination({
        page: response.data.page,
        pages: response.data.pages,
        total: response.data.total,
      });
    } catch (err) {
      setError('Failed to check eligibility. Please complete your profile first.');
    } finally {
      setChecking(false);
    }
  };

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Scholarship Dashboard</h1>
            <p className="text-gray-400 mt-1">Discover scholarships matched to your profile</p>
          </div>
          <button
            onClick={handleCheckEligibility}
            disabled={checking}
            className="mt-4 md:mt-0 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-indigo-800 transition flex items-center justify-center"
          >
            {checking ? (
              <>
                <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Checking...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Check Eligibility
              </>
            )}
          </button>
        </div>

        {/* Filters */}
        <div className="bg-gray-800 rounded-xl p-4 mb-6 border border-gray-700">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-400 mb-1">Category</label>
              <select
                name="category"
                value={filters.category}
                onChange={handleFilterChange}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Categories</option>
                <option value="General">General</option>
                <option value="OBC">OBC</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
                <option value="EWS">EWS</option>
                <option value="Minority">Minority</option>
              </select>
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-400 mb-1">State</label>
              <select
                name="state"
                value={filters.state}
                onChange={handleFilterChange}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All States</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Karnataka">Karnataka</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
                <option value="Delhi">Delhi</option>
                <option value="Gujarat">Gujarat</option>
              </select>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 rounded-xl p-6">
            <p className="text-indigo-200 text-sm">Total Schemes</p>
            <p className="text-3xl font-bold text-white">{pagination.total}</p>
          </div>
          <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-xl p-6">
            <p className="text-green-200 text-sm">High Match (80%+)</p>
            <p className="text-3xl font-bold text-white">
              {schemes.filter((s) => s.match_score >= 80).length}
            </p>
          </div>
          <div className="bg-gradient-to-r from-yellow-600 to-yellow-700 rounded-xl p-6">
            <p className="text-yellow-200 text-sm">Medium Match (50-80%)</p>
            <p className="text-3xl font-bold text-white">
              {schemes.filter((s) => s.match_score >= 50 && s.match_score < 80).length}
            </p>
          </div>
        </div>

        {/* Schemes Grid */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
          </div>
        ) : schemes.length === 0 ? (
          <div className="text-center py-12">
            <svg className="mx-auto h-16 w-16 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="mt-4 text-gray-400">No schemes found. Try adjusting your filters or complete your profile.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {schemes.map((scheme) => (
              <SchemeCard key={scheme.id} scheme={scheme} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination.pages > 1 && (
          <div className="flex justify-center mt-8 space-x-2">
            {Array.from({ length: pagination.pages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                onClick={() => setPagination({ ...pagination, page })}
                className={`px-4 py-2 rounded-lg transition ${
                  pagination.page === page
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {page}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
