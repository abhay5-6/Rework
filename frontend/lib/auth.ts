export function isAuthenticated() {

  if (
    typeof window ===
    "undefined"
  ) {
    return false;
  }

  const token =
    sessionStorage.getItem(
      "token"
    ) ||
    localStorage.getItem(
      "token"
    );

  return !!token;
}