import { HttpClient, httpResource } from '@angular/common/http';
import { Injectable, computed, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { Envelope, fieldOptions, unwrapData } from '../../../core/api/envelope';
import { environment } from '../../../../environments/environment';

export interface ProcedureType {
  id: string;
  name: string;
  description: string | null;
  category: string;
  typical_duration_minutes: number;
  min_duration_minutes: number | null;
  max_duration_minutes: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  links: { self?: { href: string }; update?: { href: string }; delete?: { href: string } };
}

export interface ProcedureTypePayload {
  name: string;
  description: string | null;
  category: string;
  typical_duration_minutes: number;
  min_duration_minutes: number | null;
  max_duration_minutes: number | null;
}

type ProceduresEnvelope = Envelope<ProcedureType[]>;
type ProcedureEnvelope = Envelope<ProcedureType>;

const EMPTY_LIST_ENVELOPE: ProceduresEnvelope = { _data: { procedure: [] } };

// Feature-local state — a plain injectable, provided on
// ProceduresManagementShell (mirrors DoctorsManagementStore/WardsManagementStore).
@Injectable()
export class ProceduresManagementStore {
  private readonly http = inject(HttpClient);

  readonly listResource = httpResource<ProceduresEnvelope>(() => `${environment.apiUrl}/procedures`, {
    defaultValue: EMPTY_LIST_ENVELOPE,
  });

  readonly procedures = computed(
    () => unwrapData(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'procedure') ?? [],
  );
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());
  readonly categoryOptions = computed(() =>
    fieldOptions(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'category'),
  );

  async createProcedure(payload: ProcedureTypePayload): Promise<ProcedureType> {
    const response = await firstValueFrom(
      this.http.post<ProcedureEnvelope>(`${environment.apiUrl}/procedures`, payload),
    );
    this.listResource.reload();
    return unwrapData(response, 'procedure') as ProcedureType;
  }

  async updateProcedure(procedure: ProcedureType, payload: Partial<ProcedureTypePayload>): Promise<ProcedureType> {
    const url = procedure.links.update?.href;
    if (!url) throw new Error(`Not permitted to update procedure ${procedure.id}`);
    const response = await firstValueFrom(this.http.patch<ProcedureEnvelope>(`${environment.apiUrl}${url}`, payload));
    this.listResource.reload();
    return unwrapData(response, 'procedure') as ProcedureType;
  }

  async deleteProcedure(procedure: ProcedureType): Promise<void> {
    const url = procedure.links.delete?.href;
    if (!url) throw new Error(`Not permitted to delete procedure ${procedure.id}`);
    await firstValueFrom(this.http.delete(`${environment.apiUrl}${url}`));
    this.listResource.reload();
  }
}

export function injectProcedureResource(id: () => string | undefined) {
  const resource = httpResource<ProcedureEnvelope>(() => {
    const procedureId = id();
    return procedureId ? `${environment.apiUrl}/procedures/${procedureId}` : undefined;
  });
  const procedure = computed(() => {
    const value = resource.value();
    return value ? unwrapData(value, 'procedure') : undefined;
  });
  return { resource, procedure };
}
