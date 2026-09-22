import { HttpErrorResponse } from '@angular/common/http';
import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormField, FormRoot, form, min, required, schema } from '@angular/forms/signals';

import { BedBoardStore } from '../bed-board.store';

interface AssignProcedureModel {
  procedure_type_id: string;
  expected_duration_minutes: number | null;
  procedure_notes: string;
}

const INITIAL_MODEL: AssignProcedureModel = {
  procedure_type_id: '',
  expected_duration_minutes: null,
  procedure_notes: '',
};

const assignProcedureSchema = schema<AssignProcedureModel>((path) => {
  required(path.procedure_type_id);
  required(path.expected_duration_minutes);
  min(path.expected_duration_minutes, 15);
});

@Component({
  selector: 'app-assign-procedure-dialog',
  imports: [FormField, FormRoot],
  templateUrl: './assign-procedure-dialog.html',
  styleUrl: './assign-procedure-dialog.scss',
})
export class AssignProcedureDialog {
  readonly bedId = input.required<string>();
  readonly bedNumber = input.required<string>();
  readonly closed = output<void>();

  protected readonly store = inject(BedBoardStore);

  protected readonly model = signal<AssignProcedureModel>(INITIAL_MODEL);
  protected readonly saveError = signal<string | null>(null);
  protected readonly saving = signal(false);

  protected readonly assignForm = form(this.model, assignProcedureSchema, {
    submission: {
      action: async () => {
        this.saveError.set(null);
        this.saving.set(true);
        try {
          const value = this.model();
          await this.store.assignProcedure(this.bedId(), {
            procedure_type_id: value.procedure_type_id,
            expected_duration_minutes: value.expected_duration_minutes,
            procedure_notes: value.procedure_notes || null,
          });
          this.closed.emit();
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
    // Pre-fills the duration field from the selected procedure's typical
    // duration — a cross-field default, not a DOM-sync effect, but there's
    // no signals-only way to write into a sibling field from a schema fn.
    effect(() => {
      const current = this.model();
      if (!current.procedure_type_id || current.expected_duration_minutes !== null) return;
      const procedure = this.store.procedures().find((p) => p.id === current.procedure_type_id);
      if (procedure) {
        this.model.update((m) => ({ ...m, expected_duration_minutes: procedure.typical_duration_minutes }));
      }
    });
  }

  protected onCancel(): void {
    this.closed.emit();
  }

  private extractErrorMessage(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      return err.error?.detail ?? 'Failed to assign procedure.';
    }
    return err instanceof Error ? err.message : 'Failed to assign procedure.';
  }
}
