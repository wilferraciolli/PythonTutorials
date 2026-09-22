import { HttpClient, httpResource } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';

import { Envelope, unwrapData } from '../../core/api/envelope';
import { environment } from '../../../environments/environment';

export interface InsightsOverview {
  total_beds: number;
  occupied_beds: number;
  preparing_beds: number;
  ready_beds: number;
  cleaning_beds: number;
  availability_rate: number;
  occupancy_rate: number;
  avg_occupancy_duration: number | null;
  avg_duration_variance: number | null;
  overdue_beds: number;
}

export interface WardDurationAnalysis {
  ward_id: string;
  ward_name: string;
  total_occupancies: number;
  on_track: number;
  overrun: number;
  underutilized: number;
  avg_variance_percent: number;
  total_overrun_minutes: number;
  total_underutil_minutes: number;
}

export interface VarianceBucket {
  count: number;
  percent: number;
}

export interface VarianceDistribution {
  very_underutilized: VarianceBucket;
  underutilized: VarianceBucket;
  on_track: VarianceBucket;
  overrun: VarianceBucket;
  very_overrun: VarianceBucket;
}

export interface InsightsFilters {
  wardId: string | null;
  dateFrom: string | null;
  dateTo: string | null;
}

type OverviewEnvelope = Envelope<InsightsOverview>;
type DurationAnalysisEnvelope = Envelope<WardDurationAnalysis[]>;
type VarianceDistributionEnvelope = Envelope<VarianceDistribution>;

const EMPTY_FILTERS: InsightsFilters = { wardId: null, dateFrom: null, dateTo: null };
const EMPTY_DISTRIBUTION: VarianceDistribution = {
  very_underutilized: { count: 0, percent: 0 },
  underutilized: { count: 0, percent: 0 },
  on_track: { count: 0, percent: 0 },
  overrun: { count: 0, percent: 0 },
  very_overrun: { count: 0, percent: 0 },
};

function buildQuery(filters: InsightsFilters): string {
  const params = new URLSearchParams();
  if (filters.wardId) params.set('ward_id', filters.wardId);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  const query = params.toString();
  return query ? `?${query}` : '';
}

// Feature-local state — a plain injectable, not a signalStore, per
// docs/frontend-conventions.md. Provided on InsightsPage; there's only
// one page in this feature, so no shared shell is needed.
@Injectable()
export class InsightsStore {
  private readonly http = inject(HttpClient);

  readonly filters = signal<InsightsFilters>(EMPTY_FILTERS);

  readonly overviewResource = httpResource<OverviewEnvelope>(
    () => `${environment.apiUrl}/insights/overview${buildQuery(this.filters())}`,
  );
  readonly durationAnalysisResource = httpResource<DurationAnalysisEnvelope>(
    () => `${environment.apiUrl}/insights/occupancy-duration-analysis${buildQuery(this.filters())}`,
    { defaultValue: { _data: { duration_analysis: [] } } },
  );
  readonly varianceDistributionResource = httpResource<VarianceDistributionEnvelope>(
    () => `${environment.apiUrl}/insights/duration-variance-distribution${buildQuery(this.filters())}`,
  );

  readonly overview = computed(() => {
    const value = this.overviewResource.value();
    return value ? unwrapData(value, 'overview') : undefined;
  });
  readonly durationAnalysis = computed(
    () =>
      unwrapData(
        this.durationAnalysisResource.value() ?? { _data: { duration_analysis: [] } },
        'duration_analysis',
      ) ?? [],
  );
  readonly varianceDistribution = computed(() => {
    const value = this.varianceDistributionResource.value();
    return value ? unwrapData(value, 'variance_distribution') ?? EMPTY_DISTRIBUTION : EMPTY_DISTRIBUTION;
  });

  readonly isLoading = computed(
    () =>
      this.overviewResource.isLoading() ||
      this.durationAnalysisResource.isLoading() ||
      this.varianceDistributionResource.isLoading(),
  );
  readonly loadError = computed(
    () => this.overviewResource.error() ?? this.durationAnalysisResource.error() ?? this.varianceDistributionResource.error(),
  );
}
