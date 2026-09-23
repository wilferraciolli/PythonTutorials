import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { ActivatedRoute, Router, RouterLink, RouterLinkActive } from '@angular/router';

import { describeApiError } from '../../../core/api/api-error';
import { Chat, ChatProvider, ChatsStore } from '../chats.store';

@Component({
  selector: 'app-chat-list',
  imports: [RouterLink, RouterLinkActive, MatButtonModule, MatFormFieldModule, MatIconModule, MatInputModule],
  templateUrl: './chat-list.html',
  styleUrl: './chat-list.scss',
})
export class ChatList {
  protected readonly store = inject(ChatsStore);
  private readonly router = inject(Router);

  protected readonly creating = signal(false);
  protected readonly selectedProvider = signal<ChatProvider>('cloudflare');
  protected readonly editingChatId = signal<string | null>(null);
  protected readonly editingTitle = signal('');
  protected readonly savingChatId = signal<string | null>(null);
  protected readonly renameError = signal<string | null>(null);

  private readonly route = inject(ActivatedRoute);

  constructor() {
    this.route.queryParamMap.subscribe((params) => {
      const provider = params.get('provider');
      if (provider === 'cloudflare' || provider === 'groq') {
        this.selectedProvider.set(provider);
      }
    });
  }

  protected async newChat(): Promise<void> {
    if (this.creating()) return;

    this.creating.set(true);
    try {
      const chat = await this.store.createChat(this.selectedProvider());
      await this.router.navigate(['/workers-ai', chat.id]);
    } finally {
      this.creating.set(false);
    }
  }

  protected providerLabel(provider: ChatProvider): string {
    return provider === 'groq' ? 'Groq' : 'Cloudflare Workers AI';
  }

  protected async selectProvider(provider: string): Promise<void> {
    if (provider !== 'cloudflare' && provider !== 'groq') return;
    this.selectedProvider.set(provider);
    await this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { provider },
      queryParamsHandling: 'merge',
    });
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
