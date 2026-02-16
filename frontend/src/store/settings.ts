const TOKEN_KEY = 'incourses_api_token';

export const getApiToken = (): string => localStorage.getItem(TOKEN_KEY) ?? '';
export const setApiToken = (token: string) => localStorage.setItem(TOKEN_KEY, token);
export const clearApiToken = () => localStorage.removeItem(TOKEN_KEY);
export const getApiBaseUrl = () => import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
