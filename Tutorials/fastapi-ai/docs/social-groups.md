# Social groups (Reddit-style): design

Users create **groups** (public or private), post to them, and other people like and comment on
posts and reply to comments. Users can **be a member** of a group or just **follow** it, and each
user has a **timeline** built from the groups they can see.

> **Status:** design for review (revision 4), no code yet. Items marked **(decision)** are
> defaults I chose; change them before building.

## Roles: two different things

| Term | Where it comes from | Scope |
|---|---|---|
| **Admin** | The user's system role: `ADMIN` in the `users` / `user_roles` tables, copied from the Clerk token's `roles` claim | Whole app. **Bypasses group security** |
| **Standard user** | Same place: `STANDARD` (assigned when the Clerk `roles` array is empty or has no `ADMIN`) | Whole app |
| **Owner** | A standard user who owns a group (`groups.owner_id`) | One group |
| **Member** | A user in `group_members` | One group |
| **Follower** | A user in `group_followers` | One group |

There is **no group-level admin role**. "Admin" always means the system `ADMIN` role.

How a user's role is set (existing code, `MeService`): on `/me`, the Clerk `roles` claim is
read; if it contains `ADMIN` the user gets `ADMIN`, otherwise (including an empty array) they
get `STANDARD`.

> **Gap to fix in step 1:** today roles are copied only when the `users` row is **first
> created**. If someone is made admin in Clerk later, our row stays `STANDARD`. The plan is
> to re-sync roles from the token on every `/me` call, so Clerk stays the source of truth.

## Concepts

| Concept | Meaning |
|---|---|
| **Public group** | Anyone signed in can see it, read its posts, follow it and join it. |
| **Private group** | Only the owner, its members and admins can see it or its posts. |
| **Owner** | The creator, initially. Optional: a group keeps working if the owner is deleted. |

```mermaid
flowchart LR
    Anyone[Any signed-in user] -->|creates| G[Group]
    G -->|creator becomes| Owner[Owner + member + follower]
    Anyone -->|follows public group| F[Follower]
    Anyone -->|joins public group| M[Member + auto follower]
    Owner -->|adds people to a private group| M
    M -->|can unfollow any time| F2[Still a member, no longer follows]
    Admin[System ADMIN] -.->|sees and manages everything| G
```

## Rules

1. **Anyone can create a group** (public or private). The creator becomes the **owner**, a
   member and a follower.
2. **A group does not need an owner.** If the owner's user is deleted, `owner_id` becomes empty
   and the group carries on. Only an admin can then manage it or assign a new owner.
3. **Changing owner:** the current owner or an admin can assign a different owner.
   **(decision)** The new owner must already be a member; if not, add them first.
4. **Owners and members are auto-followed.** Becoming a member or owner creates a follower row.
   Users can unfollow at any time; unfollowing does not end membership, it only drops the group
   from their FOLLOWING timeline. Leaving a public group does not unfollow it.
