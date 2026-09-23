import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { from, switchMap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AuthStore } from './auth.store';

// Only attaches the token to calls at our own API — never leak the Clerk
// session token to a third-party request.
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(environment.apiUrl)) {
    return next(req);
  }

  const authStore = inject(AuthStore);
  return from(authStore.getToken()).pipe(
    switchMap((token) => {
      const authorizedReq = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
      return next(authorizedReq);
    }),
  );
};
