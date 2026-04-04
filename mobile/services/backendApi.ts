import type {
  BackendAuthResponse,
  BackendBooking,
  BackendPage,
  BackendProfile,
  BackendProfilePayload,
  BackendRecommendationPayload,
  BackendRecommendationResponse,
  BackendString,
} from '../types/backend';

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.trim() ||
  'http://127.0.0.1:3001/api/v1';

export class BackendApiError extends Error {
  constructor(
    message: string,
    readonly statusCode?: number,
  ) {
    super(message);
  }
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT';
  body?: unknown;
  token?: string | null;
};

async function requestJson<T>(
  path: string,
  { method = 'GET', body, token }: RequestOptions = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      Accept: 'application/json',
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

  const json = (await response.json().catch(() => ({}))) as
    | Record<string, unknown>
    | undefined;

  if (!response.ok) {
    const error = json?.error as
      | { message?: string; details?: unknown }
      | undefined;
    throw new BackendApiError(
      error?.message ||
        (typeof json?.detail === 'string' ? json.detail : undefined) ||
        'Request failed',
      response.status,
    );
  }

  return json as T;
}

export const backendApi = {
  baseUrl: API_BASE_URL,
  registerPlayer(payload: {
    username: string;
    phone_number: string;
    password: string;
  }) {
    return requestJson<BackendAuthResponse>('/auth/register', {
      method: 'POST',
      body: payload,
    });
  },
  loginPlayer(payload: { phone_number: string; password: string }) {
    return requestJson<BackendAuthResponse>('/auth/login', {
      method: 'POST',
      body: payload,
    });
  },
  fetchCurrentUser(token: string) {
    return requestJson<BackendAuthResponse['user']>('/auth/me', { token });
  },
  fetchProfile(token: string) {
    return requestJson<BackendProfile>('/profile', { token });
  },
  saveProfile(token: string, payload: BackendProfilePayload) {
    return requestJson<BackendProfile>('/profile', {
      method: 'PUT',
      body: payload,
      token,
    });
  },
  listStrings(token: string) {
    return requestJson<BackendPage<BackendString>>('/strings', { token });
  },
  listBookings(token: string) {
    return requestJson<BackendPage<BackendBooking>>('/bookings', { token });
  },
  createBooking(
    token: string,
    payload: {
      string_id: string;
      racket_brand?: string;
      racket_model?: string;
      requested_tension?: number;
      drop_off_datetime?: string;
      notes?: string;
    },
  ) {
    return requestJson<BackendBooking>('/bookings', {
      method: 'POST',
      body: payload,
      token,
    });
  },
  previewRecommendations(token: string, payload: BackendRecommendationPayload) {
    return requestJson<BackendRecommendationResponse>('/recommendations/preview', {
      method: 'POST',
      body: payload,
      token,
    });
  },
  profileRecommendations(token: string, top_n = 3) {
    return requestJson<BackendRecommendationResponse>('/recommendations/profile', {
      method: 'POST',
      body: { top_n },
      token,
    });
  },
};
