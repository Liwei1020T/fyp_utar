import type {
  BackendAdminInventoryString,
  BackendAdminFeedbackSummary,
  BackendAdminDeviceToken,
  BackendAdminFeedback,
  BackendAdminNotification,
  BackendAgentQuery,
  BackendAgentResponse,
  BackendAnalyticsSummary,
  BackendAuthResponse,
  BackendCheckInLookupResponse,
  BackendCheckInRequest,
  BackendCheckInToken,
  BackendBooking,
  BackendBookingConversation,
  BackendBookingPaymentQuote,
  BackendCreateFeedbackPayload,
  BackendCreateRacketPayload,
  BackendFeedbackSummary,
  BackendFeedback,
  BackendForgotPasswordRequestResponse,
  BackendInventoryUpdatePayload,
  BackendMarkNotificationsReadPayload,
  BackendMarkNotificationsReadResponse,
  BackendMessageResponse,
  BackendNotification,
  BackendNotificationPreferences,
  BackendNotificationPreferencesPayload,
  BackendPrivacySettings,
  BackendOfficialPerformance,
  BackendPage,
  BackendPayment,
  BackendPopularString,
  BackendProfile,
  BackendProfilePayload,
  BackendRecommendationDetailResponse,
  BackendRecommendationResponse,
  BackendRecommendationRun,
  BackendRacket,
  BackendRacketDetail,
  BackendRacketModelOption,
  BackendSendConversationMessagePayload,
  BackendServiceQueue,
  BackendSlot,
  BackendStoreBusinessHours,
  BackendStoreBusinessHoursPayload,
  BackendStoreSettings,
  BackendStoreSettingsPayload,
  BackendString,
  BackendStringEditorUpdatePayload,
  BackendUpdateRacketPayload,
  BackendUpdateFeedbackPayload,
  BackendWallet,
} from '../types/backend';
import { Platform } from 'react-native';
import {
  API_BASE_URL,
  requestFormJson,
  requestJson,
  requestText,
} from './backendClient';

export {
  BackendApiError,
  isBackendAuthError,
  resolveBackendMediaUrl,
  setBackendSessionExpiredHandler,
} from './backendClient';

export type BackendUploadFile = {
  uri: string;
  name: string;
  type: string;
};

export type BackendBookingPhotoType = 'racket' | 'service_progress' | 'other';

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