5. **Private groups are invisible to outsiders.** A non-member gets `404 Group not found`
   (not 403, so its existence isn't leaked). **(decision)** Leaving or being removed from a
   private group also removes the follower row.
6. **Joining:** public groups, anyone can join. **(decision)** Private groups, the owner or an
   admin adds the member; join requests can come later.
7. **Admins bypass group security.** They can see every group, post and comment (public or
   private), post, comment and like anywhere, delete any group, post or comment and assign
   owners, all without being a member.
8. **Posts need a title and a body.** Both are required.
9. **Posts are ordered by creation date and time, newest first.**

## Who can do what

| Action | Outsider | Follower | Member | Owner | Admin |
|---|---|---|---|---|---|
| See a public group and its posts | yes | yes | yes | yes | yes |
| See a private group and its posts | no (404) | no (404) | yes | yes | **yes** |
| Follow / unfollow | follow public only | unfollow | yes | yes | yes |
| Join / leave | join public | join public | leave | leave* | n/a |
| Post, comment, reply, like | no | no | yes | yes | **yes** |
| Edit own post or comment | | | yes | yes | yes |
| Delete own post or comment | | | yes | yes | yes |
| Delete anyone's post or comment | no | no | no | yes | **yes** |
| Add / remove members | no | no | no | yes | **yes** |
| Edit group, change visibility | no | no | no | yes | **yes** |
| Assign a different owner | no | no | no | yes | **yes** |
| Delete the group | no | no | no | yes | **yes** |

\* An owner who leaves stops being owner; the group becomes ownerless. **(decision)**

Admins bypass **all** group security, including writing: they can post, comment, reply and
like in any group, public or private, without joining.

**(decision)** Admins can delete but not edit other people's posts and comments, so nobody's
words are changed under their name.

Every one of these questions is answered by **one class**, `GroupPermissions`, used by the
API, the timeline and the AI tools, so the rules can't drift apart. Its first check is always
"is the caller an admin? then allow".

## Data model

```mermaid
erDiagram
    users ||--o{ groups : "owns (optional)"
    groups ||--o{ group_members : "has"
    users ||--o{ group_members : "is member"
    groups ||--o{ group_followers : "has"
    users ||--o{ group_followers : "follows"
    groups ||--o{ posts : "contains"
    users ||--o{ posts : "writes"
    posts ||--o{ comments : "has"
    posts ||--|| post_stats : "counted in"
    comments ||--o{ comments : "replies to"
    users ||--o{ comments : "writes"
    users ||--o{ reactions : "likes"

    groups {
        text id PK
        text name "unique"
        text description
        text visibility "PUBLIC or PRIVATE"
        text owner_id "nullable, set null if the user is deleted"
        text created_by
        text created_date
    }
    group_members {
        text group_id PK
        text user_id PK
        text joined_date
    }
    group_followers {
        text group_id PK
        text user_id PK
        text created_date
    }
    posts {
        text id PK
        text group_id
        text author_id "nullable: System or deleted user"
        text title "required"
        text body "required"
        text created_date "orders every list"
        text updated_date
        text deleted_date "soft delete"
    }
    comments {
        text id PK
        text post_id
        text parent_comment_id "null means top level"
        text author_id "nullable: System or deleted user"
        text body "required"
        text created_date
        text deleted_date "soft delete"
    }
    reactions {
        text user_id PK
        text target_type PK "post or comment"
        text target_id PK
        text created_date
    }
    post_stats {
        text post_id PK
        int like_count
        int comment_count "comments and replies"
        int score "comment_count x 2 + like_count"
        text updated_date
    }
```

- **Owner** is a nullable column on the group. **Membership** has no role column. **Admin**
  comes from the existing `user_roles` table.
- **Following is its own table**, independent of membership.
- **Replies** are comments with a `parent_comment_id`. Any depth is stored; the API returns
  replies flat with their parent id and the UI indents.
- **Likes:** one row per user per target, so nobody likes twice. Like only, no downvotes.
- **`post_stats`** holds each post's counts and popularity **score**, so POPULAR doesn't have
  to count likes and comments for every post on every request:

  ```
  score = comment_count x 2 + like_count     (a comment or reply is worth 2, a like 1)
  ```

  One row per post, created with the post and updated in the same service call as the change
  that affects it: like / unlike a post, add / delete a comment or reply. Likes on comments
  don't change the post's score. Soft-deleted comments stop counting. **(decision)** A repair
  job (`POST /api/admin/post-stats/rebuild`, admin only) recomputes every row from the source
  tables, in case they ever drift.
- **Soft delete** for posts and comments so replies keep their parent ("[deleted]").
  **(decision)** Deleting a group removes its posts, comments, reactions, members and
  followers for good.
- **Indexes** for the timeline: `posts(group_id, created_date)`, `posts(created_date)`,
  `comments(post_id)`, `reactions(target_type, target_id)`, `post_stats(score)`.

## Seed data: the News group

A migration ships one group so there is something to see on a fresh database:

| Field | Value |
|---|---|
| `id` | fixed UUID, so the migration is idempotent (`INSERT OR IGNORE`) |
| `name` | `News` |
| `visibility` | `PUBLIC` |
| `owner_id` | `NULL` (only admins manage it) |
| `created_by` | `NULL` (system) |

Plus about 10 dummy posts, spread over the last few weeks so the timeline ordering is visible,
with a few comments, replies and likes so POPULAR has something to rank.

**(decision)** Seeded posts and comments have `author_id = NULL`, shown as **"System"**. Real
users may not exist yet when the migration runs, and a fake user row would show up in
`/api/users`. So `posts.author_id` and `comments.author_id` are nullable (which also covers a
deleted author). Seeded likes need real users, so they are skipped; seeded comments count
towards POPULAR instead.

Nobody is a member or follower of News on a fresh database. It still appears in `ALL` and
`POPULAR` for everyone because it is public; users can follow it to get it in `FOLLOWING`.

## Visibility: one predicate everywhere

A user can see a group when **they are an admin**, or it is `PUBLIC`, or they are its owner,
or they are a member. This one rule is applied by the group endpoints, the posts endpoints,
the timeline and the AI tools.

```mermaid
flowchart TD
    Req[Request for a group or its posts] --> A{Caller is ADMIN?}
    A -- yes --> Do[Allowed]
    A -- no --> G{Group exists?}
    G -- no --> NF[404]
    G -- yes --> V{Public?}
    V -- yes --> OK[Allowed to read]
    V -- no --> M{Owner or member?}
    M -- yes --> OK
    M -- no --> NF
    OK --> W{Write action?}
    W -- no --> Do
    W -- yes --> R{Allowed for this action?<br/>member / author / owner}
    R -- yes --> Do
    R -- no --> F[403]
```

## API

The caller is always the signed-in user. Everything about a group, its posts and their
comments is **nested under `/groups/{groupId}`**, so the group's visibility is checked on every
request, including for a single post or comment. There is no way to reach a private post
without going through its group.

### Groups

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/groups` | Groups you can see (admins: all). `?q=` searches by name, `?following=true` only those you follow, `?mine=true` only those you belong to |
| POST | `/api/groups` | Create a group (`name`, `description`, `visibility`). Caller becomes owner, member and follower |
| GET | `/api/groups/{groupId}` | One group (404 if private and you can't see it) |
| PUT | `/api/groups/{groupId}` | Edit name, description, visibility (owner or admin) |
| DELETE | `/api/groups/{groupId}` | Delete (owner or admin) |
| PUT | `/api/groups/{groupId}/owner` | Assign a different owner `{userId}` (owner or admin) |

### Members

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/groups/{groupId}/members` | Members, with who is owner |
| PUT | `/api/groups/{groupId}/members/me` | Join a public group |
| DELETE | `/api/groups/{groupId}/members/me` | Leave |
| PUT | `/api/groups/{groupId}/members/{userId}` | Add a member (owner or admin) |
| DELETE | `/api/groups/{groupId}/members/{userId}` | Remove a member (owner or admin) |

### Followers

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/groups/{groupId}/followers` | Who follows the group |
| PUT | `/api/groups/{groupId}/followers/me` | Follow (public groups, or a private group you belong to) |
| DELETE | `/api/groups/{groupId}/followers/me` | Unfollow, any time |

### Posts, comments, likes (all under the group)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/groups/{groupId}/posts` | The group's posts, newest first (`limit`) |
| POST | `/api/groups/{groupId}/posts` | Create a post; `title` and `body` required (member) |
| GET / PUT / DELETE | `/api/groups/{groupId}/posts/{postId}` | Read, edit (author), delete (author, owner, admin) |
| GET | `/api/groups/{groupId}/posts/{postId}/comments` | Comments, oldest first, with `parentCommentId` |
| POST | `/api/groups/{groupId}/posts/{postId}/comments` | Comment, or reply with `parentCommentId` (member) |
| PUT / DELETE | `/api/groups/{groupId}/posts/{postId}/comments/{commentId}` | Edit (author), delete (author, owner, admin) |
| PUT / DELETE | `.../posts/{postId}/like` and `.../comments/{commentId}/like` | Like / unlike |

### Timeline (your feed)

`GET /api/timeline/posts?type=FOLLOWING|POPULAR|ALL&limit=50`

No user id in the path: it is always about the signed-in user. `type` takes one of three
values (default `ALL`).

- **Time window: 1 year.** All three types only include posts created in the last 365 days.
- **No paging for now.** `limit` (default 50, max 100) caps the list. Paging (`offset` or a
  cursor) can be added later without changing the response shape.

| `type` | Posts returned | Order |
|---|---|---|
| `ALL` | Every post you're allowed to see from the last year (public groups, private groups you belong to; admins: everything) | Creation date and time, newest first |
| `FOLLOWING` | Posts from the last year in groups you follow (still only those you can see) | Creation date and time, newest first |
| `POPULAR` | Every post you're allowed to see from the last year | `post_stats.score` highest first (comment or reply = 2, like = 1), ties broken by newest |

```mermaid
flowchart LR
    Me[Signed-in user] --> Win["Posts from the last year"] --> Vis["Groups I can see<br/>admin: all<br/>else: public, or I am owner or member"]
    Vis --> All[ALL<br/>newest first]
    Vis --> Fol["FOLLOWING<br/>only groups I follow<br/>newest first"]
    Vis --> Pop["POPULAR<br/>score = comments x 2 + likes"]
```

`FOLLOWING` and `POPULAR` still apply the visibility rule, so a leftover follow of a private
group you were removed from can never leak its posts.

Each timeline item is a post with its group (`groupId`, `groupName`), author, `likeCount`,
`commentCount`, `likedByMe`, and links (`self`, `group`, `comments`, `like`) pointing at the
nested paths, so the UI never builds a URL. The profile links `groups`, `createGroup`,
`timelineAll`, `timelineFollowing` and `timelinePopular`.

**Links carry the permissions:** a post only gets `delete` if the caller may delete it (its
author, the group owner or an admin), a group only gets `join` if they can join it, and so on.

## How it plugs into AI search and Ask

Post titles, bodies and comments are free text, so this follows the README checklist
("Adding a new resource to AI search and Ask"): embeddings for meaning and query tools for
counts.

```mermaid
flowchart LR
    Q["'what did people say about the bike lane?'"] --> L{LLM picks tools}
    L --> T1[search_posts<br/>embeddings + keyword]
    L --> T2[count_posts / list_posts<br/>group, author, dates, popular]
    L --> T3[my_groups<br/>owner, member, following]
    T1 --> V[(resource_embeddings<br/>post, comment)]
    T2 --> DB[(posts, comments, reactions)]
    T3 --> M[(groups, members, followers)]
```

The one new thing is **whose data a tool may see**. Todos and chats are private to one user, so
a tool only needs `user_id`. Posts are shared, so every social tool applies the same
visibility predicate through `GroupPermissions` (admins see all), never through the model.
Example questions: "how many posts did I write in each group this month?", "what is my most
liked post?", "which of my groups is most active?", "posts about cycling in the groups I
follow".

## Build plan

1. **Groups, membership, owner, followers:** migrations, models, repositories, services,
   `GroupPermissions` (admin bypass first), routers, tests, profile links. Also re-sync the
   user's roles from the Clerk token on every `/me`.
2. **Posts and comments** under `/groups/{groupId}`: visibility check on every route, threaded
   replies, soft delete, permission links, tests. Seed migration for the **News** group and its
   dummy posts and comments.
3. **Likes and stats:** reactions, `post_stats` kept in step with likes and comments,
   `likedByMe`, stats rebuild endpoint.
4. **Timeline:** `ALL`, `FOLLOWING`, `POPULAR`, 1-year window, `limit`, tests for private-group
   leakage, the window and the admin bypass.
5. **AI:** embeddings for posts and comments, tools with visibility scoping, docs.
6. **Angular:** timeline page with the three tabs, groups list, group page, post page with
   threaded comments, members and follow controls.

Each step is independently shippable.

## Open questions

1. **Joining a private group.** I assumed the owner or an admin adds people. Do you want
   people to be able to request to join?
