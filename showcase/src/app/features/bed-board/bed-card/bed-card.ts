import { Component, inject, input, output } from '@angular/core';

import { MetadataValue } from '../../../core/api/envelope';
import { I18nStore } from '../../../core/i18n/i18n.store';
import { wardLabel } from '../../../core/i18n/labels';
import { Bed, BedStatus } from '../bed-board.store';

@Component({
  selector: 'app-bed-card',
  templateUrl: './bed-card.html',
  styleUrl: './bed-card.scss',
})
export class BedCard {
  readonly bed = input.required<Bed>();
  // Status selector options come from the API's `_metadata.status.values`
  // — only the set of valid `id`s is taken from there, never `value`
  // (that's English-only backend prose); the display label is always
  // looked up locally via `beds.status.<id>` so it re-translates when the
  // locale changes.
  readonly statusOptions = input.required<MetadataValue[]>();
  readonly statusChange = output<BedStatus>();
  readonly assignProcedure = output<void>();
  readonly adjustDuration = output<void>();

  protected readonly i18n = inject(I18nStore);
  protected readonly wardLabel = wardLabel;

  protected statusLabel(id: string): string {
    return this.i18n.t(`beds.status.${id}`);
  }

  protected emitStatus(id: string): void {
    // Safe cast: `id` always comes from the API's own status metadata.
    this.statusChange.emit(id as BedStatus);
  }

  protected progressPercent(): number {
    const bed = this.bed();
    if (!bed.expected_duration_minutes || bed.occupied_minutes === null) return 0;
    return Math.min(100, (bed.occupied_minutes / bed.expected_duration_minutes) * 100);
  }

  // Clock time reads faster at a glance than raw elapsed/expected minute
  // counts ("28m / 120m") — staff think in "done by 3pm", not "92 minutes
  // left of 120". Uses the org's timezone/locale via I18nStore.formatDate,
  // same as every other timestamp in the app.
  protected occupiedStartTime(): string {
    return this.i18n.formatDate(this.bed().status_changed_at, 'time');
  }

  protected occupiedEndTime(): string {
    const bed = this.bed();
    if (bed.expected_duration_minutes == null) return '';
    const end = new Date(new Date(bed.status_changed_at).getTime() + bed.expected_duration_minutes * 60_000);
    return this.i18n.formatDate(end, 'time');
  }

  // Same reasoning for the remaining/overdue figure — "1:30 remaining"
  // scans faster than "90m remaining".
  protected formatDuration(minutes: number): string {
    const sign = minutes < 0 ? '-' : '';
    const abs = Math.abs(minutes);
    const hours = Math.floor(abs / 60);
    const mins = abs % 60;
    return `${sign}${hours}:${String(mins).padStart(2, '0')}`;
  }
}
