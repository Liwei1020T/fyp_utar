export function shouldExpireBackendSession(
  currentToken: string | null,
  failedToken: string,
): boolean {
  return currentToken === failedToken;
}
