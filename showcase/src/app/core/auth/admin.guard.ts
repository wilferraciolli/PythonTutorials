import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { CurrentUserStore } from '../user/current-user.store';

// Protects /admin — checks the role on the caller's own profile (the
// backend enforces this independently on every /admin/* endpoint via
// require_admin_user_id; this guard is purely a UX shortcut so a
// non-admin never sees the admin shell flash before an API call 403s).
export const adminGuard: CanActivateFn = async () => {
  const currentUser = inject(CurrentUserStore);
  const router = inject(Router);

  const profile = await currentUser.ensureLoaded();
  if (profile.role === 'admin') {
    return true;
  }
  return router.createUrlTree(['/profile']);
};
