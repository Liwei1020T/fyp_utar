import type {
  BackendAdminInventoryString,
  BackendAuthResponse,
  BackendBooking,
  BackendForgotPasswordRequestResponse,
  BackendMessageResponse,
  BackendPage,
  BackendProfile,
  BackendProfilePayload,
  BackendRecommendationPayload,
  BackendRecommendationResponse,
  BackendString,
} from '../types/backend';

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.trim() ||
  'http://127.0.0.1:3001/api';

export class BackendApiError extends Error {
  constructor(
    message: string,
    readonly statusCode?: number,
  ) {
    super(message);
  }
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH';
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
  requestPasswordResetCode(payload: { phone_number: string }) {
    return requestJson<BackendForgotPasswordRequestResponse>(
      '/auth/forgot-password/request-code',
      {
        method: 'POST',
        body: payload,
      },
    );
  },
  resetPasswordWithCode(payload: {
    phone_number: string;
    verification_code: string;
    new_password: string;
  }) {
    return requestJson<BackendMessageResponse>('/auth/forgot-password/reset', {
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
  adminListBookings(
    token: string,
    params?: {
      status?: string;
      search?: string;
      limit?: number;
      offset?: number;
    },
  ) {
    const searchParams = new URLSearchParams();
    if (params?.status) {
      searchParams.set('status', params.status);
    }
    if (params?.search) {
      searchParams.set('search', params.search);
    }
    if (params?.limit != null) {
      searchParams.set('limit', String(params.limit));
    }
    if (params?.offset != null) {
      searchParams.set('offset', String(params.offset));
    }
    const suffix = searchParams.size > 0 ? `?${searchParams.toString()}` : '';
    return requestJson<BackendPage<BackendBooking>>(`/admin/bookings${suffix}`, {
      token,
    });
  },
  adminFetchBooking(token: string, bookingId: string) {
    return requestJson<BackendBooking>(`/admin/bookings/${bookingId}`, { token });
  },
  adminUpdateBookingStatus(
    token: string,
    bookingId: string,
    payload: { status: string; note?: string },
  ) {
    return requestJson<BackendBooking>(`/admin/bookings/${bookingId}/status`, {
      method: 'PATCH',
      body: payload,
      token,
    });
  },
  adminListInventoryStrings(
    token: string,
    params?: {
      availability?: 'in_stock' | 'low_stock' | 'out_of_stock';
      brand?: string;
      search?: string;
      limit?: number;
      offset?: number;
    },
  ) {
    const searchParams = new URLSearchParams();
    if (params?.availability) {
      searchParams.set('availability', params.availability);
    }
    if (params?.brand) {
      searchParams.set('brand', params.brand);
    }
    if (params?.search) {
      searchParams.set('search', params.search);
    }
    if (params?.limit != null) {
      searchParams.set('limit', String(params.limit));
    }
    if (params?.offset != null) {
      searchParams.set('offset', String(params.offset));
    }
    const suffix = searchParams.size > 0 ? `?${searchParams.toString()}` : '';
    return requestJson<{
      items: BackendAdminInventoryString[];
      total: number;
      limit: number | null;
      offset: number;
    }>(`/admin/inventory/strings${suffix}`, {
      token,
    });
  },
  adminFetchInventoryString(token: string, stringId: string) {
    return requestJson<BackendAdminInventoryString>(
      `/admin/inventory/strings/${stringId}`,
      { token },
    );
  },
  adminUpdateInventoryString(
    token: string,
    stringId: string,
    payload: {
      price_rm?: number | null;
      stock_level?: number | null;
      admin_note?: string | null;
    },
  ) {
    return requestJson<BackendAdminInventoryString>(
      `/admin/inventory/strings/${stringId}`,
      {
        method: 'PATCH',
        body: payload,
        token,
      },
    );
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
