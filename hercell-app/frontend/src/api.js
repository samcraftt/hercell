import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL,
  withCredentials: true
});

export const auth = {
  checkAuth: async () => {
    const response = await api.get('/auth/check-auth');
    return response.data.user;
  },
  login: async (data) => await api.post('/auth/login', data),
  logout: async () => await api.post('/auth/logout'),
  resetPassword: async (password) => await api.post('/auth/reset-password', { password }),
  sendResetPasswordEmail: async (email) => await api.post('/auth/send-reset-password-email', { email }),
  signup: async (data) => await api.post('/auth/signup', data),
  verifyEmail: async (data) => await api.post('/auth/verify-email', data)
};

export const her2 = {
  analyzeSlide: async (data) => {
    const response = await api.post('/her2/analyze', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data.analysis;
  },
  explainFinding: async (data) => {
    const response = await api.post('/her2/explain', data);
    return response.data.answer;
  }
};
