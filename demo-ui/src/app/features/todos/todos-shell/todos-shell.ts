import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { TodosStore } from '../todos.store';

@Component({
  selector: 'app-todos-shell',
  imports: [RouterOutlet],
  providers: [TodosStore],
  templateUrl: './todos-shell.html',
  styleUrl: './todos-shell.scss',
})
export class TodosShell {}
