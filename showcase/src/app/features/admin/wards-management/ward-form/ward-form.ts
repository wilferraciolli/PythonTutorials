import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormField, FormRoot, required, schema, form } from '@angular/forms/signals';
import { Router, RouterLink } from '@angular/router';

import { WardPayload, WardsManagementStore, injectWardResource } from '../wards-management.store';

interface WardFormModel {
  name: string;
  description: string;
}

const INITIAL_MODEL: WardFormModel = { name: '', description: '' };

const wardSchema = schema<WardFormModel>((path) => {
  required(path.name);
});

@Component({
  selector: 'app-ward-form',
  imports: [RouterLink, FormField, FormRoot],
  templateUrl: './ward-form.html',
  styleUrl: './ward-form.scss',
})
export class WardForm {
  // Bound from the `:id` route param via withComponentInputBinding() —
  // present only on `:id/edit`, undefined on `new`.
  readonly id = input<string>();

  protected readonly store = inject(WardsManagementStore);
  private readonly router = inject(Router);

  protected readonly isEditMode = computed(() => this.id() !== undefined);
  private readonly query = injectWardResource(this.id);
  protected readonly loadingExisting = computed(
    () => this.isEditMode() && this.query.resource.isLoading() && !this.query.ward(),
  );
  protected readonly loadExistingError = this.query.resource.error;

  protected readonly model = signal<WardFormModel>(INITIAL_MODEL);
  protected readonly saveError = signal<string | null>(null);
  protected readonly saving = signal(false);

  protected readonly wardForm = form(this.model, wardSchema, {
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
    // One-shot sync of the async-loaded ward into the writable form model
    // — same justification as DoctorForm's constructor effect.
    effect(() => {
      const ward = this.query.ward();
      if (!ward) return;
      this.model.set({ name: ward.name, description: ward.description ?? '' });
    });
  }

  private async persist(): Promise<void> {
    const value = this.model();
    const payload: WardPayload = { name: value.name, description: value.description || null };

    if (this.isEditMode()) {
      const existing = this.query.ward();
      if (!existing) throw new Error('Ward is still loading — try again.');
      await this.store.updateWard(existing, payload);
      await this.router.navigate(['/admin/wards']);
    } else {
      await this.store.createWard(payload);
      await this.router.navigate(['/admin/wards']);
    }
  }

  private extractErrorMessage(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      return err.error?.detail ?? 'Failed to save ward.';
    }
    return err instanceof Error ? err.message : 'Failed to save ward.';
  }
}
