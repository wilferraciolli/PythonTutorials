import { HttpClient, httpResource } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { Envelope, fieldOptions, unwrapData } from '../../../core/api/envelope';
import { environment } from '../../../../environments/environment';

export interface Qualification {
  type: 'board_certification' | 'degree' | 'fellowship' | 'certification' | 'other';
  name: string;
}

export interface Doctor {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  license_number: string;
  specialization: string;
  secondary_specializations: string[];
  ward_id: string | null;
  qualifications: Qualification[];
  bio: string | null;
  years_of_experience: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  links: { self?: { href: string }; update?: { href: string }; delete?: { href: string } };
}

export interface DoctorPayload {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  license_number: string;
  specialization: string;
  secondary_specializations: string[];
  ward_id: string | null;
  qualifications: Qualification[];
  bio: string | null;
  years_of_experience: number | null;
}

export interface DoctorFilters {
  wardId: string | null;
  specialization: string | null;
  isActive: boolean | null;
  search: string;
}

type DoctorsEnvelope = Envelope<Doctor[]>;
type DoctorEnvelope = Envelope<Doctor>;

const EMPTY_LIST_ENVELOPE: DoctorsEnvelope = { _data: { doctor: [] } };
const EMPTY_FILTERS: DoctorFilters = { wardId: null, specialization: null, isActive: null, search: '' };

function buildQuery(filters: DoctorFilters): string {
  const params = new URLSearchParams();
  if (filters.wardId) params.set('ward_id', filters.wardId);
  if (filters.specialization) params.set('specialization', filters.specialization);
  if (filters.isActive !== null) params.set('is_active', String(filters.isActive));
  if (filters.search) params.set('search', filters.search);
  const query = params.toString();
  return query ? `?${query}` : '';
}

// Feature-local state — a plain injectable, not a signalStore, per
// docs/frontend-conventions.md. Provided on DoctorsManagementShell so its
// lifecycle is tied to the /admin/doctors route tree being active.
@Injectable()
export class DoctorsManagementStore {
  private readonly http = inject(HttpClient);

  readonly filters = signal<DoctorFilters>(EMPTY_FILTERS);

  readonly listResource = httpResource<DoctorsEnvelope>(
    () => `${environment.apiUrl}/admin/doctors${buildQuery(this.filters())}`,
    { defaultValue: EMPTY_LIST_ENVELOPE },
  );

  readonly doctors = computed(() => unwrapData(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'doctor') ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());

  readonly totalCount = computed(() => {
    const metadata = this.listResource.value()?._metadata as Record<string, unknown> | undefined;
    const total = metadata?.['total_count'];
    return typeof total === 'number' ? total : this.doctors().length;
  });

  // Specialization selector options straight from the API's metadata —
  // never hardcoded in the UI, so a new/renamed specialization shows up
  // here automatically (mirrors BedBoardStore.statusOptions).
  readonly specializationOptions = computed(() =>
    fieldOptions(this.listResource.value() ?? EMPTY_LIST_ENVELOPE, 'specialization'),
  );

  async createDoctor(payload: DoctorPayload): Promise<Doctor> {
    const response = await firstValueFrom(
      this.http.post<DoctorEnvelope>(`${environment.apiUrl}/admin/doctors`, payload),
    );
    this.listResource.reload();
    return unwrapData(response, 'doctor') as Doctor;
  }

  async updateDoctor(doctor: Doctor, payload: Partial<DoctorPayload> & { is_active?: boolean }): Promise<Doctor> {
    const url = doctor.links.update?.href;
    if (!url) throw new Error(`Not permitted to update doctor ${doctor.id}`);
    const response = await firstValueFrom(this.http.patch<DoctorEnvelope>(`${environment.apiUrl}${url}`, payload));
    this.listResource.reload();
    return unwrapData(response, 'doctor') as Doctor;
  }

  async deleteDoctor(doctor: Doctor): Promise<void> {
    const url = doctor.links.delete?.href;
    if (!url) throw new Error(`Not permitted to delete doctor ${doctor.id}`);
    await firstValueFrom(this.http.delete(`${environment.apiUrl}${url}`));
    this.listResource.reload();
  }
}

// Shared by DoctorDetail and DoctorForm (edit mode): a single-doctor
// httpResource keyed off a reactive id — kept out of DoctorsManagementStore
// since it's driven by a route param, not shared list/filter state.
export function injectDoctorResource(id: () => string | undefined) {
  const resource = httpResource<DoctorEnvelope>(() => {
    const doctorId = id();
    return doctorId ? `${environment.apiUrl}/admin/doctors/${doctorId}` : undefined;
  });
  const doctor = computed(() => {
    const value = resource.value();
    return value ? unwrapData(value, 'doctor') : undefined;
  });
  return { resource, doctor };
}
