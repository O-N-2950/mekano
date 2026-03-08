const API_URL = import.meta.env.VITE_API_URL || "";

// Debounce utility
export function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// Frontend validators
export const validators = {
  email: (v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v),
  plaquesCH: (v) => !v || /^[A-Z]{2}\s?\d{1,6}$/.test(v.toUpperCase()),
  kmPositif: (v) => !v || (Number.isInteger(Number(v)) && Number(v) >= 0),
  maxLength: (v, max) => !v || String(v).length <= max,
};

async function request(path, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch (err) {
    throw { status: 0, error: "Erreur réseau, vérifiez votre connexion" };
  }

  // Handle empty responses
  const text = await res.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { error: "Réponse invalide du serveur" };
  }

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/login";
    throw new Error("Session expirée");
  }

  if (res.status === 429) {
    throw { status: 429, error: "Trop de requêtes, veuillez patienter" };
  }

  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: "DELETE" }),
};
