import { HttpErrorResponse } from '@angular/common/http';

import { environment } from '../../../environments/environment';

/** Turns a failed request into a message the user can actually act on. */
export function describeApiError(error: unknown, fallback: string): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return unreachable(error.url);
    }

    const detail = (error.error as { detail?: unknown } | null)?.detail;
    return typeof detail === 'string' ? detail : fallback;
  }

  return error instanceof Error ? error.message : fallback;
}

// Status 0 means the browser got no usable answer (offline, blocked, or a
// reply without CORS headers). Say which server it was: a third party such as
// Giphy is not "the API", and only a local dev build should mention port 8001.
function unreachable(url: string | null): string {
  if (url && !url.startsWith(environment.apiUrl)) {
    return (
      `Couldn't reach ${hostOf(url)}. A browser extension (ad or tracker blocker) may be ` +
      'blocking it, or the service is busy. Try again in a moment.'
    );
  }
  return environment.production
    ? "Can't reach the API right now. Check your connection and try again in a moment."
    : `Can't reach the API at ${environment.apiUrl}. Start Tutorials/fastapi-ai locally (port 8001).`;
}

function hostOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return 'that service';
  }
}
