import { Injectable, computed, inject, signal } from '@angular/core';
import { ApiClientService } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../core/api/api-error';
import { CurrentUserStore } from '../../core/user/current-user.store';

export type AskProvider = 'groq' | 'cloudflare';

// One tool the assistant ran to answer — shown under the answer so it's
// clear where a number came from ("count_todos(overdue=true) → 2").
export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
  result: unknown;
}

export interface Answer {
  question: string;
  answer: string;
  provider: string;
  model: string;
  toolCalls: ToolCall[];
}

export interface AskEntry {
  id: number;
  question: string;
  // Exactly one of these is set once the request settles; both null while pending.
  answer: Answer | null;
  error: string | null;
}

// Feature-local state — a plain injectable, per docs/frontend-conventions.md.
// The URL is never built by hand: it is the `aiAssistant` link on the user
// profile (see current-user.store.ts), so it only exists when the running
// API is fastapi-ai.
@Injectable()
export class AskStore {
  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);

  private nextId = 1;

  readonly provider = signal<AskProvider>('groq');
  readonly entries = signal<AskEntry[]>([]);

  readonly assistantLink = computed(() => this.currentUser.link('aiAssistant'));
  readonly isPending = computed(() =>
    this.entries().some((entry) => !entry.answer && !entry.error),
  );

  async ask(question: string): Promise<void> {
    const text = question.trim();
    if (!text || this.isPending()) return;

    const id = this.nextId++;
    this.entries.update((entries) => [
      ...entries,
      { id, question: text, answer: null, error: null },
    ]);

    try {
      const url = this.api.requireLink(
        this.assistantLink(),
        'The assistant is not available on this API.',
      );
      const answer = await this.api.post<
        'answer',
        Answer,
        { question: string; provider: AskProvider }
      >('answer', url, { question: text, provider: this.provider() });
      this.settle(id, { answer });
    } catch (err) {
      this.settle(id, { error: describeApiError(err, "Couldn't get an answer.") });
    }
  }

  clear(): void {
    this.entries.set([]);
  }

  private settle(id: number, outcome: Partial<Pick<AskEntry, 'answer' | 'error'>>): void {
    this.entries.update((entries) =>
      entries.map((entry) => (entry.id === id ? { ...entry, ...outcome } : entry)),
    );
  }
}
