import { Component, computed, inject, signal } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Router, RouterLink } from '@angular/router';
import { AgGridAngular } from 'ag-grid-angular';
import { AllCommunityModule, ColDef, ModuleRegistry } from 'ag-grid-community';
import { firstValueFrom } from 'rxjs';

// Imported here (not angular.json's global `styles`) so this ~300KB of CSS
// ships only in the lazy `admin` chunk instead of on every page — bedside
// staff loading the bed board never touch this route.
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';

import { injectWardIds } from '../../../../core/wards/ward-options';
import { wardLabel } from '../../../../core/i18n/labels';
import { ConfirmDialog } from '../../../../shared/confirm-dialog/confirm-dialog';
import { DoctorActionsCell, DoctorActionsContext } from './cells/doctor-actions-cell';
import { DoctorNameCell } from './cells/doctor-name-cell';
import { DoctorStatusCell } from './cells/doctor-status-cell';
import { Doctor, DoctorsManagementStore } from '../doctors-management.store';

ModuleRegistry.registerModules([AllCommunityModule]);

@Component({
  selector: 'app-doctors-list',
  imports: [RouterLink, AgGridAngular],
  templateUrl: './doctors-list.html',
  styleUrl: './doctors-list.scss',
})
export class DoctorsList {
  protected readonly store = inject(DoctorsManagementStore);
  protected readonly wardIds = injectWardIds();
  protected readonly wardLabel = wardLabel;

  private readonly router = inject(Router);
  private readonly dialog = inject(MatDialog);

  protected readonly actionError = signal<string | null>(null);
  protected readonly pendingId = signal<string | null>(null);

  // Read by the actions cell renderer via the grid's `context` — AG Grid
  // renders cell components outside this component's own template, so
  // they can't reach `onDelete`/`pendingId` any other way.
  protected readonly gridContext: DoctorActionsContext = {
    pendingId: this.pendingId,
    onDelete: (doctor) => void this.onDelete(doctor),
  };

  // License number and years of experience are left out deliberately —
  // personal/credentialing detail that belongs on the doctor's own detail
  // page (doctor-detail.html still shows them), not in the scan-at-a-glance
  // list.
  protected readonly columnDefs: ColDef<Doctor>[] = [
    {
      headerName: 'Name',
      cellRenderer: DoctorNameCell,
      flex: 1.3,
      minWidth: 160,
      comparator: (_a, _b, nodeA, nodeB) =>
        `${nodeA.data?.first_name} ${nodeA.data?.last_name}`.localeCompare(`${nodeB.data?.first_name} ${nodeB.data?.last_name}`),
    },
    { headerName: 'Email', field: 'email', flex: 1.4, minWidth: 180 },
    { headerName: 'Specialization', field: 'specialization', flex: 1, minWidth: 140 },
    {
      headerName: 'Ward',
      flex: 0.9,
      minWidth: 110,
      valueGetter: (params) => (params.data?.ward_id ? this.wardLabel(params.data.ward_id) : 'All Wards'),
    },
    { headerName: 'Status', cellRenderer: DoctorStatusCell, flex: 0.7, minWidth: 100 },
    {
      headerName: '',
      cellRenderer: DoctorActionsCell,
      flex: 1,
      minWidth: 160,
      sortable: false,
      filter: false,
      resizable: false,
    },
  ];

  protected readonly defaultColDef: ColDef<Doctor> = {
    sortable: true,
    resizable: true,
  };

  protected readonly rowData = computed(() => this.store.doctors());

  protected onSearchChange(value: string): void {
    this.store.filters.update((f) => ({ ...f, search: value }));
  }

  protected onWardFilterChange(value: string): void {
    this.store.filters.update((f) => ({ ...f, wardId: value || null }));
  }

  protected onSpecializationFilterChange(value: string): void {
    this.store.filters.update((f) => ({ ...f, specialization: value || null }));
  }

  protected onActiveFilterChange(value: string): void {
    const isActive = value === '' ? null : value === 'true';
    this.store.filters.update((f) => ({ ...f, isActive }));
  }

  protected async onDelete(doctor: Doctor): Promise<void> {
    const dialogRef = this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Deactivate doctor',
        message: `Deactivate Dr. ${doctor.first_name} ${doctor.last_name}? Their history is preserved and they can be reactivated later.`,
        confirmLabel: 'Deactivate',
        tone: 'danger',
      },
    });
    const confirmed = await firstValueFrom(dialogRef.afterClosed());
    if (!confirmed) {
      return;
    }

    this.actionError.set(null);
    this.pendingId.set(doctor.id);
    try {
      await this.store.deleteDoctor(doctor);
    } catch {
      this.actionError.set(`Couldn't deactivate Dr. ${doctor.first_name} ${doctor.last_name} — check the API is reachable.`);
    } finally {
      this.pendingId.set(null);
    }
  }

  protected viewDoctor(doctor: Doctor): void {
    this.router.navigate(['/admin/doctors', doctor.id]);
  }
}
