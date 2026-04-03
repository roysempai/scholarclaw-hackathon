import { useState, useEffect } from 'react';
import { auditAPI } from '../api/client';
import Navbar from '../components/Navbar';
import HashChainTable from '../components/HashChainTable';

export default function AuditLog() {
  const [activeTab, setActiveTab] = useState('activity');
  const [auditEntries, setAuditEntries] = useState([]);
  const [attacks, setAttacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [attackStats, setAttackStats] = useState({
    total24h: 0,
    byInjection: 0,
    byRateAbuse: 0,
    byJwtForge: 0,
  });

  useEffect(() => {
    fetchAuditData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAuditData = async () => {
    setLoading(true);
    try {
      const auditRes = await auditAPI.getChain({ limit: 50 });
      setAuditEntries(auditRes.data.entries || []);

      // Try to fetch attacks (admin only)
      try {
        const attacksRes = await auditAPI.getAttacks();
        setAttacks(attacksRes.data.attacks || []);
        setIsAdmin(true);
        calculateAttackStats(attacksRes.data.attacks || []);
      } catch {
        // Not admin, hide security tab
        setIsAdmin(false);
      }
    } catch (err) {
      setError('Failed to load audit data');
    } finally {
      setLoading(false);
    }
  };

  const calculateAttackStats = (attackList) => {
    const now = new Date();
    const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const recent = attackList.filter((a) => new Date(a.timestamp) >= last24h);

    setAttackStats({
      total24h: recent.length,
      byInjection: recent.filter((a) => a.attack_type?.toLowerCase().includes('injection')).length,
      byRateAbuse: recent.filter((a) => a.attack_type?.toLowerCase().includes('rate')).length,
      byJwtForge: recent.filter((a) => a.attack_type?.toLowerCase().includes('jwt')).length,
    });
  };

  const getAttackTypeBadge = (type) => {
    const typeLC = type?.toLowerCase() || '';
    if (typeLC.includes('injection')) return 'bg-red-500/20 text-red-400 border-red-500/50';
    if (typeLC.includes('rate')) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
    if (typeLC.includes('jwt')) return 'bg-purple-500/20 text-purple-400 border-purple-500/50';
    return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navbar />
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-2">Audit Log</h1>
        <p className="text-gray-400 mb-8">Track all system activities and security events</p>

        {error && (
          <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-gray-700 mb-6">
          <button
            onClick={() => setActiveTab('activity')}
            className={`px-6 py-3 font-medium transition ${
              activeTab === 'activity'
                ? 'text-indigo-400 border-b-2 border-indigo-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            Activity
          </button>
          {isAdmin && (
            <button
              onClick={() => setActiveTab('security')}
              className={`px-6 py-3 font-medium transition ${
                activeTab === 'security'
                  ? 'text-indigo-400 border-b-2 border-indigo-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Security Events
            </button>
          )}
        </div>

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <HashChainTable entries={auditEntries} />
        )}

        {/* Security Events Tab (Admin Only) */}
        {activeTab === 'security' && isAdmin && (
          <>
            {/* Attack Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gradient-to-r from-red-600/20 to-red-700/20 rounded-xl p-4 border border-red-500/30">
                <p className="text-red-300 text-sm">24h Attacks</p>
                <p className="text-2xl font-bold text-white">{attackStats.total24h}</p>
              </div>
              <div className="bg-gradient-to-r from-orange-600/20 to-orange-700/20 rounded-xl p-4 border border-orange-500/30">
                <p className="text-orange-300 text-sm">Injection Attempts</p>
                <p className="text-2xl font-bold text-white">{attackStats.byInjection}</p>
              </div>
              <div className="bg-gradient-to-r from-yellow-600/20 to-yellow-700/20 rounded-xl p-4 border border-yellow-500/30">
                <p className="text-yellow-300 text-sm">Rate Abuse</p>
                <p className="text-2xl font-bold text-white">{attackStats.byRateAbuse}</p>
              </div>
              <div className="bg-gradient-to-r from-purple-600/20 to-purple-700/20 rounded-xl p-4 border border-purple-500/30">
                <p className="text-purple-300 text-sm">JWT Forge</p>
                <p className="text-2xl font-bold text-white">{attackStats.byJwtForge}</p>
              </div>
            </div>

            {/* Attacks Table */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Timestamp</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Attack Type</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Source IP</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Payload Preview</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {attacks.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                          No security events recorded
                        </td>
                      </tr>
                    ) : (
                      attacks.map((attack) => (
                        <tr key={attack.id} className="hover:bg-gray-700/30 transition">
                          <td className="px-4 py-3 text-sm text-gray-300">
                            {new Date(attack.timestamp).toLocaleString()}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded-full text-xs border ${getAttackTypeBadge(attack.attack_type)}`}>
                              {attack.attack_type}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-300 font-mono">
                            {attack.source_ip}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-400 max-w-xs truncate">
                            {attack.payload_preview}
                          </td>
                          <td className="px-4 py-3">
                            {attack.blocked ? (
                              <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-400 border border-green-500/50">
                                Blocked
                              </span>
                            ) : (
                              <span className="px-2 py-1 rounded-full text-xs bg-red-500/20 text-red-400 border border-red-500/50">
                                Allowed
                              </span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
