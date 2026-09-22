import { httpResource } from '@angular/common/http';
import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Envelope, unwrapData } from '../../../core/api/envelope';
import { I18nStore } from '../../../core/i18n/i18n.store';
import { environment } from '../../../../environments/environment';

interface WardSummary {
  id: string;
  bed_count: number;
  available_beds: number;
}

interface BedSummary {
  status: 'ready' | 'preparing' | 'occupied' | 'cleaning';
}

type WardsEnvelope = Envelope<WardSummary[]>;
type BedsEnvelope = Envelope<BedSummary[]>;

const EMPTY_WARDS: WardsEnvelope = { _data: { ward: [] } };
const EMPTY_BEDS: BedsEnvelope = { _data: { bed: [] } };

@Component({
  selector: 'app-admin-dashboard',
  imports: [RouterLink],
  templateUrl: './admin-dashboard.html',
  styleUrl: './admin-dashboard.scss',
})
export class AdminDashboard {
  protected readonly i18n = inject(I18nStore);

  private readonly wardsResource = httpResource<WardsEnvelope>(() => `${environment.apiUrl}/admin/wards`, {
    defaultValue: EMPTY_WARDS,
  });
  private readonly bedsResource = httpResource<BedsEnvelope>(() => `${environment.apiUrl}/beds`, {
    defaultValue: EMPTY_BEDS,
  });

  protected readonly isLoading = computed(() => this.wardsResource.isLoading() || this.bedsResource.isLoading());
  protected readonly loadError = computed(() => this.wardsResource.error() ?? this.bedsResource.error());

  protected readonly wards = computed(() => unwrapData(this.wardsResource.value() ?? EMPTY_WARDS, 'ward') ?? []);
  protected readonly beds = computed(() => unwrapData(this.bedsResource.value() ?? EMPTY_BEDS, 'bed') ?? []);

  protected readonly totalWards = computed(() => this.wards().length);
  protected readonly totalBeds = computed(() => this.beds().length);
  protected readonly readyBeds = computed(() => this.beds().filter((b) => b.status === 'ready').length);
  protected readonly occupiedBeds = computed(() => this.beds().filter((b) => b.status === 'occupied').length);
  protected readonly preparingBeds = computed(() => this.beds().filter((b) => b.status === 'preparing').length);
  protected readonly cleaningBeds = computed(() => this.beds().filter((b) => b.status === 'cleaning').length);
}
