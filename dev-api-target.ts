/** Server-only Vite configuration: never pass credentials through VITE_* vars. */
export function devApiTarget(env: Record<string, string | undefined>): string {
  const value = env.BBY_DEV_API_TARGET?.trim() || 'http://127.0.0.1:8420';
  const url = new URL(value);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password ||
      (url.pathname !== '/' && url.pathname !== '') || url.search || url.hash) {
    throw new Error('BBY_DEV_API_TARGET must be an HTTP(S) origin without credentials');
  }
  const loopback = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if (!loopback && env.BBY_DEV_ALLOW_REMOTE !== '1') {
    throw new Error('Non-local development API targets require BBY_DEV_ALLOW_REMOTE=1');
  }
  return url.origin;
}
