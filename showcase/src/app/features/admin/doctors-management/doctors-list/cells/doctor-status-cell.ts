import { Component } from '@angular/core';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import { ICellRendererParams } from 'ag-grid-community';

import { Doctor } from '../../doctors-management.store';

@Component({
  selector: 'app-doctor-status-cell',
  template: `
    <span class="DoctorStatusCell-badge" [class.is-active]="doctor.is_active">
      {{ doctor.is_active ? 'Active' : 'Inactive' }}
    </span>
  `,
  styles: `
    .DoctorStatusCell-badge {
      display: inline-block;
      background: #ddd;
      color: #333;
      border-radius: 999px;
      padding: 0.15rem 0.6rem;
      font-size: 0.75rem;

      &.is-active {
        background: #dff5e1;
        color: #1e7d34;
      }
    }
  `,
})
export class DoctorStatusCell implements ICellRendererAngularComp {
  protected doctor!: Doctor;

  agInit(params: ICellRendererParams<Doctor>): void {
    this.doctor = params.data!;
  }

  refresh(params: ICellRendererParams<Doctor>): boolean {
    this.doctor = params.data!;
    return true;
  }
}
