import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthStore } from './auth.store';

/** Gates the signed-in-only areas. The home page stays public. */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthStore);
  const router = inject(Router);
  return auth.isSignedIn() ? true : router.createUrlTree(['/'], { queryParams: { signin: 1 } });
};
