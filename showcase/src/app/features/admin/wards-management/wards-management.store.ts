import { HttpClient, httpResource } from '@angular/common/http';
import { Injectable, computed, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { Envelope, unwrapData } from '../../../core/api/envelope';
import { environment } from '../../../../environments/environment';

export interface Ward {
  id: string;
  name: string;
  description: string | null;
  bed_count: number;
  available_beds: number;
  created_at: string;
  updated_at: string;
  links: { self?: { href: string }; update?: { href: string }; delete?: { href: string } };
}

export interface WardPayload {
  name: string;
  description: string | null;
}

type WardsEnvelope = Envelope<Ward[]>;
type WardEnvelope = Envelope<Ward>;

const EMPTY_LIST_ENVELOPE: WardsEnvelope = { _data: { ward: [] } };

// Feature-local state — a plain injectable, not a signalStore, provided on
// WardsManagementShell (mirrors DoctorsManagementStore).
@Injectable()
export class WardsManagementStore {
  private readonly http = inject(HttpClient);

  readonly listResource = httpResource<WardsEnvelope>(() => `${environment.apiUrl}/admin/wards`, {
    defaultValue: EMPTY_LIST_ENVELOPE,
  });

  readonly wards = computed(() => unwrapData(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'ward') ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());

  async createWard(payload: WardPayload): Promise<Ward> {
    const response = await firstValueFrom(this.http.post<WardEnvelope>(`${environment.apiUrl}/admin/wards`, payload));
    this.listResource.reload();
    return unwrapData(response, 'ward') as Ward;
  }

  async updateWard(ward: Ward, payload: Partial<WardPayload>): Promise<Ward> {
    const url = ward.links.update?.href;
    if (!url) throw new Error(`Not permitted to update ward ${ward.id}`);
    const response = await firstValueFrom(this.http.patch<WardEnvelope>(`${environment.apiUrl}${url}`, payload));
    this.listResource.reload();
    return unwrapData(response, 'ward') as Ward;
  }

  async deleteWard(ward: Ward): Promise<void> {
    const url = ward.links.delete?.href;
    if (!url) throw new Error(`Not permitted to delete ward ${ward.id}`);
    await firstValueFrom(this.http.delete(`${environment.apiUrl}${url}`));
    this.listResource.reload();
  }
}

export function injectWardResource(id: () => string | undefined) {
  const resource = httpResource<WardEnvelope>(() => {
    const wardId = id();
    return wardId ? `${environment.apiUrl}/admin/wards/${wardId}` : undefined;
  });
  const ward = computed(() => {
    const value = resource.value();
    return value ? unwrapData(value, 'ward') : undefined;
  });
  return { resource, ward };
}
