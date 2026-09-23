import { httpResource } from '@angular/common/http';
import { Injectable, computed, inject } from '@angular/core';
import { ApiClientService, CollectionEnvelope, ILink } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../core/api/api-error';
import { CurrentUserStore } from '../../core/user/current-user.store';

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
// Talks to whichever AI project is running (fastapi-cloudflare-ai,
// fastapi-groq-ai or fastapi-ai — only one runs locally at a time, see
// PYTHON_APP_CONVENTIONS.md). The chats URL is never built by hand: it is
// the chats link on the user profile (`/users/{id}/chats`), which each
// project names after itself (CHATS_LINK_NAMES).
const CHATS_LINK_NAMES = ['aiChats', 'cloudflareChats', 'groqChats'];
@Injectable()
export class ChatsStore {
  private readonly api = inject(ApiClientService);

  private readonly currentUser = inject(CurrentUserStore);

  private readonly chatsLink = computed<ILink | undefined>(() =>
    CHATS_LINK_NAMES.map((name) => this.currentUser.link(name)).find((link) => !!link),
  );

  private readonly listResource = httpResource<ChatsEnvelope>(() => this.api.resolve(this.chatsLink()));

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
