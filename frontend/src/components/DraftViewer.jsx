import { useState } from 'react';

export default function DraftViewer({ draft, auditHash, requiredDocuments }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const fullText = draft?.personal_statement || '';
    await navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!draft) return null;

  return (
    <div className="bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-6 h-6 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h2 className="text-xl font-semibold text-white">Generated Application Draft</h2>
          </div>
          <button
            onClick={handleCopy}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition flex items-center text-sm"
          >
            {copied ? (
              <>
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Copied!
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                </svg>
                Copy
              </>
            )}
          </button>
        </div>
      </div>

      {/* Personal Statement */}
      <div className="p-6">
        <h3 className="text-lg font-medium text-white mb-3">Personal Statement</h3>
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
          <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
            {draft.personal_statement}
          </p>
        </div>
      </div>

      {/* Q&A Answers */}
      {draft.answers && draft.answers.length > 0 && (
        <div className="px-6 pb-6">
          <h3 className="text-lg font-medium text-white mb-3">Application Answers</h3>
          <div className="space-y-4">
            {draft.answers.map((item, index) => (
              <div key={index} className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <p className="text-indigo-400 font-medium mb-2">{item.question}</p>
                <p className="text-gray-300 whitespace-pre-wrap">{item.answer}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Checklist */}
      {requiredDocuments && requiredDocuments.length > 0 && (
        <div className="px-6 pb-6">
          <h3 className="text-lg font-medium text-white mb-3">Document Checklist</h3>
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <ul className="space-y-2">
              {requiredDocuments.map((doc, index) => (
                <li key={index} className="flex items-center text-gray-300">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-indigo-600 bg-gray-700 border-gray-600 rounded focus:ring-indigo-500 mr-3"
                  />
                  {doc}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Audit Hash */}
      {auditHash && (
        <div className="px-6 pb-6">
          <div className="flex items-center justify-between bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm text-gray-400">Audit Hash:</span>
            </div>
            <code className="text-sm text-indigo-400 font-mono">{auditHash}</code>
          </div>
        </div>
      )}

      {/* Notes */}
      <div className="px-6 pb-6">
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-yellow-400 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="text-sm text-yellow-200 font-medium">Important Notes</p>
              <ul className="mt-2 text-sm text-yellow-100/80 list-disc list-inside space-y-1">
                <li>Review and personalize this draft before submitting</li>
                <li>Ensure all information is accurate and up-to-date</li>
                <li>Attach all required documents listed in the checklist</li>
                <li>This draft was generated by AI and may need adjustments</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
