import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { authInterceptor } from './core/auth/auth.interceptor';
import { AuthStore } from './core/auth/auth.store';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    // withComponentInputBinding: routed components read route/query params
    // as plain `input()`s instead of subscribing to ActivatedRoute.
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor])),
    // Material's components (the home page's button ripple) need an
    // animations driver; the async variant lazy-loads the animations
    // package instead of putting it in the initial bundle.
    provideAnimationsAsync(),
    // Loads Clerk before the app renders so route guards and the interceptor
    // never race a not-yet-loaded instance — see auth.store.ts.
    provideAppInitializer(() => inject(AuthStore).init()),
  ],
};
