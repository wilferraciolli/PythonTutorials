import { HttpClient, httpResource } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { firstValueFrom, interval, startWith } from 'rxjs';
import { toSignal } from '@angular/core/rxjs-interop';

import { Envelope, ResourceLinks, fieldOptions, unwrapData } from '../../core/api/envelope';
import { environment } from '../../../environments/environment';

export type BedStatus = 'ready' | 'preparing' | 'occupied' | 'cleaning';

export interface ProcedureTypeSummary {
  id: string;
  name: string;
  typical_duration_minutes: number;
}

export interface ProcedureType extends ProcedureTypeSummary {
  description: string | null;
  category: string;
  min_duration_minutes: number | null;
  max_duration_minutes: number | null;
  is_active: boolean;
}

export interface Bed {
  id: string;
  bed_number: string;
  ward_id: string;
  status: BedStatus;
  status_changed_at: string;
  expected_duration_minutes: number | null;
  occupied_minutes: number | null;
  is_overdue: boolean;
  overdue_minutes: number;
  remaining_minutes: number | null;
  current_procedure_type_id: string | null;
  procedure_type: ProcedureTypeSummary | null;
  procedure_notes: string | null;
  duration_changed_at: string | null;
  links: ResourceLinks;
}

export type ChangeReason =
  | 'procedure_assignment'
  | 'doctor_adjustment'
  | 'emergency_extension'
  | 'manual_change'
  | 'late_procedure';

export interface AssignProcedurePayload {
  procedure_type_id: string;
  expected_duration_minutes?: number | null;
  procedure_notes?: string | null;
}

export interface AdjustDurationPayload {
  expected_duration_minutes: number;
  change_reason: ChangeReason;
  notes?: string | null;
}

export interface DurationHistoryEntry {
  id: string;
  old_duration_minutes: number | null;
  new_duration_minutes: number;
  procedure_type_id: string | null;
  changed_by: string;
  change_reason: ChangeReason;
  changed_at: string;
}

type BedsEnvelope = Envelope<Bed[]>;
type ProceduresEnvelope = Envelope<ProcedureType[]>;
type DurationHistoryEnvelope = Envelope<DurationHistoryEntry[]>;

const EMPTY_ENVELOPE: BedsEnvelope = { _data: { bed: [] } };
const EMPTY_PROCEDURES_ENVELOPE: ProceduresEnvelope = { _data: { procedure: [] } };
const EMPTY_HISTORY_ENVELOPE: DurationHistoryEnvelope = { _data: { duration_history: [] } };
const POLL_INTERVAL_MS = 60_000;

// Feature-local state — a plain injectable, not a signalStore, per
// docs/frontend-conventions.md (signalStore is reserved for app-wide state
// like AuthStore). Provided on the shell component, not root, so its
// lifecycle (and polling) is tied to the feature being active.
@Injectable()
export class BedBoardStore {
  private readonly http = inject(HttpClient);

  // Ward filtering happens client-side against the full beds list (below),
  // not as a server-side query param — the API's ward_id filter only
  // accepts one value (resource-management-api/src/routers/beds.py), and
  // deriving wardIds from a ward-filtered fetch was the bug: selecting a
  // ward shrank the fetched set down to that one ward, which made the
  // other filter chips disappear. An empty set means "no filter" (show
  // all wards).
  readonly wardFilters = signal<ReadonlySet<string>>(new Set());

  // RxJS interop for the poll ticker, per conventions doc — signals are
  // still the state model, this is just bridging a timer into one.
  private readonly pollTick = toSignal(interval(POLL_INTERVAL_MS).pipe(startWith(0)), { initialValue: 0 });

  readonly bedsResource = httpResource<BedsEnvelope>(
    () => {
      this.pollTick();
      return `${environment.apiUrl}/beds`;
    },
    { defaultValue: EMPTY_ENVELOPE },
  );

