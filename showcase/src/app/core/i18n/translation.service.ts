import { Injectable, Signal, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { TranslocoService } from '@jsverse/transloco';
import { firstValueFrom } from 'rxjs';

// Translating from TypeScript (templates use the `transloco` pipe instead).
// Deliberately free of any app dependency, so stores can use it without a
// cycle; the user's language/locale live in I18nService.
@Injectable({ providedIn: 'root' })
export class TranslationService {
  private readonly transloco = inject(TranslocoService);

  /** The active UI language; reading it in a `computed` re-runs it on a switch. */
  readonly language: Signal<string> = toSignal(this.transloco.langChanges$, {
    initialValue: this.transloco.getActiveLang(),
  });

  /**
   * Makes `lang` the UI language. Loads its dictionary first: `translate()`
   * (unlike the template pipe) returns the raw key for a language that has
   * not been loaded yet.
   */
  async use(lang: string): Promise<void> {
    await firstValueFrom(this.transloco.load(lang));
    this.transloco.setActiveLang(lang);
  }

  /** Translates a key. Reads `language()` so a `computed` caller stays current. */
  t(key: string, params?: Record<string, unknown>): string {
    this.language();
    return this.transloco.translate(key, params);
  }

  /**
   * The label for one of the API's option values (`language`, `locale`,
   * `theme`, todo `state`). A value with no label is shown as itself, so an
   * option the API adds later still renders.
   */
  optionLabel(key: string, value: string): string {
    const fullKey = `${key}.${value}`;
    const label = this.t(fullKey);
    return label === fullKey ? value : label;
  }
}
