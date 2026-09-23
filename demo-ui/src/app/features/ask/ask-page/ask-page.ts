import { JsonPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';

import { AskProvider, AskStore } from '../ask.store';

const SUGGESTIONS = [
  'How many todos are overdue?',
  'How many todos are new?',
  'Which todo is due first?',
  'Show me where I asked about Java',
];

// "Ask your data": one question box over everything the assistant has tools
// for (todos, chat history, ...). Answers show which tools were run.
@Component({
  selector: 'app-ask-page',
  imports: [JsonPipe, MatButtonModule, MatFormFieldModule, MatIconModule, MatInputModule],
  templateUrl: './ask-page.html',
  styleUrl: './ask-page.scss',
})
export class AskPage {
  protected readonly store = inject(AskStore);

  protected readonly suggestions = SUGGESTIONS;
  protected readonly draft = signal('');

  protected async submit(question = this.draft()): Promise<void> {
    if (!question.trim() || this.store.isPending()) return;
    this.draft.set('');
    await this.store.ask(question);
  }

  protected selectProvider(value: string): void {
    if (value === 'groq' || value === 'cloudflare') this.store.provider.set(value as AskProvider);
  }
}
