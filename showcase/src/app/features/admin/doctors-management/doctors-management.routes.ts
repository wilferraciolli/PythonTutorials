import { Routes } from '@angular/router';

import { DoctorDetail } from './doctor-detail/doctor-detail';
import { DoctorForm } from './doctor-form/doctor-form';
import { DoctorsList } from './doctors-list/doctors-list';
import { DoctorsManagementShell } from './doctors-management-shell/doctors-management-shell';

export const doctorsManagementRoutes: Routes = [
  {
    path: '',
    component: DoctorsManagementShell,
    children: [
      { path: '', component: DoctorsList },
      { path: 'new', component: DoctorForm },
      { path: ':id', component: DoctorDetail },
      { path: ':id/edit', component: DoctorForm },
    ],
  },
];
