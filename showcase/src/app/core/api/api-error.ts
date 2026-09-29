import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';

import { TranslationService } from '../i18n/translation.service';

// Every Python tutorial backend in this repo shares one local port (8001)
// and only one runs at a time (see Tutorials/PYTHON_APP_CONVENTIONS.md) —
// so a status-0 failure almost always means "no service is listening on
// 8001 right now" (wrong one running, or none at all), not a real server
// error. Called out explicitly (`errors.unreachable`) instead of a generic
// "failed to load".

/** Turns a failed request into a message the user can actually act on. */
@Injectable({ providedIn: 'root' })
export class ApiErrors {
  private readonly i18n = inject(TranslationService);

  /**
   * `fallbackKey` is a translation key, used when the API gave no message of
   * its own. The API's own `detail` text is shown as it arrives.
   */
  describe(error: unknown, fallbackKey: string): string {
    if (error instanceof HttpErrorResponse) {
      if (error.status === 0) {
        return this.i18n.t('errors.unreachable');
      }

      const detail = (error.error as { detail?: unknown } | null)?.detail;
      return typeof detail === 'string' ? detail : this.i18n.t(fallbackKey);
    }

    return error instanceof Error ? error.message : this.i18n.t(fallbackKey);
  }
}
