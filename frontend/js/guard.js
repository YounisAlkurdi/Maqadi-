import { getToken } from "./api.js";

export function requireAuth() {
  const token = getToken();
  if (!token) {
    window.location.replace("index.html");
    return false;
  }
  return true;
}
