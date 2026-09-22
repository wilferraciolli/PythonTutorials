import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { qualificationTypeLabel, wardLabel } from '../../../../core/i18n/labels';
import { injectDoctorResource } from '../doctors-management.store';

@Component({
  selector: 'app-doctor-detail',
  imports: [RouterLink],
  templateUrl: './doctor-detail.html',
  styleUrl: './doctor-detail.scss',
})
export class DoctorDetail {
  // Bound from the `:id` route param via withComponentInputBinding().
  readonly id = input.required<string>();

  private readonly query = injectDoctorResource(this.id);
  protected readonly doctor = this.query.doctor;
  protected readonly isLoading = this.query.resource.isLoading;
  protected readonly loadError = this.query.resource.error;

  protected readonly wardLabel = wardLabel;
  protected readonly qualificationTypeLabel = qualificationTypeLabel;
}
