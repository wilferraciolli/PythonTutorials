import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { ProceduresManagementStore } from '../procedures-management.store';

@Component({
  selector: 'app-procedures-management-shell',
  imports: [RouterOutlet],
  providers: [ProceduresManagementStore],
  templateUrl: './procedures-management-shell.html',
  styleUrl: './procedures-management-shell.scss',
})
export class ProceduresManagementShell {}
