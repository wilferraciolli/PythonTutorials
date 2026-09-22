import { Component, inject } from '@angular/core';

import { injectWardIds } from '../../../core/wards/ward-options';
import { wardLabel } from '../../../core/i18n/labels';
import { InsightsStore, VarianceDistribution, WardDurationAnalysis } from '../insights.store';

@Component({
  selector: 'app-insights-page',
  providers: [InsightsStore],
  templateUrl: './insights-page.html',
  styleUrl: './insights-page.scss',
})
export class InsightsPage {
  protected readonly store = inject(InsightsStore);
  protected readonly wardIds = injectWardIds();
  protected readonly wardLabel = wardLabel;

  protected readonly varianceBuckets: { key: keyof VarianceDistribution; label: string }[] = [
    { key: 'very_underutilized', label: '< -30%' },
    { key: 'underutilized', label: '-30% to -10%' },
    { key: 'on_track', label: '-10% to +10%' },
    { key: 'overrun', label: '+10% to +30%' },
    { key: 'very_overrun', label: '> +30%' },
  ];

  protected onWardFilterChange(value: string): void {
    this.store.filters.update((f) => ({ ...f, wardId: value || null }));
  }

  protected onDateFromChange(value: string): void {
    this.store.filters.update((f) => ({ ...f, dateFrom: value ? `${value}T00:00:00` : null }));
  }

  protected onDateToChange(value: string): void {
    this.store.filters.update((f) => ({ ...f, dateTo: value ? `${value}T23:59:59` : null }));
  }

  protected wardSegmentWidth(entry: WardDurationAnalysis, count: number): number {
    return entry.total_occupancies ? (count / entry.total_occupancies) * 100 : 0;
  }

  protected maxBucketPercent(): number {
    return Math.max(1, ...this.varianceBuckets.map((b) => this.store.varianceDistribution()[b.key].percent));
  }
}
