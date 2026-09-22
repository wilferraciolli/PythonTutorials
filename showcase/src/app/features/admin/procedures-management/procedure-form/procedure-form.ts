import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormField, FormRoot, form, min, required, schema } from '@angular/forms/signals';
import { Router, RouterLink } from '@angular/router';

import {
  ProcedureTypePayload,
  ProceduresManagementStore,
  injectProcedureResource,
} from '../procedures-management.store';

interface ProcedureFormModel {
  name: string;
  description: string;
  category: string;
  typical_duration_minutes: number;
  min_duration_minutes: number | null;
  max_duration_minutes: number | null;
}

const INITIAL_MODEL: ProcedureFormModel = {
  name: '',
  description: '',
  category: '',
  typical_duration_minutes: 60,
  min_duration_minutes: null,
  max_duration_minutes: null,
};

const CATEGORIES = ['surgery', 'diagnostic', 'treatment', 'recovery', 'other'];

const procedureSchema = schema<ProcedureFormModel>((path) => {
  required(path.name);
  required(path.category);
  required(path.typical_duration_minutes);
  min(path.typical_duration_minutes, 15);
});

@Component({
  selector: 'app-procedure-form',
  imports: [RouterLink, FormField, FormRoot],
  templateUrl: './procedure-form.html',
  styleUrl: './procedure-form.scss',
})
export class ProcedureForm {
  // Bound from the `:id` route param via withComponentInputBinding() —
  // present only on `:id/edit`, undefined on `new`.
  readonly id = input<string>();

  protected readonly store = inject(ProceduresManagementStore);
  protected readonly categories = CATEGORIES;
  private readonly router = inject(Router);

  protected readonly isEditMode = computed(() => this.id() !== undefined);
  private readonly query = injectProcedureResource(this.id);
  protected readonly loadingExisting = computed(
    () => this.isEditMode() && this.query.resource.isLoading() && !this.query.procedure(),
  );
  protected readonly loadExistingError = this.query.resource.error;

  protected readonly model = signal<ProcedureFormModel>(INITIAL_MODEL);
  protected readonly saveError = signal<string | null>(null);
  protected readonly saving = signal(false);

  protected readonly procedureForm = form(this.model, procedureSchema, {
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
    // One-shot sync of the async-loaded procedure into the writable form
    // model — same justification as DoctorForm's constructor effect.
    effect(() => {
      const procedure = this.query.procedure();
      if (!procedure) return;
      this.model.set({
        name: procedure.name,
        description: procedure.description ?? '',
        category: procedure.category,
        typical_duration_minutes: procedure.typical_duration_minutes,
        min_duration_minutes: procedure.min_duration_minutes,
        max_duration_minutes: procedure.max_duration_minutes,
      });
    });
  }

  private async persist(): Promise<void> {
    const value = this.model();
    const payload: ProcedureTypePayload = {
      name: value.name,
      description: value.description || null,
      category: value.category,
      typical_duration_minutes: value.typical_duration_minutes,
      min_duration_minutes: value.min_duration_minutes,
      max_duration_minutes: value.max_duration_minutes,
    };

    if (this.isEditMode()) {
      const existing = this.query.procedure();
      if (!existing) throw new Error('Procedure is still loading — try again.');
      await this.store.updateProcedure(existing, payload);
    } else {
      await this.store.createProcedure(payload);
    }
    await this.router.navigate(['/admin/procedures']);
  }

  private extractErrorMessage(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      return err.error?.detail ?? 'Failed to save procedure.';
    }
    return err instanceof Error ? err.message : 'Failed to save procedure.';
  }
}
