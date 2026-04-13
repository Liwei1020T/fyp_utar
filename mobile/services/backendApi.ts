import type {
  BackendAdminInventoryString,
  BackendAnalyticsSummary,
  BackendAuthResponse,
  BackendCheckInLookupResponse,
  BackendCheckInRequest,
  BackendBooking,
  BackendForgotPasswordRequestResponse,
  BackendInventoryUpdatePayload,
  BackendMessageResponse,
  BackendOfficialPerformance,
  BackendOfficialPerformancePayload,
  BackendPage,
  BackendPopularString,
  BackendProfile,
  BackendProfilePayload,
  BackendRecommendationPayload,
  BackendRecommendationDetailResponse,
  BackendRecommendationResponse,
  BackendServiceQueue,
  BackendSlot,
  BackendStoreBusinessHours,
  BackendStoreBusinessHoursPayload,
  BackendStoreSettings,
  BackendStoreSettingsPayload,
  BackendString,
  BackendStringWritePayload,
} from '../types/backend';
import { Platform } from 'react-native';

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.trim() ||
  'http://localhost:3001/api';
const REQUEST_TIMEOUT_MS = 12000;

export class BackendApiError extends Error {
  constructor(
    message: string,
    readonly statusCode?: number,
  ) {
    super(message);
  }
}

export function isBackendAuthError(error: unknown): error is BackendApiError {
  return (
    error instanceof BackendApiError &&
    (error.statusCode === 401 || error.statusCode === 403)
  );
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  token?: string | null;
};

export type BackendUploadFile = {
  uri: string;
  name: string;
  type: string;
};

export type BackendBookingPhotoType = 'racket' | 'service_progress' | 'other';

function apiRootUrl() {
  return API_BASE_URL.replace(/\/api\/?$/, '');
}

export function resolveBackendMediaUrl(value?: string | null) {
  if (!value) {
    return undefined;
  }
  if (/^https?:\/\//i.test(value)) {
    return value;
  }
  return `${apiRootUrl()}${value.startsWith('/') ? value : `/${value}`}`;
}

async function requestJson<T>(
  path: string,
  { method = 'GET', body, token }: RequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        Accept: 'application/json',
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error && error.name === 'AbortError') {
      throw new BackendApiError(
        `The backend did not respond within ${REQUEST_TIMEOUT_MS / 1000} seconds. Confirm the API is running and EXPO_PUBLIC_API_BASE_URL is correct.`,
      );
    }

    throw new BackendApiError(
      'Unable to reach the backend. Confirm the API is running and EXPO_PUBLIC_API_BASE_URL points to it.',
    );
  }

  clearTimeout(timeoutId);

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

async function requestFormJson<T>(
  path: string,
  {
    formData,
    token,
  }: {
    formData: FormData;
    token?: string | null;
  },
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error && error.name === 'AbortError') {
      throw new BackendApiError(
        `The backend did not respond within ${REQUEST_TIMEOUT_MS / 1000} seconds. Confirm the API is running and EXPO_PUBLIC_API_BASE_URL is correct.`,
      );
    }

    throw new BackendApiError(
      'Unable to reach the backend. Confirm the API is running and EXPO_PUBLIC_API_BASE_URL points to it.',
    );
  }

  clearTimeout(timeoutId);

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

async function normalizeUploadFile(file: BackendUploadFile) {
  if (Platform.OS !== 'web') {
    return file as unknown as Blob;
  }

  const response = await fetch(file.uri);
  const blob = await response.blob();

  if (typeof File === 'undefined') {
    return blob;
  }

  return new File([blob], file.name, { type: file.type || blob.type });
}

async function buildBookingUpdateForm(input: {
  comment?: string;
  photo?: BackendUploadFile | null;
  photoType?: BackendBookingPhotoType;
}) {
  const formData = new FormData();
  if (input.comment?.trim()) {
    formData.append('comment', input.comment.trim());
  }
  if (input.photoType) {
    formData.append('photo_type', input.photoType);
  }
  if (input.photo) {
    formData.append('photo', await normalizeUploadFile(input.photo));
  }
  return formData;
}

