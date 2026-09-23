import { httpResource } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { ApiClientService, SingleEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../core/api/api-error';
import { CurrentUserStore } from '../../../core/user/current-user.store';

interface AdminTool {
  id: string;
  name: string;
  description: string;
}

type AdminEnvelope = SingleEnvelope<'admin', { tools: AdminTool[] }>;

// The admin area: follows the `admin` link that only an admin's own profile
// has, and shows each tool the API lists. A tool's action is the meta link
// with the tool's id (e.g. `rebuildPostStats`), so a new admin tool on the
// API shows up here without UI changes.
@Component({
  selector: 'app-admin-page',
  imports: [MatButtonModule, MatCardModule],
  templateUrl: './admin-page.html',
  styleUrl: './admin-page.scss',
})
export class AdminPage {
  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);

  protected readonly adminLink = computed(() => this.currentUser.link('admin'));
  protected readonly profileLoaded = computed(() => !!this.currentUser.profile());

  private readonly hub = httpResource<AdminEnvelope>(() => this.api.resolve(this.adminLink()));
  protected readonly tools = computed(() => this.hub.value()?._data['admin'].tools ?? []);
  protected readonly loadError = computed(() => {
    const error = this.hub.error();
    return error ? describeApiError(error, "Couldn't load the admin area.") : null;
  });

  protected readonly running = signal<string | null>(null);
  protected readonly results = signal<Record<string, string>>({});

  protected hasAction(tool: AdminTool): boolean {
    return !!this.hub.value()?._metaLinks?.[tool.id];
  }

  protected async run(tool: AdminTool): Promise<void> {
    const url = this.api.requireLink(
      this.hub.value()?._metaLinks?.[tool.id],
      `${tool.name} isn't available.`,
    );
    this.running.set(tool.id);
    try {
      const result = await this.api.post<string, Record<string, unknown>, object>(
        tool.id === 'rebuildPostStats' ? 'postStats' : tool.id,
        url,
        {},
      );
      this.setResult(tool, `Done. ${summarise(result)}`);
    } catch (err) {
      this.setResult(tool, describeApiError(err, `${tool.name} failed.`));
    } finally {
      this.running.set(null);
    }
  }

  private setResult(tool: AdminTool, message: string): void {
    this.results.update((results) => ({ ...results, [tool.id]: message }));
  }
}

function summarise(result: Record<string, unknown> | undefined): string {
  if (!result) return '';
  if (typeof result['rebuilt'] === 'number') return `${result['rebuilt']} posts recalculated.`;
  return Object.entries(result)
    .map(([key, value]) => `${key}: ${describe(value)}`)
    .join(', ');
}

// Nested counts read as "posts 10, comments 8" rather than [object Object].
function describe(value: unknown): string {
  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, inner]) => `${key} ${String(inner)}`)
      .join(', ');
  }
  return String(value);
}
