export default function HashChainTable({ entries }) {
  const getResultBadge = (action) => {
    const actionLC = action?.toLowerCase() || '';
    if (actionLC.includes('success') || actionLC.includes('complete')) {
      return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/50', label: 'Success' };
    }
    if (actionLC.includes('fail') || actionLC.includes('error')) {
      return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/50', label: 'Failed' };
    }
    if (actionLC.includes('pending') || actionLC.includes('progress')) {
      return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/50', label: 'Pending' };
    }
    return { bg: 'bg-indigo-500/20', text: 'text-indigo-400', border: 'border-indigo-500/50', label: 'Info' };
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const truncateHash = (hash) => {
    if (!hash) return 'N/A';
    return hash.substring(0, 8);
  };

  if (!entries || entries.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-8 text-center">
        <svg className="mx-auto h-12 w-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p className="mt-4 text-gray-400">No audit entries found</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Timestamp</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Action</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Agent</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Result</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Hash</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {entries.map((entry) => {
              const badge = getResultBadge(entry.action);
              return (
                <tr key={entry.id} className="hover:bg-gray-700/30 transition">
                  <td className="px-4 py-3 text-sm text-gray-300 whitespace-nowrap">
                    {formatTimestamp(entry.timestamp)}
                  </td>
                  <td className="px-4 py-3 text-sm text-white">
                    {entry.action}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {entry.agent || 'System'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs border ${badge.bg} ${badge.text} ${badge.border}`}>
                      {badge.label}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <code className="text-sm text-indigo-400 font-mono bg-gray-900 px-2 py-1 rounded">
                      {truncateHash(entry.current_hash)}
                    </code>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Chain Validation Footer */}
      <div className="bg-gray-900 px-4 py-3 flex items-center justify-between border-t border-gray-700">
        <div className="flex items-center">
          <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span className="text-sm text-gray-300">Hash chain integrity verified</span>
        </div>
        <span className="text-sm text-gray-500">{entries.length} entries</span>
      </div>
    </div>
  );
}
