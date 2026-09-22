import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { WardsManagementStore } from '../wards-management.store';

@Component({
  selector: 'app-wards-management-shell',
  imports: [RouterOutlet],
  providers: [WardsManagementStore],
  templateUrl: './wards-management-shell.html',
  styleUrl: './wards-management-shell.scss',
})
export class WardsManagementShell {}
