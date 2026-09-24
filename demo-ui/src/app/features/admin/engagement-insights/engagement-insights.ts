import { httpResource } from '@angular/common/http';
import { Component, computed, inject, input, linkedSignal, signal } from '@angular/core';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatIconModule } from '@angular/material/icon';
import { ApiClientService, ILink, SingleEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../core/api/api-error';
import { Engagement, METRICS, Metric, compact, delta, shortDate } from '../engagement.models';
import { DailyChart } from './daily-chart/daily-chart';

const LABELS: Record<Metric, string> = {
  groups: 'Groups created',
  posts: 'Posts',
  comments: 'Comments',
  likes: 'Likes',
};

const PERIODS = [7, 30, 90] as const;

// Social engagement for the admin area, from the engagement analytics API:
// one row of totals (with the change against the previous period), then a
// daily chart per metric — small multiples, since likes and groups live on
// very different scales — and every number again in a table.
@Component({
  selector: 'app-engagement-insights',
  imports: [MatButtonToggleModule, MatIconModule, DailyChart],
  templateUrl: './engagement-insights.html',
  styleUrl: './engagement-insights.scss',
})
export class EngagementInsights {
  /** The admin hub's `engagementAnalytics` link. */
  readonly link = input<ILink | undefined>();

  private readonly api = inject(ApiClientService);

  protected readonly periods = PERIODS;
  protected readonly days = signal<number>(30);

  private readonly resource = httpResource<SingleEnvelope<'engagement', Engagement>>(() => {
    const url = this.api.resolve(this.link());
    return url ? `${url}?days=${this.days()}` : undefined;
  });

  // Switching the period keeps the last numbers on screen (dimmed) until the
  // new ones arrive, rather than flashing empty.
  protected readonly engagement = linkedSignal<Engagement | undefined, Engagement | undefined>({
    source: () =>
      this.resource.hasValue() ? this.resource.value()._data['engagement'] : undefined,
    computation: (next, previous) => next ?? previous?.value,
  });
  protected readonly refreshing = computed(() => this.resource.isLoading() && !!this.engagement());
  protected readonly errorMessage = computed(() => {
    const error = this.resource.error();
    return error ? describeApiError(error, "Couldn't load engagement.") : null;
  });

  protected readonly tiles = computed(() => {
    const data = this.engagement();
    if (!data) return [];
    return METRICS.map((metric) => ({
      metric,
      label: LABELS[metric],
      value: compact(data.totals[metric]),
      delta: delta(data.totals[metric], data.previousTotals[metric]),
    }));
  });

  protected readonly charts = computed(() => {
    const data = this.engagement();
    if (!data) return [];
    return METRICS.map((metric) => ({
      metric,
      title: LABELS[metric],
      data: data.daily.map((day) => ({ date: day.date, value: day[metric] })),
    }));
  });

  protected readonly range = computed(() => {
    const data = this.engagement();
    return data ? `${shortDate(data.from)} – ${shortDate(data.to)} (UTC)` : '';
  });

  protected readonly metrics = METRICS;
  protected readonly labels = LABELS;
  protected readonly shortDate = shortDate;

  protected choose(days: number): void {
    this.days.set(days);
  }
}
