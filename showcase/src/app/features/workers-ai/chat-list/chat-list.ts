import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';

import { describeApiError } from '../../../core/api/api-error';
import { Chat, ChatsStore } from '../chats.store';

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
  protected readonly editingChatId = signal<string | null>(null);
  protected readonly editingTitle = signal('');
  protected readonly savingChatId = signal<string | null>(null);
  protected readonly renameError = signal<string | null>(null);

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

  protected startEditing(chat: Chat): void {
    this.editingChatId.set(chat.id);
    this.editingTitle.set(chat.title);
    this.renameError.set(null);
  }

  protected cancelEditing(): void {
    this.editingChatId.set(null);
    this.editingTitle.set('');
    this.renameError.set(null);
  }

  protected async saveTitle(chat: Chat): Promise<void> {
    const title = this.editingTitle().trim();
    if (!title) {
      this.renameError.set('A chat name is required.');
      return;
    }

    this.savingChatId.set(chat.id);
    this.renameError.set(null);
    try {
      await this.store.updateTitle(chat, title);
      this.cancelEditing();
    } catch (err) {
      this.renameError.set(describeApiError(err, 'Failed to rename chat.'));
    } finally {
      this.savingChatId.set(null);
    }
  }
}
