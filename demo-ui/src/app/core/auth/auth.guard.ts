import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthStore } from './auth.store';

/**
 * Gates signed-in-only areas by bouncing back to the public home page,
 * which carries the sign-in button. Unused while home is the only route —
 * kept as the hook for the first guarded route added to app.routes.ts.
 */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthStore);
  const router = inject(Router);
  return auth.isSignedIn() ? true : router.createUrlTree(['/']);
};
