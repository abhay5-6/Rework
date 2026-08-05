import axios from "axios";

const api = axios.create({

  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  // Only access storage on client side
  if (typeof window !== "undefined") {
    const token = sessionStorage.getItem("token") || localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      sessionStorage.removeItem("token");
      localStorage.removeItem("token");
      window.dispatchEvent(new Event("auth-unauthorized"));
    }
    return Promise.reject(error);
  }
);

export default api;