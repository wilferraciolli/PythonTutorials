import { HttpClient } from '@angular/common/http';
import { computed, inject } from '@angular/core';
import { patchState, signalStore, withComputed, withMethods, withState } from '@ngrx/signals';
import { firstValueFrom } from 'rxjs';

import { Envelope, unwrapData } from '../api/envelope';
import { environment } from '../../../environments/environment';

export interface AdminProfile {
  can_manage_wards: boolean;
  can_manage_beds: boolean;
  can_manage_users: boolean;
  permissions: string[];
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  job_title: string | null;
  role: 'user' | 'admin';
  ward_id: string | null;
  // Nullable — null means "use the organization's default_language" (see
  // core/i18n/i18n.store.ts and docs/features/internationalization-i18n.md).
  language: 'el-GR' | 'en-GB' | null;
  admin_profile: AdminProfile | null;
}

export interface UserProfileUpdate {
  name?: string;
  phone?: string;
  job_title?: string;
  language?: 'el-GR' | 'en-GB';
}

type MeEnvelope = Envelope<UserProfile>;

interface CurrentUserState {
  profile: UserProfile | null;
  loading: boolean;
  loaded: boolean;
}

const initialState: CurrentUserState = { profile: null, loading: false, loaded: false };

// App-wide state (like AuthStore) — every route needs to know the caller's
// role (admin-gating, the profile menu, /profile), not just one feature.
export const CurrentUserStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed(({ profile }) => ({
    isAdmin: computed(() => profile()?.role === 'admin'),
  })),
  withMethods((store) => {
    const http = inject(HttpClient);
    let inFlight: Promise<UserProfile> | null = null;

    async function load(): Promise<UserProfile> {
      patchState(store, { loading: true });
      const response = await firstValueFrom(http.get<MeEnvelope>(`${environment.apiUrl}/me`));
      const profile = unwrapData(response, 'user') as UserProfile;
      patchState(store, { profile, loading: false, loaded: true });
      return profile;
    }

    return {
      load,

      // Guards, the profile menu, and every page that needs the role all
      // call this independently — dedupe concurrent callers onto the same
      // in-flight request instead of firing one GET /me each.
      async ensureLoaded(): Promise<UserProfile> {
        if (store.loaded() && store.profile()) {
          return store.profile() as UserProfile;
        }
        if (!inFlight) {
          inFlight = load().finally(() => {
            inFlight = null;
          });
        }
        return inFlight;
      },

      async updateProfile(payload: UserProfileUpdate): Promise<UserProfile> {
        const response = await firstValueFrom(http.patch<MeEnvelope>(`${environment.apiUrl}/me`, payload));
        const profile = unwrapData(response, 'user') as UserProfile;
        patchState(store, { profile });
        return profile;
      },

      reset(): void {
        patchState(store, initialState);
      },
    };
  }),
);
