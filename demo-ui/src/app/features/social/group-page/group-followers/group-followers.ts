import { DatePipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { Component, computed, inject, input } from '@angular/core';
import { ApiClientService, CollectionEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { Group, GroupFollower } from '../../social.models';

// Who follows the group (read-only; people follow or unfollow themselves).
@Component({
  selector: 'app-group-followers',
  imports: [DatePipe],
  templateUrl: './group-followers.html',
  styleUrl: './group-followers.scss',
})
export class GroupFollowers {
  readonly group = input.required<Group>();

  private readonly api = inject(ApiClientService);

  private readonly followersResource = httpResource<CollectionEnvelope<'followers', GroupFollower>>(
    () => this.api.resolve(this.group().links['followers']),
  );
  protected readonly followers = computed(
    () => this.followersResource.value()?._data['followers'] ?? [],
  );
}
