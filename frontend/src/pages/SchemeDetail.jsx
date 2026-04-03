import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { schemesAPI } from '../api/client';
import Navbar from '../components/Navbar';
import DraftViewer from '../components/DraftViewer';

export default function SchemeDetail() {
  const { id } = useParams();
  const [scheme, setScheme] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSchemeDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchSchemeDetails = async () => {
    try {
      const [schemeRes, eligibilityRes] = await Promise.all([
        schemesAPI.get(id),
        schemesAPI.checkEligibility(id),
      ]);
      setScheme(schemeRes.data);
      setEligibility(eligibilityRes.data);
    } catch (err) {
      setError('Failed to load scheme details');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDraft = async () => {
    setGenerating(true);
    setError('');
    try {
      const response = await schemesAPI.draftApplication(id);
      setDraft(response.data);
    } catch (err) {
      setError('Failed to generate application draft');
    } finally {
      setGenerating(false);
    }
  };

  const getMatchColor = (score) => {
    if (score >= 80) return 'text-green-400 bg-green-400/20';
    if (score >= 50) return 'text-yellow-400 bg-yellow-400/20';
    return 'text-red-400 bg-red-400/20';
  };

  const getStatusBadge = (status) => {
    const styles = {
      eligible: 'bg-green-500/20 text-green-400 border-green-500/50',
      ineligible: 'bg-red-500/20 text-red-400 border-red-500/50',
      partial: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    };
    return styles[status] || styles.partial;
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

  if (!scheme) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="text-center py-12">
            <p className="text-gray-400">Scheme not found</p>
            <Link to="/dashboard" className="text-indigo-400 hover:text-indigo-300 mt-4 inline-block">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Back Link */}
        <Link to="/dashboard" className="inline-flex items-center text-indigo-400 hover:text-indigo-300 mb-6">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </Link>

        {error && (
          <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Scheme Header */}
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700 mb-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-white mb-2">{scheme.name}</h1>
              <p className="text-gray-400 mb-4">{scheme.provider}</p>
              <p className="text-gray-300">{scheme.description}</p>
            </div>
            <div className="mt-4 md:mt-0 md:ml-6 flex flex-col items-end">
              <div className={`px-4 py-2 rounded-full font-bold ${getMatchColor(scheme.match_score)}`}>
                {scheme.match_score}% Match
              </div>
              {eligibility && (
                <span className={`mt-2 px-3 py-1 rounded-full text-sm border ${getStatusBadge(scheme.eligibility_status)}`}>
                  {scheme.eligibility_status?.charAt(0).toUpperCase() + scheme.eligibility_status?.slice(1)}
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-700">
            <div>
              <p className="text-gray-500 text-sm">Award Amount</p>
              <p className="text-xl font-semibold text-white">
                {scheme.amount ? `INR ${scheme.amount.toLocaleString()}` : 'Variable'}
              </p>
            </div>
            <div>
              <p className="text-gray-500 text-sm">Deadline</p>
              <p className="text-xl font-semibold text-white">
                {scheme.deadline ? new Date(scheme.deadline).toLocaleDateString() : 'Rolling'}
              </p>
            </div>
            <div className="col-span-2">
              <p className="text-gray-500 text-sm">Application URL</p>
              {scheme.application_url ? (
                <a
                  href={scheme.application_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-400 hover:text-indigo-300 truncate block"
                >
                  {scheme.application_url}
                </a>
              ) : (
                <p className="text-gray-400">Not available</p>
              )}
            </div>
          </div>
        </div>

        {/* Eligibility Details */}
        {eligibility && (
          <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700 mb-6">
            <h2 className="text-xl font-semibold text-white mb-4">Eligibility Analysis</h2>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Met Criteria */}
              <div>
                <h3 className="text-green-400 font-medium mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Criteria Met ({eligibility.met_criteria?.length || 0})
                </h3>
                <ul className="space-y-2">
                  {eligibility.met_criteria?.map((criterion, i) => (
                    <li key={i} className="text-gray-300 flex items-start">
                      <span className="text-green-400 mr-2">+</span>
                      {criterion}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Unmet Criteria */}
              <div>
                <h3 className="text-red-400 font-medium mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  Criteria Not Met ({eligibility.unmet_criteria?.length || 0})
                </h3>
                <ul className="space-y-2">
                  {eligibility.unmet_criteria?.map((criterion, i) => (
                    <li key={i} className="text-gray-300 flex items-start">
                      <span className="text-red-400 mr-2">-</span>
                      {criterion}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recommendations */}
            {eligibility.recommendations?.length > 0 && (
              <div className="mt-6 pt-6 border-t border-gray-700">
                <h3 className="text-yellow-400 font-medium mb-3">Recommendations</h3>
                <ul className="space-y-2">
                  {eligibility.recommendations.map((rec, i) => (
                    <li key={i} className="text-gray-300 flex items-start">
                      <span className="text-yellow-400 mr-2">*</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Required Documents */}
        {scheme.required_documents?.length > 0 && (
          <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700 mb-6">
            <h2 className="text-xl font-semibold text-white mb-4">Required Documents</h2>
            <ul className="grid md:grid-cols-2 gap-3">
              {scheme.required_documents.map((doc, i) => (
                <li key={i} className="flex items-center text-gray-300">
                  <svg className="w-5 h-5 mr-3 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {doc}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Generate Draft Button */}
        {!draft && (
          <div className="text-center">
            <button
              onClick={handleGenerateDraft}
              disabled={generating}
              className="px-8 py-4 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:bg-indigo-800 transition text-lg font-medium flex items-center mx-auto"
            >
              {generating ? (
                <>
                  <svg className="animate-spin h-6 w-6 mr-3" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Generating Draft...
                </>
              ) : (
                <>
                  <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Generate Application Draft
                </>
              )}
            </button>
            <p className="text-gray-500 mt-3 text-sm">AI will generate a personalized application draft based on your profile</p>
          </div>
        )}

        {/* Draft Viewer */}
        {draft && (
          <DraftViewer
            draft={draft.draft}
            auditHash={draft.audit_hash}
            requiredDocuments={scheme.required_documents}
          />
        )}
      </div>
    </div>
  );
}
