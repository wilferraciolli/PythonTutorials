import { HttpClient, httpResource } from '@angular/common/http';
import { Injectable, computed, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { Envelope, ResourceLinks, unwrapData } from '../../../core/api/envelope';
import { environment } from '../../../../environments/environment';

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  job_title: string | null;
  role: 'user' | 'admin';
  links: ResourceLinks;
}

type UsersEnvelope = Envelope<AdminUser[]>;
type UserEnvelope = Envelope<AdminUser>;

const EMPTY_LIST_ENVELOPE: UsersEnvelope = { _data: { user: [] } };

// Feature-local state — a plain injectable, provided directly on the
// `users` route (mirrors WardsManagementStore, minus the shell wrapper:
// there's no create/edit sub-route here, just the one list).
@Injectable()
export class UsersManagementStore {
  private readonly http = inject(HttpClient);

  readonly listResource = httpResource<UsersEnvelope>(() => `${environment.apiUrl}/admin/users`, {
    defaultValue: EMPTY_LIST_ENVELOPE,
  });

  readonly users = computed(() => unwrapData(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'user') ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());

  async setRole(user: AdminUser, role: 'user' | 'admin'): Promise<AdminUser> {
    const url = user.links.update?.href;
    if (!url) throw new Error(`Not permitted to update user ${user.id}`);
    const response = await firstValueFrom(this.http.patch<UserEnvelope>(`${environment.apiUrl}${url}`, { role }));
    this.listResource.reload();
    return unwrapData(response, 'user') as AdminUser;
  }
}
