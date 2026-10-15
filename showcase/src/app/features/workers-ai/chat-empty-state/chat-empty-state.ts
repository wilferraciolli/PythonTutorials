import { Component } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { TranslocoPipe } from '@jsverse/transloco';

// Shown at the exact /workers-ai path — before any chat is selected or
// created. WorkersAiShell always renders the sidebar alongside this.
@Component({
  selector: 'app-chat-empty-state',
  imports: [MatIconModule, TranslocoPipe],
  templateUrl: './chat-empty-state.html',
  styleUrl: './chat-empty-state.scss',
})
export class ChatEmptyState {}
