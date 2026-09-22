import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { CurrentUserStore } from '../user/current-user.store';
import { I18nStore } from './i18n.store';

// A minimal but well-formed /me envelope — updateProfile() unwraps
// `_data.user`, so a bare `{}` would throw inside the background persist
// call that setLocale() fires.
const ME_RESPONSE = {
  _data: {
    user: {
      id: 'u1',
      name: 'Test User',
      email: 't@example.com',
      phone: null,
      job_title: null,
      role: 'user',
      ward_id: null,
      language: 'en-GB',
      admin_profile: null,
    },
  },
};

describe('I18nStore', () => {
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    // The organization httpResource and any background /me persist calls
    // may or may not have fired synchronously within a given test — drain
    // whatever did without asserting on timing we don't control here.
    httpMock.match(() => true).forEach((req) => req.flush({ _data: {} }));
  });

  it('falls back to el-GR before the organization has loaded', () => {
    const store = TestBed.inject(I18nStore);
    expect(store.locale()).toBe('el-GR');
  });

  it('translates a known key and falls back to the key itself when missing', () => {
    const store = TestBed.inject(I18nStore);
    expect(store.t('common.buttons.save')).toBe('Αποθήκευση');
    expect(store.t('common.nonexistent.key')).toBe('common.nonexistent.key');
  });

  it('substitutes params in a translated string', () => {
    const store = TestBed.inject(I18nStore);
    store.setLocale('en-GB');
    expect(store.t('beds.card.overdueBadge', { count: 3 })).toBe('3 overdue');
  });

  it('applies a locale change instantly for the session, without waiting on the persist call', () => {
    const store = TestBed.inject(I18nStore);
    store.setLocale('en-GB');
    expect(store.locale()).toBe('en-GB');
    expect(store.t('common.buttons.save')).toBe('Save');
  });

  it('formats a UTC instant in the fallback (Europe/Athens) timezone before the organization loads', () => {
    const store = TestBed.inject(I18nStore);
    // June -> EEST (UTC+3)
    expect(store.formatDate('2024-06-15T12:00:00Z', 'time')).toBe('15:00');
  });

  it('persists a locale change server-side via PATCH /me once signed in', async () => {
    const store = TestBed.inject(I18nStore);
    const currentUser = TestBed.inject(CurrentUserStore);

    // Reach a "signed in, profile loaded" state the same way the app does.
    const loaded = currentUser.ensureLoaded();
    httpMock.expectOne(`${environment.apiUrl}/me`).flush(ME_RESPONSE);
    await loaded;

    store.setLocale('en-GB');

    const requests = httpMock.match(`${environment.apiUrl}/me`);
    expect(requests.length).toBe(1);
    expect(requests[0].request.method).toBe('PATCH');
    expect(requests[0].request.body).toEqual({ language: 'en-GB' });
    requests[0].flush(ME_RESPONSE);
  });

  it('does not call PATCH /me while signed out (no profile loaded)', () => {
    const store = TestBed.inject(I18nStore);
    store.setLocale('en-GB');

    expect(httpMock.match(`${environment.apiUrl}/me`).length).toBe(0);
  });
});
