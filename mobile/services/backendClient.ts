export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.trim() ||
  'http://localhost:3001/api';

const REQUEST_TIMEOUT_MS = 12000;
let sessionExpiredHandler: ((expiredToken: string) => void) | null = null;

export class BackendApiError extends Error {
  constructor(
    message: string,
    readonly statusCode?: number,
  ) {
    super(message);
  }
}

export function isBackendAuthError(error: unknown): error is BackendApiError {
  return error instanceof BackendApiError && error.statusCode === 401;
}

export function setBackendSessionExpiredHandler(
  handler: ((expiredToken: string) => void) | null,
) {
  sessionExpiredHandler = handler;
  return () => {
    if (sessionExpiredHandler === handler) {
      sessionExpiredHandler = null;
    }
  };
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  token?: string | null;
  expireSessionOnUnauthorized?: boolean;
};

export function resolveBackendMediaUrl(value?: string | null) {
  if (!value) {
    return undefined;
  }
  if (/^https?:\/\//i.test(value)) {
    return value;
  }
  const rootUrl = API_BASE_URL.replace(/\/api\/?$/, '');
  return `${rootUrl}${value.startsWith('/') ? value : `/${value}`}`;
}

async function request<T>(
  path: string,
  {
    method = 'GET',
    body,
    token,
    expireSessionOnUnauthorized = true,
  }: RequestOptions = {},
  responseType: 'json' | 'text' = 'json',
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const isFormData = body instanceof FormData;

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        Accept: 'application/json',
        ...(body !== undefined && !isFormData
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== undefined
        ? { body: isFormData ? body : JSON.stringify(body) }
        : {}),
      signal: controller.signal,
    });
    const json = (responseType === 'json' || !response.ok
      ? await response.json().catch(() => ({}))
      : undefined) as
      | Record<string, unknown>
      | undefined;

    if (!response.ok) {
      const error = json?.error as { message?: string } | undefined;
      if (token && response.status === 401 && expireSessionOnUnauthorized) {
        sessionExpiredHandler?.(token);
      }
      throw new BackendApiError(
        error?.message ||
          (typeof json?.detail === 'string' ? json.detail : undefined) ||
          'Request failed',
        response.status,
      );
    }
    return (responseType === 'text' ? await response.text() : json) as T;
  } catch (error) {
    if (error instanceof BackendApiError) {
      throw error;
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new BackendApiError(
        `The backend did not respond within ${REQUEST_TIMEOUT_MS / 1000} seconds. Confirm the API is running and EXPO_PUBLIC_API_BASE_URL is correct.`,
      );
    }
    throw new BackendApiError(
      'Unable to reach the backend. Confirm the API is running and EXPO_PUBLIC_API_BASE_URL points to it.',
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

export function requestJson<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  return request<T>(path, options);
}

export function requestFormJson<T>(
  path: string,
  { formData, token }: { formData: FormData; token?: string | null },
): Promise<T> {
  return request<T>(path, { method: 'POST', body: formData, token });
}

export function requestText(
  path: string,
  options: RequestOptions = {},
): Promise<string> {
  return request<string>(path, options, 'text');
}
