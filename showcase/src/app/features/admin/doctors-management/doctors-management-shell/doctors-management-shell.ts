import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { DoctorsManagementStore } from '../doctors-management.store';

@Component({
  selector: 'app-doctors-management-shell',
  imports: [RouterOutlet],
  providers: [DoctorsManagementStore],
  templateUrl: './doctors-management-shell.html',
  styleUrl: './doctors-management-shell.scss',
})
export class DoctorsManagementShell {}
