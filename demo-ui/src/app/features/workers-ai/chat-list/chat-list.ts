import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { filter, map, startWith } from 'rxjs';

import { describeApiError } from '../../../core/api/api-error';
import { Chat, ChatProvider, ChatsStore } from '../chats.store';

// The chat id lives in the child route (`/workers-ai/:chatId`), which this
// component sits outside of — so it reads it off the URL rather than
// ActivatedRoute params.
function chatIdFromUrl(url: string): string | null {
  const [, section, chatId] = url.split('?')[0].split('/');
  return section === 'workers-ai' && chatId ? chatId : null;
}

@Component({
  selector: 'app-chat-list',
  imports: [MatButtonModule, MatFormFieldModule, MatIconModule, MatInputModule],
  templateUrl: './chat-list.html',
  styleUrl: './chat-list.scss',
})
export class ChatList {
  protected readonly store = inject(ChatsStore);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly creating = signal(false);
  protected readonly selectedProvider = signal<ChatProvider>('cloudflare');
  protected readonly editing = signal(false);
  protected readonly editingTitle = signal('');
  protected readonly saving = signal(false);
  protected readonly renameError = signal<string | null>(null);

  protected readonly currentChatId = toSignal(
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
      map((event) => chatIdFromUrl(event.urlAfterRedirects)),
      startWith(chatIdFromUrl(this.router.url)),
    ),
    { initialValue: null },
  );

  protected readonly currentChat = computed(() =>
    this.store.chats().find((chat) => chat.id === this.currentChatId()),
  );

  constructor() {
    this.route.queryParamMap.subscribe((params) => {
      const provider = params.get('provider');
      if (provider === 'cloudflare' || provider === 'groq') {
        this.selectedProvider.set(provider);
      }
    });
  }

  protected async openChat(chatId: string): Promise<void> {
    this.cancelEditing();
    if (chatId) await this.router.navigate(['/workers-ai', chatId]);
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
    this.editing.set(true);
    this.editingTitle.set(chat.title);
    this.renameError.set(null);
  }

  protected cancelEditing(): void {
    this.editing.set(false);
    this.editingTitle.set('');
    this.renameError.set(null);
  }

  protected async saveTitle(chat: Chat): Promise<void> {
    const title = this.editingTitle().trim();
    if (!title) {
      this.renameError.set('A chat name is required.');
      return;
    }

    this.saving.set(true);
    this.renameError.set(null);
    try {
      await this.store.updateTitle(chat, title);
      this.cancelEditing();
    } catch (err) {
      this.renameError.set(describeApiError(err, 'Failed to rename chat.'));
    } finally {
      this.saving.set(false);
    }
  }
}
