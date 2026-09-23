import { httpResource } from '@angular/common/http';
import { Injectable, computed, inject } from '@angular/core';
import { ApiClientService, CollectionEnvelope, ILink } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../core/api/api-error';
import { environment } from '../../../environments/environment';

export type ChatMessageRole = 'user' | 'assistant';
export type ChatProvider = 'cloudflare' | 'groq';

export interface ChatMessage {
  id: string;
  chat_id: string;
  role: ChatMessageRole;
  content: string;
  created_date: string;
}

export interface Chat {
  id: string;
  user_id: string;
  title: string;
  provider: ChatProvider;
  model: string;
  created_date: string;
  updated_date: string;
  messages: ChatMessage[];
  links: Record<string, ILink>;
}

type ChatsEnvelope = CollectionEnvelope<'chats', Chat>;

// Feature-local state — a plain injectable, per docs/frontend-conventions.md.
// Provided on WorkersAiShell so its lifecycle matches the /workers-ai route
// tree, same as TodosStore/TodosShell.
//
// Talks to fastapi-cloudflare-ai, not the D1 API — its routes are the one
// backend in this app mounted under `/api` (see that project's main.py), so
// unlike tags.store.ts's hand-built `/tags` this hand-built URL needs the
// prefix. Only one Python service runs locally at a time (see
// PYTHON_APP_CONVENTIONS.md) — this feature only works while that one is
// fastapi-cloudflare-ai.
@Injectable()
export class ChatsStore {
  private readonly api = inject(ApiClientService);

  private readonly listResource = httpResource<ChatsEnvelope>(() => `${environment.apiUrl}/api/chats`);

  readonly chats = computed(() => this.listResource.value()?._data['chats'] ?? []);
  readonly isLoading = computed(() => this.listResource.isLoading());
  readonly loadError = computed(() => this.listResource.error());
  readonly loadErrorMessage = computed(() => {
    const error = this.loadError();
    return error ? describeApiError(error, "Couldn't load your chats.") : null;
  });

  private readonly createChatLink = computed<ILink | undefined>(
    () => this.listResource.value()?._metaLinks?.['createChat'],
  );

  async createChat(provider: ChatProvider): Promise<Chat> {
    const url = this.api.requireLink(this.createChatLink(), 'No create-chat link available yet — try again.');
    const chat = await this.api.post<'chat', Chat, { provider: ChatProvider }>('chat', url, { provider });
    this.listResource.reload();
    return chat;
  }

  async deleteChat(chat: Chat): Promise<void> {
    const url = this.api.requireLink(chat.links['delete'], `Not permitted to delete chat ${chat.id}`);
    await this.api.delete(url);
    this.listResource.reload();
  }

  async updateTitle(chat: Chat, title: string): Promise<Chat> {
    const url = this.api.requireLink(chat.links['updateTitle'], `Not permitted to rename chat ${chat.id}`);
    const updatedChat = await this.api.put<'chat', Chat, { title: string }>('chat', url, { title });
    this.listResource.reload();
    return updatedChat;
  }

  reloadList(): void {
    this.listResource.reload();
  }
}
