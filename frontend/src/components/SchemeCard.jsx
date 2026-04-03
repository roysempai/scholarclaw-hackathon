import { Link } from 'react-router-dom';

export default function SchemeCard({ scheme }) {
  const getMatchColor = (score) => {
    if (score >= 80) return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/50' };
    if (score >= 50) return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/50' };
    return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/50' };
  };

  const matchColor = getMatchColor(scheme.match_score);

  const formatAmount = (amount) => {
    if (!amount) return 'Variable';
    if (amount >= 100000) return `INR ${(amount / 100000).toFixed(1)}L`;
    if (amount >= 1000) return `INR ${(amount / 1000).toFixed(0)}K`;
    return `INR ${amount}`;
  };

  const formatDeadline = (deadline) => {
    if (!deadline) return 'Rolling';
    const date = new Date(deadline);
    const now = new Date();
    const daysLeft = Math.ceil((date - now) / (1000 * 60 * 60 * 24));

    if (daysLeft < 0) return 'Expired';
    if (daysLeft === 0) return 'Today';
    if (daysLeft <= 7) return `${daysLeft} days left`;
    return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  };

  return (
    <Link
      to={`/scheme/${scheme.id}`}
      className="block bg-gray-800 rounded-xl border border-gray-700 hover:border-indigo-500 transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/10 overflow-hidden group"
    >
      {/* Match Score Badge */}
      <div className={`px-4 py-2 ${matchColor.bg} border-b ${matchColor.border}`}>
        <div className="flex items-center justify-between">
          <span className={`text-sm font-semibold ${matchColor.text}`}>
            {scheme.match_score}% Match
          </span>
          <div className="flex items-center">
            {scheme.match_score >= 80 && (
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            )}
          </div>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-5">
        <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-indigo-400 transition line-clamp-2">
          {scheme.name}
        </h3>
        <p className="text-sm text-gray-400 mb-4">{scheme.provider}</p>

        {/* Eligibility Summary */}
        {scheme.eligibility_summary && (
          <p className="text-sm text-gray-300 mb-4 line-clamp-2">
            {scheme.eligibility_summary}
          </p>
        )}

        {/* Stats */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-700">
          <div>
            <p className="text-xs text-gray-500">Award</p>
            <p className="text-sm font-semibold text-white">{formatAmount(scheme.amount)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Deadline</p>
            <p className={`text-sm font-semibold ${
              formatDeadline(scheme.deadline) === 'Expired' ? 'text-red-400' :
              formatDeadline(scheme.deadline).includes('days') ? 'text-yellow-400' :
              'text-white'
            }`}>
              {formatDeadline(scheme.deadline)}
            </p>
          </div>
        </div>
      </div>

      {/* Hover Arrow */}
      <div className="px-5 pb-4 flex justify-end">
        <span className="text-indigo-400 text-sm flex items-center opacity-0 group-hover:opacity-100 transition">
          View Details
          <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </span>
      </div>
    </Link>
  );
}
