import { Component, Signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import { ICellRendererParams } from 'ag-grid-community';

import { Doctor } from '../../doctors-management.store';

export interface DoctorActionsContext {
  pendingId: Signal<string | null>;
  onDelete: (doctor: Doctor) => void;
}

// `.App-button` (styles.scss) is a truly global class (not scoped to
// DoctorsList's component styles, which this cell renderer sits outside
// of), so it applies here with no local styling needed.
@Component({
  selector: 'app-doctor-actions-cell',
  imports: [RouterLink],
  template: `
    <div class="DoctorActionsCell">
      <a class="App-button App-button-secondary App-button-sm" [routerLink]="['/admin/doctors', doctor.id, 'edit']">Edit</a>
      <button
        type="button"
        class="App-button App-button-danger App-button-sm"
        [disabled]="context.pendingId() === doctor.id"
        (click)="context.onDelete(doctor)"
      >
        {{ context.pendingId() === doctor.id ? 'Deactivating…' : 'Deactivate' }}
      </button>
    </div>
  `,
  styles: `
    .DoctorActionsCell {
      display: flex;
      gap: 0.5rem;
      align-items: center;
      height: 100%;
    }
  `,
})
export class DoctorActionsCell implements ICellRendererAngularComp {
  protected doctor!: Doctor;
  protected context!: DoctorActionsContext;

  agInit(params: ICellRendererParams<Doctor> & { context: DoctorActionsContext }): void {
    this.doctor = params.data!;
    this.context = params.context;
  }

  refresh(params: ICellRendererParams<Doctor> & { context: DoctorActionsContext }): boolean {
    this.doctor = params.data!;
    this.context = params.context;
    return true;
  }
}