async function buildPaymentForm(input: {
  method: 'qr_transfer' | 'cash' | 'wallet_balance';
  amount?: number;
  expectedAmount?: number;
  proof?: BackendUploadFile | null;
}) {
  const formData = new FormData();
  formData.append('method', input.method);
  if (input.amount != null) {
    formData.append('amount', String(input.amount));
  }
  if (input.expectedAmount != null) {
    formData.append('expected_amount', String(input.expectedAmount));
  }
  if (input.proof) {
    formData.append('proof', await normalizeUploadFile(input.proof));
  }
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
  changePassword(
    token: string,
    payload: { current_password: string; new_password: string },
  ) {
    return requestJson<BackendMessageResponse>('/auth/change-password', {
      method: 'POST',
      body: payload,
      token,
      expireSessionOnUnauthorized: false,
    });
  },
  requestAccountDeletion(token: string, reason?: string) {
    return requestJson<{
      id: string;
      status: string;
      reason: string | null;
      requested_at: string;
    }>('/auth/delete-account-request', {
      method: 'POST',
      body: { reason: reason?.trim() || null },
      token,
    });
  },
  fetchProfile(token: string) {
    return requestJson<BackendProfile | null>('/profile', { token });
  },
  saveProfile(token: string, payload: BackendProfilePayload) {
    return requestJson<BackendProfile>('/profile', {
      method: 'PUT',
      body: payload,
      token,
    });
  },
  fetchPrivacySettings(token: string) {
    return requestJson<BackendPrivacySettings>('/profile/privacy', { token });
  },
  updatePrivacySettings(token: string, payload: BackendPrivacySettings) {
    return requestJson<BackendPrivacySettings>('/profile/privacy', {
      method: 'PUT',
      body: payload,
      token,
    });
  },
  fetchNotificationPreferences(token: string) {
    return requestJson<BackendNotificationPreferences>(
      '/notifications/preferences',
      { token },
    );
  },
  updateNotificationPreferences(
    token: string,
    payload: BackendNotificationPreferencesPayload,
  ) {
    return requestJson<BackendNotificationPreferences>(
      '/notifications/preferences',
      {
        method: 'PUT',
        body: payload,
        token,
      },
    );
  },
  listNotifications(token: string, limit = 100) {
    const searchParams = new URLSearchParams({ limit: String(limit) });
    return requestJson<BackendNotification[]>(
      `/notifications?${searchParams.toString()}`,
      { token },
    );
  },
  markNotificationsRead(
    token: string,
    payload: BackendMarkNotificationsReadPayload,
  ) {
    return requestJson<BackendMarkNotificationsReadResponse>(
      '/notifications/read',
      {
        method: 'PATCH',
        body: payload,
        token,
      },
    );
  },
  listPayments(token: string) {
    return requestJson<BackendPayment[]>('/payments', { token });
  },
  fetchBookingPaymentQuote(token: string, bookingId: string) {
    return requestJson<BackendBookingPaymentQuote>(
      `/payments/bookings/${bookingId}/quote`,
      { token },
    );
  },
  createBookingPayment(
    token: string,
    bookingId: string,
    method: 'qr_transfer' | 'cash' | 'wallet_balance',
    expectedAmount?: number,
    proof?: BackendUploadFile | null,
  ) {
    return buildPaymentForm({ method, expectedAmount, proof }).then((formData) =>
      requestFormJson<BackendPayment>(`/payments/bookings/${bookingId}`, {
        formData,
        token,
      }),
    );
  },
  fetchWallet(token: string) {
    return requestJson<BackendWallet>('/wallet', { token });
  },
  requestWalletTopUp(
    token: string,
    payload: {
      amount: number;
      method: 'qr_transfer' | 'cash';
      proof?: BackendUploadFile | null;
    },
  ) {
    return buildPaymentForm(payload).then((formData) =>
      requestFormJson<BackendPayment>('/wallet/top-ups', {
        formData,
        token,
      }),
    );
  },
  adminListPayments(token: string) {
    return requestJson<BackendPayment[]>('/admin/payments', { token });
  },
  adminUpdatePayment(
    token: string,
    paymentId: string,
    status: 'paid' | 'failed' | 'cancelled',
  ) {
    return requestJson<BackendPayment>(`/admin/payments/${paymentId}`, {
      method: 'PATCH',
      body: { status },
      token,
    });
  },
  adminUploadPaymentQr(token: string, photo: BackendUploadFile) {
    return buildImageUploadForm({ photo }).then((formData) =>
      requestFormJson<BackendStoreSettings>('/admin/store-settings/payment-qr', {
        formData,
        token,
      }),
    );
  },
  adminDeletePaymentQr(token: string) {
    return requestJson<BackendStoreSettings>('/admin/store-settings/payment-qr', {
      method: 'DELETE',
      token,
    });
  },
  listStrings(token: string) {
    return requestJson<BackendPage<BackendString>>('/strings', { token });
  },
  fetchFeedbackSummary(token: string) {
    return requestJson<BackendFeedbackSummary>('/strings/feedback-summary', {
      token,
    });
  },
  listBookings(token: string) {
    return requestJson<BackendPage<BackendBooking>>('/bookings', { token });
  },
  fetchBooking(token: string, bookingId: string) {
    return requestJson<BackendBooking>(`/bookings/${bookingId}`, { token });
  },
  cancelBooking(token: string, bookingId: string, reason: string) {
    return requestJson<BackendBooking>(`/bookings/${bookingId}/cancel`, {
      method: 'POST',
      body: { reason },
      token,
    });
  },
  createCheckInToken(token: string, bookingId: string) {
    return requestJson<BackendCheckInToken>(
      `/bookings/${bookingId}/check-in-token`,
      { method: 'POST', token },
    );
  },
  listPlayerConversations(token: string) {
    return requestJson<BackendBookingConversation[]>('/conversations', {
      token,
    });
  },
  requestBookingSupport(token: string, bookingId: string) {
    return requestJson<BackendBookingConversation>(
      `/bookings/${bookingId}/support`,
      {
        method: 'POST',
        token,
      },
    );
  },
  requestGeneralSupport(token: string) {
    return requestJson<BackendBookingConversation>('/conversations/support', {
      method: 'POST',
      token,
    });
  },
  fetchPlayerConversation(token: string, conversationId: string) {
    return requestJson<BackendBookingConversation>(
      `/conversations/${conversationId}`,
      { token },
    );
  },
  sendPlayerConversationMessage(
    token: string,
    conversationId: string,
    payload: BackendSendConversationMessagePayload,
  ) {
    return requestJson<BackendBookingConversation>(
      `/conversations/${conversationId}/messages`,
      {
        method: 'POST',
        body: payload,
        token,
      },
    );
  },
  markPlayerConversationRead(token: string, conversationId: string) {
    return requestJson<BackendBookingConversation>(
      `/conversations/${conversationId}/read`,
      {
        method: 'POST',
        token,
      },
    );
  },
  adminListConversations(token: string) {
    return requestJson<BackendBookingConversation[]>('/admin/conversations', {
      token,
    });
  },
  adminFetchConversation(token: string, conversationId: string) {
    return requestJson<BackendBookingConversation>(
      `/admin/conversations/${conversationId}`,
      { token },
    );
  },
  adminSendConversationMessage(
    token: string,
    conversationId: string,
    payload: BackendSendConversationMessagePayload,
  ) {
    return requestJson<BackendBookingConversation>(
      `/admin/conversations/${conversationId}/messages`,
      {
        method: 'POST',
        body: payload,
        token,
      },
    );
  },
  adminMarkConversationRead(token: string, conversationId: string) {
    return requestJson<BackendBookingConversation>(
      `/admin/conversations/${conversationId}/read`,
      {
        method: 'POST',
        token,
      },
    );
  },
  adminResolveConversation(token: string, conversationId: string) {
    return requestJson<BackendBookingConversation>(
      `/admin/conversations/${conversationId}/resolve`,
      {
        method: 'POST',
        token,
      },
    );
  },
  adminCloseConversation(token: string, conversationId: string) {
    return requestJson<BackendBookingConversation>(
      `/admin/conversations/${conversationId}/close`,
      {
        method: 'POST',
        token,
      },
    );
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
    payload: {
      status: string;
      note?: string;
      expected_completion_datetime?: string | null;
    },
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
  adminLookupSecureCheckIn(token: string, qrToken: string) {
    return requestJson<BackendCheckInLookupResponse>('/admin/check-in/lookup', {
      method: 'POST',
      body: { token: qrToken },
      token,
    });
  },
  adminConfirmSecureCheckIn(
    token: string,
    qrToken: string,
    note?: string,
  ) {
    return requestJson<BackendBooking>('/admin/check-in/confirm', {
      method: 'POST',
      body: { token: qrToken, note: note?.trim() || null },
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
  fetchStoreSettings(token: string) {
    return requestJson<BackendStoreSettings>('/store-settings', {
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
  adminAnalyticsSummary(token: string, days: 7 | 30 = 7) {
    return requestJson<BackendAnalyticsSummary>(
      `/admin/analytics/summary?days=${days}`,
      { token },
    );
  },
  adminPopularStrings(token: string, limit = 5) {
    const searchParams = new URLSearchParams({ limit: String(limit) });
    return requestJson<BackendPopularString[]>(
      `/admin/analytics/popular-strings?${searchParams.toString()}`,
      { token },
    );
  },
  adminListFeedback(
    token: string,
    params?: {
      booking_id?: string;
      string_id?: string;
      rating?: number;
      date_from?: string;
      date_to?: string;
      limit?: number;
      offset?: number;
    },
  ) {
    const searchParams = new URLSearchParams();
    if (params?.booking_id) searchParams.set('booking_id', params.booking_id);
    if (params?.string_id) searchParams.set('string_id', params.string_id);
    if (params?.rating != null) searchParams.set('rating', String(params.rating));
    if (params?.date_from) searchParams.set('date_from', params.date_from);
    if (params?.date_to) searchParams.set('date_to', params.date_to);
    if (params?.limit != null) searchParams.set('limit', String(params.limit));
    if (params?.offset != null) searchParams.set('offset', String(params.offset));
    const suffix = searchParams.size ? `?${searchParams.toString()}` : '';
    return requestJson<BackendPage<BackendAdminFeedback>>(
      `/admin/feedback${suffix}`,
      { token },
    );
  },
  adminFetchFeedbackSummary(token: string) {
    return requestJson<BackendAdminFeedbackSummary>('/admin/feedback/summary', {
      token,
    });
  },
  async adminExportFeedback(
    token: string,
    params?: {
      booking_id?: string;
      string_id?: string;
      rating?: number;
      date_from?: string;
      date_to?: string;
    },
  ) {
    const searchParams = new URLSearchParams();
    if (params?.booking_id) searchParams.set('booking_id', params.booking_id);
    if (params?.string_id) searchParams.set('string_id', params.string_id);
    if (params?.rating != null) searchParams.set('rating', String(params.rating));
    if (params?.date_from) searchParams.set('date_from', params.date_from);
    if (params?.date_to) searchParams.set('date_to', params.date_to);
    const suffix = searchParams.size ? `?${searchParams.toString()}` : '';
    return requestText(`/admin/feedback/export${suffix}`, { token });
  },
  adminListNotifications(token: string, status?: string) {
    const suffix = status
      ? `?${new URLSearchParams({ status }).toString()}`
      : '';
    return requestJson<BackendAdminNotification[]>(
      `/admin/notifications${suffix}`,
      { token },
    );
  },
  adminListDeviceTokens(token: string) {
    return requestJson<BackendAdminDeviceToken[]>('/admin/device-tokens', {
      token,
    });
  },
  adminSendNotification(
    token: string,
    payload: {
      user_id: string;
      category: BackendAdminNotification['category'];
      title: string;
      body: string;
      route?: string | null;
    },
  ) {
    return requestJson<BackendAdminNotification>('/admin/notifications', {
      method: 'POST',
      body: payload,
      token,
    });
  },
  adminResendNotification(token: string, notificationId: string) {
    return requestJson<BackendAdminNotification>(
      `/admin/notifications/${notificationId}/resend`,
      { method: 'POST', token },
    );
  },
  adminListRecommendationRuns(
    token: string,
    params?: {
      phone_number?: string;
      algorithm_version?: string;
      limit?: number;
      offset?: number;
    },
  ) {
    const searchParams = new URLSearchParams();
    if (params?.phone_number) {
      searchParams.set('phone_number', params.phone_number);
    }
    if (params?.algorithm_version) {
      searchParams.set('algorithm_version', params.algorithm_version);
    }
    if (params?.limit != null) {
      searchParams.set('limit', String(params.limit));
    }
    if (params?.offset != null) {
      searchParams.set('offset', String(params.offset));
    }
    const suffix = searchParams.size > 0 ? `?${searchParams.toString()}` : '';
    return requestJson<BackendPage<BackendRecommendationRun>>(
      `/admin/recommendations/runs${suffix}`,
      { token },
    );
  },
  adminFetchRecommendationRun(token: string, runId: string) {
    return requestJson<BackendRecommendationRun>(
      `/admin/recommendations/runs/${runId}`,
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
  adminUpdateStringEditor(
    token: string,
    stringId: string,
    payload: BackendStringEditorUpdatePayload,
  ) {
    return requestJson<BackendAdminInventoryString>(
      `/admin/inventory/strings/${stringId}/editor`,
      {
        method: 'PUT',
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
  adminFetchOfficialPerformance(token: string, stringId: string) {
    return requestJson<BackendOfficialPerformance>(
      `/admin/strings/${stringId}/official-performance`,
      { token },
    );
  },
  createBooking(
    token: string,
    payload: {
      string_id: string;
      racket_id?: string;
      racket_brand?: string;
      racket_model?: string;
      requested_tension?: number;
      slot_id?: string;
      drop_off_datetime?: string;
      notes?: string;
      service_method?: 'counter_dropoff' | 'pickup_request';
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
  listRackets(token: string) {
    return requestJson<BackendRacket[]>('/rackets', { token });
  },
  listRacketModels(token: string) {
    return requestJson<BackendRacketModelOption[]>('/racket-models', { token });
  },
  createRacket(token: string, payload: BackendCreateRacketPayload) {
    return requestJson<BackendRacket>('/rackets', {
      method: 'POST',
      body: payload,
      token,
    });
  },
  fetchRacket(token: string, racketId: string) {
    return requestJson<BackendRacketDetail>(`/rackets/${racketId}`, { token });
  },
  updateRacket(
    token: string,
    racketId: string,
    payload: BackendUpdateRacketPayload,
  ) {
    return requestJson<BackendRacket>(`/rackets/${racketId}`, {
      method: 'PATCH',
      body: payload,
      token,
    });
  },
  deleteRacket(token: string, racketId: string) {
    return requestJson<BackendMessageResponse>(`/rackets/${racketId}`, {
      method: 'DELETE',
      token,
    });
  },
  createBookingFeedback(
    token: string,
    bookingId: string,
    payload: BackendCreateFeedbackPayload,
  ) {
    return requestJson<BackendFeedback>(`/bookings/${bookingId}/feedback`, {
      method: 'POST',
      body: payload,
      token,
    });
  },
  updateBookingFeedback(
    token: string,
    bookingId: string,
    payload: BackendUpdateFeedbackPayload,
  ) {
    return requestJson<BackendFeedback>(`/bookings/${bookingId}/feedback`, {
      method: 'PATCH',
      body: payload,
      token,
    });
  },
  fetchBookingFeedback(token: string, bookingId: string) {
    return requestJson<BackendFeedback | null>(`/bookings/${bookingId}/feedback`, {
      token,
    });
  },
  generateRecommendations(token: string, top_n = 3, racket_id?: string) {
    return requestJson<BackendRecommendationResponse>('/recommendations/generate', {
      method: 'POST',
      body: { top_n, racket_id },
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
  queryAgent(token: string, payload: BackendAgentQuery) {
    return requestJson<BackendAgentResponse>('/agent/query', {
      method: 'POST',
      body: payload,
      token,
    });
  },
};
