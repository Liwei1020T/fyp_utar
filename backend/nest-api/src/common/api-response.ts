export interface SuccessPayload<T> {
  success: true;
  message: string;
  data: T;
}

export interface PaginatedPayload<T> extends SuccessPayload<T[]> {
  pagination: {
    total: number;
    limit: number | null;
    offset: number;
  };
}

export function successResponse<T>(message: string, data: T): SuccessPayload<T> {
  return {
    success: true,
    message,
    data,
  };
}

export function paginatedResponse<T>(
  message: string,
  data: T[],
  total: number,
  limit: number | null,
  offset: number,
): PaginatedPayload<T> {
  return {
    success: true,
    message,
    data,
    pagination: {
      total,
      limit,
      offset,
    },
  };
}
