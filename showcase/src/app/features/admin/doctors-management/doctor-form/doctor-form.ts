import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormField, FormRoot, email, form, min, required, schema } from '@angular/forms/signals';
import { Router, RouterLink } from '@angular/router';

import { injectWardIds } from '../../../../core/wards/ward-options';
import { QUALIFICATION_TYPES, qualificationTypeLabel, wardLabel } from '../../../../core/i18n/labels';
import { DoctorPayload, DoctorsManagementStore, Qualification, injectDoctorResource } from '../doctors-management.store';

interface DoctorFormModel {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  license_number: string;
  specialization: string;
  ward_id: string;
  bio: string;
  years_of_experience: number | null;
  is_active: boolean;
}

const INITIAL_MODEL: DoctorFormModel = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  license_number: '',
  specialization: '',
  ward_id: '',
  bio: '',
  years_of_experience: null,
  is_active: true,
};

const doctorSchema = schema<DoctorFormModel>((path) => {
  required(path.first_name);
  required(path.last_name);
  required(path.email);
  email(path.email);
  required(path.phone);
  required(path.license_number);
  required(path.specialization);
  min(path.years_of_experience, 0);
});

@Component({
  selector: 'app-doctor-form',
  imports: [RouterLink, FormField, FormRoot],
  templateUrl: './doctor-form.html',
  styleUrl: './doctor-form.scss',
})
export class DoctorForm {
  // Bound from the `:id` route param via withComponentInputBinding() —
  // present only on the `:id/edit` route, undefined on `new`.
  readonly id = input<string>();

  protected readonly store = inject(DoctorsManagementStore);
  protected readonly wardIds = injectWardIds();
  protected readonly wardLabel = wardLabel;
  protected readonly qualificationTypes = QUALIFICATION_TYPES;
  protected readonly qualificationTypeLabel = qualificationTypeLabel;

  private readonly router = inject(Router);

  protected readonly isEditMode = computed(() => this.id() !== undefined);
  private readonly query = injectDoctorResource(this.id);
  protected readonly loadingExisting = computed(() => this.isEditMode() && this.query.resource.isLoading() && !this.query.doctor());
  protected readonly loadExistingError = this.query.resource.error;

  protected readonly model = signal<DoctorFormModel>(INITIAL_MODEL);
  protected readonly secondarySpecializations = signal<string[]>([]);
  protected readonly qualifications = signal<Qualification[]>([]);
  protected readonly saveError = signal<string | null>(null);
  protected readonly saving = signal(false);

  protected readonly doctorForm = form(this.model, doctorSchema, {
    submission: {
      action: async () => {
        this.saveError.set(null);
        this.saving.set(true);
        try {
          await this.persist();
        } catch (err) {
          this.saveError.set(this.extractErrorMessage(err));
        } finally {
          this.saving.set(false);
        }
        return undefined;
      },
    },
  });

  constructor() {
    // Prefills the writable form model once the existing doctor loads —
    // there is no signals-only way to seed a WritableSignal from an async
    // resource, so this is a genuine (one-shot, per doctor id) sync effect.
    effect(() => {
      const doctor = this.query.doctor();
      if (!doctor) return;
      this.model.set({
        first_name: doctor.first_name,
        last_name: doctor.last_name,
        email: doctor.email,
        phone: doctor.phone,
        license_number: doctor.license_number,
        specialization: doctor.specialization,
        ward_id: doctor.ward_id ?? '',
        bio: doctor.bio ?? '',
        years_of_experience: doctor.years_of_experience,
        is_active: doctor.is_active,
      });
      this.secondarySpecializations.set(doctor.secondary_specializations);
      this.qualifications.set(doctor.qualifications);
    });
  }

  protected toggleSecondarySpecialization(value: string, checked: boolean): void {
    this.secondarySpecializations.update((list) =>
      checked ? [...list, value] : list.filter((v) => v !== value),
    );
  }

  protected addQualification(): void {
    this.qualifications.update((list) => [...list, { type: 'degree', name: '' }]);
  }

  protected removeQualification(index: number): void {
    this.qualifications.update((list) => list.filter((_, i) => i !== index));
  }

  protected updateQualificationType(index: number, type: Qualification['type']): void {
    this.qualifications.update((list) => list.map((q, i) => (i === index ? { ...q, type } : q)));
  }

  protected updateQualificationName(index: number, name: string): void {
    this.qualifications.update((list) => list.map((q, i) => (i === index ? { ...q, name } : q)));
  }

  private async persist(): Promise<void> {
    const value = this.model();
    const payload: DoctorPayload = {
      first_name: value.first_name,
      last_name: value.last_name,
      email: value.email,
      phone: value.phone,
      license_number: value.license_number,
      specialization: value.specialization,
      secondary_specializations: this.secondarySpecializations(),
      ward_id: value.ward_id || null,
      qualifications: this.qualifications(),
      bio: value.bio || null,
      years_of_experience: value.years_of_experience,
    };

    if (this.isEditMode()) {
      const existing = this.query.doctor();
      if (!existing) throw new Error('Doctor is still loading — try again.');
      const updated = await this.store.updateDoctor(existing, { ...payload, is_active: value.is_active });
      await this.router.navigate(['/admin/doctors', updated.id]);
    } else {
      const created = await this.store.createDoctor(payload);
      await this.router.navigate(['/admin/doctors', created.id]);
    }
  }

  private extractErrorMessage(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      return err.error?.detail ?? 'Failed to save doctor.';
    }
    return err instanceof Error ? err.message : 'Failed to save doctor.';
  }
}
