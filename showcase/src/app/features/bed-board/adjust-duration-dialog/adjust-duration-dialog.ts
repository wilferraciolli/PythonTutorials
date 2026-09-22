import { HttpErrorResponse } from '@angular/common/http';
import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormField, FormRoot, form, max, min, required, schema } from '@angular/forms/signals';

import { BedBoardStore, ChangeReason, DurationHistoryEntry } from '../bed-board.store';

interface AdjustDurationModel {
  expected_duration_minutes: number;
  change_reason: ChangeReason;
  notes: string;
}

const CHANGE_REASONS: { id: ChangeReason; label: string }[] = [
  { id: 'doctor_adjustment', label: 'Doctor adjustment' },
  { id: 'emergency_extension', label: 'Emergency extension' },
  { id: 'late_procedure', label: 'Procedure running late' },
  { id: 'manual_change', label: 'Manual change' },
];

const adjustDurationSchema = schema<AdjustDurationModel>((path) => {
  required(path.expected_duration_minutes);
  min(path.expected_duration_minutes, 15);
  max(path.expected_duration_minutes, 1440);
});

@Component({
  selector: 'app-adjust-duration-dialog',
  imports: [FormField, FormRoot],
  templateUrl: './adjust-duration-dialog.html',
  styleUrl: './adjust-duration-dialog.scss',
})
export class AdjustDurationDialog {
  readonly bedId = input.required<string>();
  readonly bedNumber = input.required<string>();
  readonly currentDurationMinutes = input.required<number | null>();
  readonly occupiedMinutes = input.required<number | null>();
  readonly closed = output<void>();

  protected readonly store = inject(BedBoardStore);
  protected readonly changeReasons = CHANGE_REASONS;

  protected readonly model = signal<AdjustDurationModel>({
    expected_duration_minutes: 120,
    change_reason: 'doctor_adjustment',
    notes: '',
  });
  protected readonly saveError = signal<string | null>(null);
  protected readonly saving = signal(false);
  protected readonly history = signal<DurationHistoryEntry[]>([]);

  protected readonly durationForm = form(this.model, adjustDurationSchema, {
    submission: {
      action: async () => {
        this.saveError.set(null);
        this.saving.set(true);
        try {
          const value = this.model();
          await this.store.adjustDuration(this.bedId(), {
            expected_duration_minutes: value.expected_duration_minutes,
            change_reason: value.change_reason,
            notes: value.notes || null,
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
    // Required inputs aren't guaranteed set yet during the constructor
    // body itself (e.g. TestBed's createComponent-then-setInput order) —
    // effect() defers this read to after Angular's finished wiring them,
    // same as DoctorForm's constructor effect.
    effect(() => {
      const current = this.currentDurationMinutes();
      this.model.update((m) => ({ ...m, expected_duration_minutes: current ?? 120 }));
    });
    effect(() => {
      const id = this.bedId();
      this.store.getDurationHistory(id).then((history) => this.history.set(history));
    });
  }

  protected onCancel(): void {
    this.closed.emit();
  }

  private extractErrorMessage(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      return err.error?.detail ?? 'Failed to update duration.';
    }
    return err instanceof Error ? err.message : 'Failed to update duration.';
  }
}
