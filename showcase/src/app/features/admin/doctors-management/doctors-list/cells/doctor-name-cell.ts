import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import { ICellRendererParams } from 'ag-grid-community';

import { Doctor } from '../../doctors-management.store';

// AG Grid cell renderer: name as a real routerLink (not a plain <a href>,
// which would force a full page reload instead of client-side navigation).
// Angular scopes component styles to their own template, so this carries
// its own small stylesheet rather than relying on doctors-list.scss, which
// cell renderers sit outside of.
@Component({
  selector: 'app-doctor-name-cell',
  imports: [RouterLink],
  template: `
    <a class="DoctorNameCell-link" [class.is-inactive]="!doctor.is_active" [routerLink]="['/admin/doctors', doctor.id]">
      {{ doctor.first_name }} {{ doctor.last_name }}
    </a>
  `,
  styles: `
    .DoctorNameCell-link {
      color: #1a1a1a;
      font-weight: 600;
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }

      &.is-inactive {
        color: #777;
        font-weight: 500;
      }
    }
  `,
})
export class DoctorNameCell implements ICellRendererAngularComp {
  protected doctor!: Doctor;

  agInit(params: ICellRendererParams<Doctor>): void {
    this.doctor = params.data!;
  }

  refresh(params: ICellRendererParams<Doctor>): boolean {
    this.doctor = params.data!;
    return true;
  }
}