  // Active procedure types for the assign-procedure picker — fetched once
  // per shell lifetime (procedures rarely change mid-session), not polled.
  readonly proceduresResource = httpResource<ProceduresEnvelope>(
    () => `${environment.apiUrl}/procedures?is_active=true`,
    { defaultValue: EMPTY_PROCEDURES_ENVELOPE },
  );

  // Every poll re-fetches the full list and parses a brand-new object
  // graph, even when nothing changed — so a plain `computed` here would
  // hand every `<app-bed-card>` a new `bed` object reference each time,
  // and Angular has no way to know the fields are actually identical.
  // That forced every card to re-render on every poll (visible flicker),
  // including reassigning `<option [selected]>` on the status dropdown,
  // which closes an open native picker out from under the user mid-tap.
  // This keeps the *same* Bed reference across polls for any bed whose
  // data hasn't changed, so only cards that actually changed re-render —
  // a signal input compares by reference, so an identical reference is a
  // no-op, not just a cheap update.
  private readonly bedIdentity = new Map<string, Bed>();
  private readonly _beds = signal<Bed[]>([]);
  readonly beds = this._beds.asReadonly();

  constructor() {
    effect(() => {
      const raw = unwrapData(this.bedsResource.value() ?? EMPTY_ENVELOPE, 'bed') ?? [];
      const next = raw.map((bed) => {
        const prev = this.bedIdentity.get(bed.id);
        const stable = prev && JSON.stringify(prev) === JSON.stringify(bed) ? prev : bed;
        this.bedIdentity.set(bed.id, stable);
        return stable;
      });
      const nextIds = new Set(next.map((bed) => bed.id));
      for (const id of this.bedIdentity.keys()) {
        if (!nextIds.has(id)) this.bedIdentity.delete(id);
      }
      this._beds.set(next);
    });
  }

  readonly isLoading = computed(() => this.bedsResource.isLoading());
  readonly loadError = computed(() => this.bedsResource.error());
  // Derived from the full (unfiltered) beds list, so the set of chips on
  // offer never shrinks as filters are applied.
  readonly wardIds = computed(() => [...new Set(this.beds().map((bed) => bed.ward_id))].sort());
  readonly filteredBeds = computed(() => {
    const filters = this.wardFilters();
    const beds = this.beds();
    return filters.size === 0 ? beds : beds.filter((bed) => filters.has(bed.ward_id));
  });
  readonly overdueCount = computed(() => this.filteredBeds().filter((bed) => bed.is_overdue).length);
  readonly procedures = computed(
    () => unwrapData(this.proceduresResource.value() ?? EMPTY_PROCEDURES_ENVELOPE, 'procedure') ?? [],
  );

  // Selector options straight from the API's metadata — never hardcoded
  // in the UI, so a new/renamed status shows up here automatically.
  readonly statusOptions = computed(() => fieldOptions(this.bedsResource.value() ?? EMPTY_ENVELOPE, 'status'));

  clearWardFilters(): void {
    this.wardFilters.set(new Set());
  }

  async updateStatus(bedId: string, status: BedStatus): Promise<void> {
    await firstValueFrom(this.http.patch(`${environment.apiUrl}/beds/${bedId}/status`, { status }));
    this.bedsResource.reload();
  }

  async assignProcedure(bedId: string, payload: AssignProcedurePayload): Promise<void> {
    await firstValueFrom(this.http.post(`${environment.apiUrl}/beds/${bedId}/procedure`, payload));
    this.bedsResource.reload();
  }

  async adjustDuration(bedId: string, payload: AdjustDurationPayload): Promise<void> {
    await firstValueFrom(this.http.patch(`${environment.apiUrl}/beds/${bedId}/duration`, payload));
    this.bedsResource.reload();
  }

  async getDurationHistory(bedId: string): Promise<DurationHistoryEntry[]> {
    const response = await firstValueFrom(
      this.http.get<DurationHistoryEnvelope>(`${environment.apiUrl}/beds/${bedId}/duration-history`),
    );
    return unwrapData(response ?? EMPTY_HISTORY_ENVELOPE, 'duration_history') ?? [];
  }
}
