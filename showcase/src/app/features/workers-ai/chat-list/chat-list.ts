import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';

import { ChatsStore } from '../chats.store';

@Component({
  selector: 'app-chat-list',
  imports: [RouterLink, RouterLinkActive, MatButtonModule, MatIconModule],
  templateUrl: './chat-list.html',
  styleUrl: './chat-list.scss',
})
export class ChatList {
  protected readonly store = inject(ChatsStore);
  private readonly router = inject(Router);

  protected readonly creating = signal(false);

  protected async newChat(): Promise<void> {
    if (this.creating()) return;

    this.creating.set(true);
    try {
      const chat = await this.store.createChat();
      await this.router.navigate(['/workers-ai', chat.id]);
    } finally {
      this.creating.set(false);
    }
  }
}
