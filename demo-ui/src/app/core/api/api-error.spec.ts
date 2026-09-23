import { HttpErrorResponse } from '@angular/common/http';

import { environment } from '../../../environments/environment';
import { describeApiError } from './api-error';

describe('describeApiError', () => {
  it('names a third-party host instead of blaming the API', () => {
    const error = new HttpErrorResponse({
      status: 0,
      url: 'https://api.giphy.com/v1/gifs/search?q=x',
    });
    const message = describeApiError(error, 'fallback');
    expect(message).toContain('api.giphy.com');
    expect(message).not.toContain('8001');
  });

  it('points at the API when our own API is unreachable', () => {
    const error = new HttpErrorResponse({ status: 0, url: `${environment.apiUrl}/api/me` });
    expect(describeApiError(error, 'fallback')).toContain("Can't reach the API");
  });

  it('uses the API detail, then the fallback', () => {
    expect(
      describeApiError(new HttpErrorResponse({ status: 400, error: { detail: 'Bad id' } }), 'x'),
    ).toBe('Bad id');
    expect(describeApiError(new HttpErrorResponse({ status: 500 }), 'Something failed')).toBe(
      'Something failed',
    );
  });
});
