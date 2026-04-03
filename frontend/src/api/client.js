import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach JWT from localStorage
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[API] Request with token:', config.url);
    } else {
      console.log('[API] Request without token:', config.url);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: 401 -> redirect to /login, clear token
// Note: 403 means authenticated but not authorized - don't log out
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only log out on 401 (invalid/expired token), not 403 (insufficient permissions)
    if (error.response?.status === 401) {
      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, password) => client.post('/auth/login', { email, password }),
  register: (email, password, full_name) => client.post('/auth/register', { email, password, full_name }),
  logout: () => client.post('/auth/logout'),
  refresh: (refresh_token) => client.post('/auth/refresh', { refresh_token }),
};

// Profile API
export const profileAPI = {
  get: () => client.get('/profile'),
  update: (data) => client.put('/profile', data),
};

// Schemes API
export const schemesAPI = {
  list: (params = {}) => client.get('/schemes', { params }),
  get: (schemeId) => client.get(`/schemes/${schemeId}`),
  checkEligibility: (schemeId) => client.post(`/schemes/${schemeId}/check-eligibility`),
  draftApplication: (schemeId) => client.post(`/schemes/${schemeId}/draft-application`),
};

// Audit API
export const auditAPI = {
  getChain: (params = {}) => client.get('/audit/logs', { params }),
  verify: () => client.get('/audit/verify'),
  getAttacks: () => client.get('/audit/attacks'),
};

export default client;
