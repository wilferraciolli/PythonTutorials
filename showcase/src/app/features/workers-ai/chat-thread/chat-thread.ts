import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { TranslocoPipe } from '@jsverse/transloco';
import { ApiClientService } from '@wiliamferraciolli/ngx-api-client';
import { marked } from 'marked';

import { ApiErrors } from '../../../core/api/api-error';
import { TranslationService } from '../../../core/i18n/translation.service';
import { Chat, ChatMessage, ChatProvider, ChatsStore } from '../chats.store';

@Component({
  selector: 'app-chat-thread',
  imports: [MatButtonModule, MatFormFieldModule, MatIconModule, MatInputModule, TranslocoPipe],
  templateUrl: './chat-thread.html',
  styleUrl: './chat-thread.scss',
})
export class ChatThread {
  // Bound from the `:chatId` route param via withComponentInputBinding()
  // (app.config.ts) — the same pattern todo-form.ts uses for `:id`.
  readonly chatId = input.required<string>();

  private readonly api = inject(ApiClientService);
  private readonly chats = inject(ChatsStore);
  private readonly apiErrors = inject(ApiErrors);
  private readonly i18n = inject(TranslationService);

  // A resource of its own, not ChatsStore state — the list only carries
  // chat summaries (no messages; see chats.store.ts/chat_service.py), so
  // opening a specific chat always needs its own GET, at the `self` link
  // the list handed out for it (no request until the list has loaded).
  private readonly detailResource = this.api.resource<'chat', Chat>('chat', () =>
    this.api.resolve(this.chats.chats().find((chat) => chat.id === this.chatId())?.links['self']),
  );

  protected readonly chat = this.detailResource.value;
  protected readonly isLoading = this.detailResource.isLoading;
  protected readonly loadErrorMessage = computed(() => {
    const error = this.detailResource.error();
    return error ? this.apiErrors.describe(error, 'chat.thread.loadFailed') : null;
  });

  protected readonly messages = computed<ChatMessage[]>(() => this.chat()?.messages ?? []);

  protected readonly draft = signal('');
  protected readonly sending = signal(false);
  protected readonly sendError = signal<string | null>(null);

  protected providerLabel(provider: ChatProvider): string {
    return this.i18n.t(`chat.providers.${provider}`);
  }

  protected renderMarkdown(content: string): string {
    return marked.parse(content, { async: false });
  }

  constructor() {
    // A different chat was opened — drop any half-typed draft/stale error
    // from the previous one instead of carrying it across.
    effect(() => {
      this.chatId();
      this.draft.set('');
      this.sendError.set(null);
    });
  }

  protected async send(): Promise<void> {
    const content = this.draft().trim();
    const chat = this.chat();
    if (!content || !chat || this.sending()) return;

    this.sending.set(true);
    this.sendError.set(null);
    try {
      const url = this.api.requireLink(chat.links['sendMessage'], this.i18n.t('chat.thread.cannotMessage'));
      await this.api.post<'chat', Chat, { content: string }>('chat', url, { content });
      this.draft.set('');
      this.detailResource.reload();
    } catch (err) {
      this.sendError.set(this.apiErrors.describe(err, 'chat.thread.sendFailed'));
    } finally {
      this.sending.set(false);
    }
  }
}
