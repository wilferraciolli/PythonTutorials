import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { API_ORIGIN } from '@wiliamferraciolli/ngx-api-client';

import { I18nService } from './core/i18n/i18n.service';
import { provideI18n } from './core/i18n/i18n.providers';
import { authInterceptor } from './core/auth/auth.interceptor';
import { AuthStore } from './core/auth/auth.store';
import { routes } from './app.routes';
import { environment } from '../environments/environment';

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
    // Runtime translations (Transloco) — see core/i18n/.
    provideI18n(),
    // Created up front so the UI language follows the user's settings from
    // the first render instead of when a component first asks for it.
    provideAppInitializer(() => {
      inject(I18nService);
    }),
    // Loads Clerk before the app renders so route guards and the interceptor
    // never race a not-yet-loaded instance — see auth.store.ts.
    provideAppInitializer(() => inject(AuthStore).init()),
    // ApiClientService.resolve()/requireLink() prefix a link's bare href
    // with this origin — needed because the UI (localhost:4200) and the
    // API (localhost:8001 in dev) are on different origins. Defaults to
    // '' (same-origin), which is wrong here.
    { provide: API_ORIGIN, useValue: environment.apiUrl },
  ],
};