async function buildImageUploadForm(input: {
  photo: BackendUploadFile;
}) {
  const formData = new FormData();
  formData.append('photo', await normalizeUploadFile(input.photo));
  return formData;
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
  login(payload: { phone_number: string; password: string }) {
    return requestJson<BackendAuthResponse>('/auth/login', {
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
  fetchBooking(token: string, bookingId: string) {
    return requestJson<BackendBooking>(`/bookings/${bookingId}`, { token });
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
  adminAddBookingUpdate(
    token: string,
    bookingId: string,
    input: {
      comment?: string;
      photo?: BackendUploadFile | null;
      photoType?: BackendBookingPhotoType;
    },
  ) {
    return buildBookingUpdateForm(input).then((formData) =>
      requestFormJson<BackendBooking>(`/admin/bookings/${bookingId}/updates`, {
        formData,
        token,
      }),
    );
  },
  adminUploadBookingPhoto(
    token: string,
    bookingId: string,
    input: {
      photo: BackendUploadFile;
      comment?: string;
      photoType?: BackendBookingPhotoType;
    },
  ) {
    return buildBookingUpdateForm({
      comment: input.comment,
      photo: input.photo,
      photoType: input.photoType ?? 'racket',
    }).then((formData) =>
      requestFormJson<BackendBooking>(`/admin/bookings/${bookingId}/photos`, {
        formData,
        token,
      }),
    );
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
  fetchBusinessHours(token: string) {
    return requestJson<BackendStoreBusinessHours>('/admin/business-hours', {
      token,
    });
  },
  updateBusinessHours(token: string, payload: BackendStoreBusinessHoursPayload) {
    return requestJson<BackendStoreBusinessHours>('/admin/business-hours', {
      method: 'PUT',
      body: payload,
      token,
    });
  },
  listSlots(
    token: string,
    params?: {
      date?: string;
      date_from?: string;
      days?: number;
    },
  ) {
    const searchParams = new URLSearchParams();
    if (params?.date) {
      searchParams.set('date', params.date);
    }
    if (params?.date_from) {
      searchParams.set('date_from', params.date_from);
    }
    if (params?.days != null) {
      searchParams.set('days', String(params.days));
    }
    const suffix = searchParams.size > 0 ? `?${searchParams.toString()}` : '';
    return requestJson<BackendPage<BackendSlot>>(`/slots${suffix}`, { token });
  },
  adminListSlots(
    token: string,
    params?: {
      date?: string;
      date_from?: string;
      days?: number;
    },
  ) {
    const searchParams = new URLSearchParams();
    if (params?.date) {
      searchParams.set('date', params.date);
    }
    if (params?.date_from) {
      searchParams.set('date_from', params.date_from);
    }
    if (params?.days != null) {
      searchParams.set('days', String(params.days));
    }
    const suffix = searchParams.size > 0 ? `?${searchParams.toString()}` : '';
    return requestJson<BackendPage<BackendSlot>>(`/admin/slots${suffix}`, {
      token,
    });
  },
  adminLookupCheckIn(token: string, reference: string) {
    const searchParams = new URLSearchParams({ reference });
    return requestJson<BackendCheckInLookupResponse>(
      `/admin/check-in/lookup?${searchParams.toString()}`,
      { token },
    );
  },
  adminCheckIn(token: string, payload: BackendCheckInRequest) {
    return requestJson<BackendBooking>('/admin/check-in', {
      method: 'POST',
      body: payload,
      token,
    });
  },
  adminFetchServiceQueue(token: string) {
    return requestJson<BackendServiceQueue>('/admin/service-queue', {
      token,
    });
  },
  adminFetchStoreSettings(token: string) {
    return requestJson<BackendStoreSettings>('/admin/store-settings', {
      token,
    });
  },
  adminUpdateStoreSettings(
    token: string,
    payload: BackendStoreSettingsPayload,
  ) {
    return requestJson<BackendStoreSettings>('/admin/store-settings', {
      method: 'PUT',
      body: payload,
      token,
    });
  },
  adminAnalyticsSummary(token: string) {
    return requestJson<BackendAnalyticsSummary>('/admin/analytics/summary', {
      token,
    });
  },
  adminPopularStrings(token: string, limit = 5) {
    const searchParams = new URLSearchParams({ limit: String(limit) });
    return requestJson<BackendPopularString[]>(
      `/admin/analytics/popular-strings?${searchParams.toString()}`,
      { token },
    );
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
    payload: BackendInventoryUpdatePayload,
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
  adminUploadStringImage(
    token: string,
    stringId: string,
    input: { photo: BackendUploadFile },
  ) {
    return buildImageUploadForm(input).then((formData) =>
      requestFormJson<BackendString>(`/admin/strings/${stringId}/image`, {
        formData,
        token,
      }),
    );
  },
  adminDeleteStringImage(token: string, stringId: string) {
    return requestJson<BackendString>(`/admin/strings/${stringId}/image`, {
      method: 'DELETE',
      token,
    });
  },
  adminUpdateString(
    token: string,
    stringId: string,
    payload: BackendStringWritePayload,
  ) {
    return requestJson<BackendString>(`/admin/strings/${stringId}`, {
      method: 'PUT',
      body: payload,
      token,
    });
  },
  adminFetchOfficialPerformance(token: string, stringId: string) {
    return requestJson<BackendOfficialPerformance>(
      `/admin/strings/${stringId}/official-performance`,
      { token },
    );
  },
  adminUpdateOfficialPerformance(
    token: string,
    stringId: string,
    payload: BackendOfficialPerformancePayload,
  ) {
    return requestJson<BackendOfficialPerformance>(
      `/admin/strings/${stringId}/official-performance`,
      {
        method: 'PUT',
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
  addBookingUpdate(
    token: string,
    bookingId: string,
    input: {
      comment?: string;
      photo?: BackendUploadFile | null;
      photoType?: BackendBookingPhotoType;
    },
  ) {
    return buildBookingUpdateForm(input).then((formData) =>
      requestFormJson<BackendBooking>(`/bookings/${bookingId}/updates`, {
        formData,
        token,
      }),
    );
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
  generateRecommendations(token: string, top_n = 3) {
    return requestJson<BackendRecommendationResponse>('/recommendations/generate', {
      method: 'POST',
      body: { top_n },
      token,
    });
  },
  fetchCachedRecommendations(token: string, userId = 'me') {
    return requestJson<BackendRecommendationResponse>(
      `/recommendations/${encodeURIComponent(userId)}`,
      { token },
    );
  },
  fetchRecommendationDetail(token: string, userId: string, catalogId: string) {
    return requestJson<BackendRecommendationDetailResponse>(
      `/recommendations/${encodeURIComponent(userId)}/${encodeURIComponent(catalogId)}`,
      { token },
    );
  },
};
