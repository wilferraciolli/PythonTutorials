import { HttpErrorResponse } from '@angular/common/http';

// Every Python tutorial backend in this repo shares one local port (8001)
// and only one runs at a time (see Tutorials/PYTHON_APP_CONVENTIONS.md) —
// so a status-0 failure almost always means "no service is listening on
// 8001 right now" (wrong one running, or none at all), not a real server
// error. Called out explicitly instead of a generic "failed to load".
const UNREACHABLE_MESSAGE =
  "Can't reach the API. Make sure the matching FastAPI service is running locally on port 8001 " +
  '— only one Python tutorial service runs at a time, so stop any other one first.';

/** Turns a failed request into a message the user can actually act on. */
export function describeApiError(error: unknown, fallback: string): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return UNREACHABLE_MESSAGE;
    }

    const detail = (error.error as { detail?: unknown } | null)?.detail;
    return typeof detail === 'string' ? detail : fallback;
  }

  return error instanceof Error ? error.message : fallback;
}
