import axios from "axios";

const api = axios.create({

  baseURL:
    process.env
      .NEXT_PUBLIC_API_URL,
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

    if (
      error.response?.status ===
      401
    ) {

      // Clear from sessionStorage (primary) and localStorage (fallback)
      sessionStorage.removeItem(
        "token"
      );
      
      localStorage.removeItem(
        "token"
      );

      if (
        window.location.pathname
        !== "/login"
      ) {

        window.location.href =
          "/login";
      }
    }

    return Promise.reject(
      error
    );
  }
);

export default api;