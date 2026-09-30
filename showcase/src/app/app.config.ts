import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { API_ORIGIN } from '@wiltech-labs/ngx-api-client';
import { provideAuth, authInterceptor } from '@wiltech-labs/ngx-auth';
import { UserSettingsStore } from '@wiltech-labs/ngx-region-settings';

import { I18nService } from './core/i18n/i18n.service';
import { provideI18n } from './core/i18n/i18n.providers';
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
    // Clerk authentication backed by ngx-auth library
    provideAuth({
      clerkPublishableKey: environment.clerkPublishableKey,
      apiOrigin: environment.apiUrl,
      jwtTemplate: environment.clerkJwtTemplate,
    }),
    // ApiClientService.resolve()/requireLink() prefix a link's bare href
    // with this origin — needed because the UI (localhost:4200) and the
    // API (localhost:8001 in dev) are on different origins. Defaults to
    // '' (same-origin), which is wrong here.
    { provide: API_ORIGIN, useValue: environment.apiUrl },
    // Runtime translations (Transloco) — see core/i18n/.
    provideI18n(),
    // User settings store (root-provided so I18nService and the settings
    // page share one instance and one request).
    UserSettingsStore,
    // Created up front so the UI language follows the user's settings from
    // the first render instead of when a component first asks for it.
    provideAppInitializer(() => {
      inject(I18nService);
    }),
  ],
};
