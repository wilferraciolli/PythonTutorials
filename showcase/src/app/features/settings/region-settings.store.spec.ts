import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Type, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ILink } from '@wiliamferraciolli/ngx-api-client';

import { CurrentUserStore } from '../../core/user/current-user.store';
import {
  RegionSettingsStore,
  SystemSettingsStore,
  UserSettingsStore,
} from './region-settings.store';

// A stand-in for the profile: just the links the settings screens follow.
function fakeCurrentUser(links: Record<string, ILink>) {
  return {
    loading: signal(false),
    profile: signal({ links }),
    link: (name: string) => links[name],
  };
}

const USER_SETTINGS_ENVELOPE = {
  _data: {
    userSettings: {
      id: 'u1',
      owner_type: 'SYSTEM',
      timezone: 'Europe/London',
      language: 'en-GB',
      currency: 'GBP',
      theme: 'light',
      links: { updateSettings: { href: '/api/users/u1/settings', method: 'PUT' } },
    },
  },
  _metadata: {
    theme: {
      mandatory: true,
      values: [
        { id: 'light', value: 'light' },
        { id: 'dark', value: 'dark' },
      ],
    },
  },
  _metaLinks: {},
  _messages: [],
};

describe('RegionSettingsStore', () => {
  function setup<T extends RegionSettingsStore>(store: Type<T>, links: Record<string, ILink>) {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        store,
        { provide: CurrentUserStore, useValue: fakeCurrentUser(links) },
      ],
    });
    return { store: TestBed.inject(store), http: TestBed.inject(HttpTestingController) };
  }

  it('follows the userSettings profile link and exposes the metadata options', async () => {
    const { store, http } = setup(UserSettingsStore, {
      userSettings: { href: '/api/users/u1/settings' },
    });
    TestBed.tick();

    http
      .expectOne((req) => req.url.endsWith('/api/users/u1/settings'))
      .flush(USER_SETTINGS_ENVELOPE);
    await Promise.resolve();

    expect(store.settings()?.timezone).toBe('Europe/London');
    expect(store.options().theme).toEqual([
      { value: 'light', viewValue: 'light' },
      { value: 'dark', viewValue: 'dark' },
    ]);
    expect(store.notAvailable()).toBe(false);
  });

  it('makes no request and reports not available without the systemSettings link', () => {
    const { store, http } = setup(SystemSettingsStore, {
      userSettings: { href: '/api/users/u1/settings' },
    });
    TestBed.tick();

    http.expectNone(() => true);
    expect(store.notAvailable()).toBe(true);
  });
});
