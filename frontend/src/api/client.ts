import axios from 'axios';

import { getApiBaseUrl, getApiToken } from '../store/settings';
import type { ApiError } from './types';

export const apiClient = axios.create({
  baseURL: `${getApiBaseUrl()}/api`,
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  const token = getApiToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const toApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 401 || status === 403) {
      return {
        status,
        message: 'Недостаточно прав / требуется вход',
        details: error.response?.data,
      };
    }
    return {
      status,
      message: (error.response?.data as { detail?: string })?.detail ?? error.message,
      details: error.response?.data,
    };
  }

  return {
    message: error instanceof Error ? error.message : 'Неизвестная ошибка',
  };
};
