import { Component, inject, signal } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { firstValueFrom } from 'rxjs';

import { CurrentUserStore } from '../../../../core/user/current-user.store';
import { ConfirmDialog } from '../../../../shared/confirm-dialog/confirm-dialog';
import { AdminUser, UsersManagementStore } from '../users-management.store';

@Component({
  selector: 'app-users-list',
  providers: [UsersManagementStore],
  templateUrl: './users-list.html',
  styleUrl: './users-list.scss',
})
export class UsersList {
  protected readonly store = inject(UsersManagementStore);
  private readonly currentUser = inject(CurrentUserStore);
  private readonly dialog = inject(MatDialog);

  protected readonly ownId = this.currentUser.profile()?.id ?? null;
  protected readonly actionError = signal<string | null>(null);
  protected readonly pendingId = signal<string | null>(null);

  protected async onToggleRole(user: AdminUser): Promise<void> {
    const grant = user.role !== 'admin';
    const dialogRef = this.dialog.open(ConfirmDialog, {
      data: {
        title: grant ? 'Grant admin access' : 'Remove admin access',
        message: grant
          ? `Give ${user.name} full admin access to manage wards, doctors, procedures, and other users?`
          : `Remove ${user.name}'s admin access? They'll go back to a standard user.`,
        confirmLabel: grant ? 'Grant admin access' : 'Remove admin access',
        tone: grant ? 'primary' : 'danger',
      },
    });
    const confirmed = await firstValueFrom(dialogRef.afterClosed());
    if (!confirmed) {
      return;
    }

    this.actionError.set(null);
    this.pendingId.set(user.id);
    try {
      await this.store.setRole(user, grant ? 'admin' : 'user');
    } catch {
      this.actionError.set(`Couldn't update ${user.name}'s role — check the API is reachable.`);
    } finally {
      this.pendingId.set(null);
    }
  }
}
