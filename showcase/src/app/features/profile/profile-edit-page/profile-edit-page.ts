import { HttpErrorResponse } from '@angular/common/http';
import { Component, effect, inject, signal } from '@angular/core';
import { FormField, FormRoot, form, required, schema } from '@angular/forms/signals';
import { Router, RouterLink } from '@angular/router';

import { I18nStore, Locale } from '../../../core/i18n/i18n.store';
import { CurrentUserStore } from '../../../core/user/current-user.store';

interface ProfileFormModel {
  name: string;
  phone: string;
  job_title: string;
}

const INITIAL_MODEL: ProfileFormModel = { name: '', phone: '', job_title: '' };

const profileSchema = schema<ProfileFormModel>((path) => {
  required(path.name);
});

@Component({
  selector: 'app-profile-edit-page',
  imports: [RouterLink, FormField, FormRoot],
  templateUrl: './profile-edit-page.html',
  styleUrl: './profile-edit-page.scss',
})
export class ProfileEditPage {
  protected readonly currentUser = inject(CurrentUserStore);
  protected readonly i18n = inject(I18nStore);
  private readonly router = inject(Router);

  protected readonly model = signal<ProfileFormModel>(INITIAL_MODEL);
  protected readonly saveError = signal<string | null>(null);
  protected readonly saving = signal(false);

  protected readonly profileForm = form(this.model, profileSchema, {
    submission: {
      action: async () => {
        this.saveError.set(null);
        this.saving.set(true);
        try {
          const value = this.model();
          await this.currentUser.updateProfile({
            name: value.name,
            phone: value.phone || undefined,
            job_title: value.job_title || undefined,
          });
          await this.router.navigate(['/profile']);
        } catch (err) {
          this.saveError.set(this.extractErrorMessage(err));
        } finally {
          this.saving.set(false);
        }
        return undefined;
      },
    },
  });

  constructor() {
    void this.currentUser.ensureLoaded();
    // One-shot sync of the async-loaded profile into the writable form
    // model — same justification as DoctorForm's constructor effect.
    effect(() => {
      const profile = this.currentUser.profile();
      if (!profile) return;
      this.model.set({
        name: profile.name,
        phone: profile.phone ?? '',
        job_title: profile.job_title ?? '',
      });
    });
  }

  protected onLanguageChange(locale: string): void {
    this.i18n.setLocale(locale as Locale);
  }

  private extractErrorMessage(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      return err.error?.detail ?? 'Failed to save profile.';
    }
    return err instanceof Error ? err.message : 'Failed to save profile.';
  }
}
