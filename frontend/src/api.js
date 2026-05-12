import axios from 'axios';

// Dynamically pick backend host based on how the app is accessed
const BACKEND_HOST = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'localhost'
  : window.location.hostname;

export const API_BASE_URL = `http://${BACKEND_HOST}:5001`;

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  withCredentials: true,
});

export default api;
