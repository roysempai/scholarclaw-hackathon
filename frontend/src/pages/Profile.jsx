import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { profileAPI } from '../api/client';
import Navbar from '../components/Navbar';

const STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
  'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
  'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
  'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Delhi', 'Jammu and Kashmir', 'Ladakh'
];

const CATEGORIES = ['General', 'OBC', 'SC', 'ST', 'EWS', 'Minority'];
const EDUCATION_LEVELS = ['10th', '12th', 'Diploma', 'Undergraduate', 'Postgraduate', 'PhD'];
const GENDERS = ['Male', 'Female', 'Other'];

export default function Profile() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({
    full_name: '',
    date_of_birth: '',
    gender: '',
    category: '',
    annual_income: '',
    state: '',
    district: '',
    education_level: '',
    institution: '',
    course: '',
    percentage: '',
    disability_status: false,
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await profileAPI.get();
      const profile = response.data;
      setFormData({
        full_name: profile.full_name || '',
        date_of_birth: profile.date_of_birth || '',
        gender: profile.gender || '',
        category: profile.category || '',
        annual_income: profile.annual_income || '',
        state: profile.state || '',
        district: profile.district || '',
        education_level: profile.education_level || '',
        institution: profile.institution || '',
        course: profile.course || '',
        percentage: profile.percentage || '',
        disability_status: profile.disability_status || false,
      });
    } catch (err) {
      if (err.response?.status !== 404) {
        setError('Failed to load profile');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      const dataToSubmit = {
        ...formData,
        annual_income: formData.annual_income ? Number(formData.annual_income) : null,
        percentage: formData.percentage ? Number(formData.percentage) : null,
      };
      await profileAPI.update(dataToSubmit);
      setSuccess('Profile updated successfully!');
      setTimeout(() => navigate('/dashboard'), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-gray-800 rounded-2xl shadow-xl p-8 border border-gray-700">
          <h1 className="text-2xl font-bold text-white mb-2">Complete Your Profile</h1>
          <p className="text-gray-400 mb-8">Fill in your details to get personalized scholarship recommendations</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
            {success && (
              <div className="bg-green-500/20 border border-green-500/50 text-green-200 px-4 py-3 rounded-lg">
                {success}
              </div>
            )}

            {/* Personal Information */}
            <div className="border-b border-gray-700 pb-6">
              <h2 className="text-lg font-semibold text-white mb-4">Personal Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Date of Birth</label>
                  <input
                    type="date"
                    name="date_of_birth"
                    value={formData.date_of_birth}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Gender</label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Select Gender</option>
                    {GENDERS.map((g) => (
                      <option key={g} value={g}>{g}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Select Category</option>
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="border-b border-gray-700 pb-6">
              <h2 className="text-lg font-semibold text-white mb-4">Location</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">State</label>
                  <select
                    name="state"
                    value={formData.state}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Select State</option>
                    {STATES.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">District</label>
                  <input
                    type="text"
                    name="district"
                    value={formData.district}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Enter your district"
                  />
                </div>
              </div>
            </div>

            {/* Education */}
            <div className="border-b border-gray-700 pb-6">
              <h2 className="text-lg font-semibold text-white mb-4">Education</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Education Level</label>
                  <select
                    name="education_level"
                    value={formData.education_level}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Select Level</option>
                    {EDUCATION_LEVELS.map((e) => (
                      <option key={e} value={e}>{e}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Institution</label>
                  <input
                    type="text"
                    name="institution"
                    value={formData.institution}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="School/College name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Course</label>
                  <input
                    type="text"
                    name="course"
                    value={formData.course}
                    onChange={handleChange}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="B.Tech, MBA, etc."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Percentage/CGPA</label>
                  <input
                    type="number"
                    name="percentage"
                    value={formData.percentage}
                    onChange={handleChange}
                    min="0"
                    max="100"
                    step="0.01"
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="85.5"
                  />
                </div>
              </div>
            </div>

            {/* Financial & Additional */}
            <div className="pb-6">
              <h2 className="text-lg font-semibold text-white mb-4">Financial & Additional</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Annual Family Income (INR)</label>
                  <input
                    type="number"
                    name="annual_income"
                    value={formData.annual_income}
                    onChange={handleChange}
                    min="0"
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="500000"
                  />
                </div>
                <div className="flex items-center pt-8">
                  <input
                    type="checkbox"
                    name="disability_status"
                    checked={formData.disability_status}
                    onChange={handleChange}
                    className="h-5 w-5 text-indigo-600 bg-gray-700 border-gray-600 rounded focus:ring-indigo-500"
                  />
                  <label className="ml-3 text-sm text-gray-300">
                    Person with Disability (PwD)
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="px-6 py-3 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition"
              >
                Skip for now
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-indigo-800 disabled:cursor-not-allowed transition flex items-center"
              >
                {saving ? (
                  <>
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Saving...
                  </>
                ) : (
                  'Save Profile'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
