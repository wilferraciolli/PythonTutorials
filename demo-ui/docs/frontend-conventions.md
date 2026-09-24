# Angular frontend conventions (portable)

Reusable conventions extracted from this project's frontend setup, stripped
of project-specific names/paths. Copy this file into another Angular app
and adjust the concrete mixin/store names to that app's domain.

Assumes: Angular (standalone components, no NgModules), Signals API,
Angular Material + CDK (Material 3 theme), Vitest, Prettier, SCSS.

**Starting a new app?** Read "Design system: Material 3" — it is a complete
starter kit (palette, shared partials, shell, screen recipes) that makes every
app look and behave the same.

## Design tooling: the `impeccable` skill
This repo has the `impeccable` Claude Code skill installed
(`.claude/skills/impeccable/`, by pbakaus). **After installing it into a
project for the first time, start a new Claude Code session before using
it** — a skill just added to `.claude/skills/` isn't picked up by a
session already running, since the skill list is loaded at session start.
Once in a fresh session, run `/impeccable init` first (captures durable
product context into `PRODUCT.md`) before any other command.

Reach for it for any design/UX work on the frontend rather than
freehanding it: shaping a new
screen before writing code (`shape`), reviewing what's already built
(`critique` for a UX/heuristic pass, `audit` for a11y/perf/responsive
checks), and refining it afterward (`polish`, `bolder`, `quieter`,
`distill`, `harden`, `colorize`, `layout`, `typeset`, `animate`, `delight`,
`clarify`, `adapt`, `optimize` — see the skill's own command table for the
full list and what each one is for). Invoke it as `/impeccable <command>
[target]`, or with no argument for its context-aware menu. It also owns
this project's `PRODUCT.md`/`DESIGN.md` (via its `init`/`document`
commands) — generate those from this project's own code rather than
copying another project's, since they capture *this* app's product intent
and existing visual language.

Whichever design skill you use, the "Design system: Material 3" section below is
the brief: it wins over a skill's generic aesthetic defaults.

## Core rules
- Standalone components only — no `NgModule` declarations anywhere in new
  code.
- Signals API (`signal()` / `computed()` / `linkedSignal()` / `resource()`
  / `httpResource()`) for local and feature state. Avoid `effect()` —
  prefer `computed()`, `httpResource()` and explicit event handlers;
  reserve `effect()` for genuine render/DOM-sync side effects only.
- `@ngrx/signals` (`signalStore`) is fine for cross-cutting, app-wide state
  (e.g. an `AuthStore`) — it's still signals under the hood. Avoid the
  classic RxJS-based `@ngrx/store`/`@ngrx/effects`; feature-local state
  stays plain injectable signal stores.
- RxJS interop (`toSignal()`/`toObservable()`) is fine for bridging
  Reactive Forms into signals, but signals are the default state model.
- Signals Forms (`model` / typed forms) for form handling.
- One typed API service per feature via `HttpClient`. Prefer
  `httpResource()`/`resource()` over manual `subscribe()` plumbing for
  data fetches.
- Vitest for tests. Prefer testing signal-based store behavior directly
  (it's plain TypeScript) over over-mocking component internals.
- Prettier for formatting (100 col, single quotes, Angular parser for
  `*.html` in `.prettierrc`) — run it rather than hand-formatting.
- `.editorconfig`: 2-space indent everywhere, single quotes in `*.ts`.

## Folder structure — one folder per component
Follow the Angular style guide: feature folders, but **every component
gets its own folder** holding its four files — `name.ts`, `name.html`,
`name.scss`, `name.spec.ts`. **No component — and no component
stylesheet, including a shared partial — sits directly at a
feature-folder level**; the feature shell and shared `*.scss` partials
each get their own folder too. Plain non-component classes (signal
stores, guards, resolvers) may still live at the feature root, e.g.
`some-feature/some-feature.store.ts`. Nest child components inside their
parent's folder.

```
src/app/
├── core/            # interceptors, guards, api services
├── features/
│   └── some-feature/
│       ├── some-feature-shell/            # the feature's shell component
│       │   └── some-feature-shell.{ts,html,scss,spec.ts}
│       ├── shared-partial/                # shared style partial, its own folder
│       │   └── shared-partial.scss        # → .SharedPartial-… (see SCSS naming rule)
│       ├── list-view/
│       │   ├── list-view.{ts,html,scss,spec.ts}
│       │   └── list-item/                 # child component of list-view
│       │       └── list-item.{ts,html,scss,spec.ts}
│       └── some-feature.store.ts          # signal-based state for the feature
├── shared/          # reusable UI components (same one-folder-per-component rule)
└── app.routes.ts
```

## Authentication (Clerk)
Clerk is the auth provider. One gotcha hits every new app that reaches for
`@clerk/clerk-js`'s embedded UI:

- **Never call `clerk.mountSignIn()` / `mountUserButton()` / any other
  `mount*` method.** The npm build of `@clerk/clerk-js` ships *without*
  the embedded UI components bundle (that's only available through
  Clerk's React SDK) — a `mount*` call throws `Error: Clerk was not
  loaded with Ui components` at runtime, not at build time, so it slips
  past a typecheck and a first glance. Headless/CI browsers make it
  worse: Clerk's own bot detection can withhold the UI chunk even where a
  mount call would otherwise render.
- **Use `clerk.redirectToSignIn({ redirectUrl })` instead** — a full-page
  redirect to Clerk's hosted Account Portal, then back to the app. It's
  the one sign-in entry point that doesn't depend on the missing UI
  bundle, and it behaves identically in a real browser and in Playwright.

### `AuthStore` shape
A root-provided `signalStore` (see Core rules) is the single source of
truth for "who is signed in":
- State holds the raw `user`/`session` from `Clerk['user']`/`Clerk['session']`
  — not a hand-rolled DTO. Read fields directly where needed:
  `user()?.primaryEmailAddress?.emailAddress`, `user()?.firstName`, etc.
- `isSignedIn = computed(() => session() != null)`.
- `init()` constructs `new Clerk(environment.clerkPublishableKey)`, calls
  `await instance.load()`, patches state, then `instance.addListener(...)`
  to keep it in sync going forward. Call `init()` once via
  `provideAppInitializer` in `app.config.ts` — **not** from the root
  component's constructor — so route guards and the HTTP auth
  interceptor never race a not-yet-loaded Clerk instance.
- `getToken()` returns `(await clerk?.session?.getToken()) ?? null`, for
  the HTTP interceptor to attach as `Authorization: Bearer …`.
- `signIn()` calls `redirectToSignIn({ redirectUrl: window.location.href })`.
- `signOut()` calls `clerk?.signOut()`.

### Routing
Keep at least one route public (a landing/home page) instead of gating
the whole app behind sign-in in the root component — it gives the app
something to render, and something to smoke-test the Clerk wiring
against, before backend auth even enters the picture. Gate everything
else with a `CanActivateFn` guard (`authGuard`) that checks
`auth.isSignedIn()` and redirects home otherwise. Never reach for a
mounted/embedded sign-in widget on a route — see above.

### Testing
- Component/unit tests don't need to mock Clerk specifically — `init()`
  only runs from the app-level initializer, never from a component
  constructor.
- Playwright e2e: use `@clerk/testing/playwright`. `clerkSetup()` must run
  in its own Playwright `project` (not a function-based `globalSetup` —
  this is Clerk's documented requirement) to fetch a
  `CLERK_TESTING_TOKEN`; skip this and Clerk's bot detection can produce
  the exact same "Clerk was not loaded with Ui components" error in
  headless Chromium, even with the redirect-based flow above. Sign in
  with `clerk.signIn({ page, emailAddress })` — a server-side testing
  token that bypasses password/MFA entirely — rather than driving the
  hosted sign-in form through the UI.

## Environment config
- `src/environments/environment.ts` — dev defaults (used by `ng serve` and
  any build without an explicit `production` configuration). Points
  `apiUrl` at the local backend.
- `src/environments/environment.prod.ts` — swapped in for the
  `production` build configuration via `fileReplacements` in
  `angular.json`. `apiUrl` must point at the deployed backend URL.
- Import `environment` from `../environments/environment` (relative to
  the consuming file) — never hardcode API base URLs in
  services/components.
- These files hold non-secret config only (base URLs, feature flags) — no
  API keys or credentials, since they ship in the client bundle.

## Design system: Material 3
Every app built from these conventions looks and behaves the same: the
[Material 3](https://m3.material.io) (M3) design language, implemented with
Angular Material's M3 theme, a house palette, one adaptive shell and a small set
of shared SCSS mixins. **This section is a complete starter kit** — the
guidelines, the full source of every shared partial, the shell, recipes for the
common screens, and the gotchas. Copy the files, follow the rules, and a new app
comes out consistent with no design decisions left to make.

Where this section and a generic "make it distinctive" instinct disagree, this
section wins: M3 is the brief. Spend originality on content, copy and one
memorable moment per screen, not on new colours, radii or components.

The source of truth is the working app (`src/styles.scss`, `src/styles/_ui.scss`,
`src/app/shared/…`); the code blocks below are copies, each wrapped in
`<!-- embed: path -->` markers. After changing one of those files run
`npm run docs:sync` and commit the doc with it; `npm run docs:check` fails when
the doc has drifted (run it before committing). When you copy this file into a
new app, copy `scripts/sync-conventions.mjs` and the two npm scripts with it.

### 1. The rules
1. **Tokens, never values.** Colour, type, shape, elevation and state layers come
   from the `--mat-sys-*` variables emitted by `mat.theme()`. No hex codes, no
   raw pixel radii (`--mat-sys-corner-*`), no ad hoc shadows, no `rgba()` greys.
   (Two exceptions: categorical data colours such as a tag dot, and overlays that
   sit on top of photos/video.)
2. **Roles carry meaning; use pairs.** Always pair a container with its `on-`
   colour (`surface-container-low` + `on-surface`, `primary-container` +
   `on-primary-container`). That is what makes light and dark both work. Don't
   spend a role on decoration.
3. **Depth is tonal.** Separate surfaces by picking a `surface-container-*` step,
   not by adding a shadow. Built-in shadows (FAB, menus, dialogs, the modal
   drawer at `level1`) are the only ones.
4. **One filled button per view.** Filled = the primary action; tonal = the
   secondary; text = the tertiary; outlined = a neutral alternative (rare).
   A page's *create* action is a FAB. Rarely-used actions go in an overflow menu.
5. **Lists are one grouped surface** with a hairline between rows — never a
   stack of identical bordered cards.
6. **Navigation is adaptive** (see section 4): modal drawer on compact windows,
   rail from medium up. Destinations are declared once.
7. **Mobile first, then widen.** Base styles are the phone; `bp.up()` layers on
   the rest. Content is capped at `--app-page-max-width`.
8. **Motion answers the user or marks a route change.** Nothing animates on its
   own. Everything respects `prefers-reduced-motion`.

#### Colour roles — what goes where
| Role | Use |
|---|---|
| `surface` | Page background, top app bar, rail |
| `surface-container-low` | Grouped lists, tonal panels (forms), tiles, feed cards, modal drawer |
| `surface-container` | Top app bar once scrolled; code/tool output; nested lists inside a panel |
| `surface-container-high` | The other party's chat bubble |
| `on-surface` | Primary text and icons |
| `on-surface-variant` | Secondary text, inactive icons, meta lines, supporting copy |
| `outline` | Field and chip borders, footer version marker |
| `outline-variant` | Hairlines between list rows, tab underline, dividers |
| `primary` | Filled buttons, links, the selected check, active tab indicator |
| `primary-container` / `on-primary-container` | Avatars, icon wells, the user's chat bubble |
| `secondary-container` / `on-secondary-container` | Selected nav indicator, secondary avatars |
| `tertiary-container` / `on-tertiary-container` | The one semantic accent (in this house style: AI features and "Owner" badges) |
| `error` / `error-container` / `on-error-container` | Failures, banners, overdue, destructive actions |
| `--app-chart-1` (app token, not M3) | Chart marks only: bars, lines, dots. Never text |
| `scrim` | Modal scrim at 32% |

#### Type — which token for which job
Use `font: var(--mat-sys-…)` (which sets size, weight and line-height together)
plus the matching `letter-spacing: var(--mat-sys-…-tracking)`. The mixins below
wrap the common ones.

| Job | Token |
|---|---|
| Hero headline | `headline-large` compact, `display-small` from medium up |
| Page title (`h1`) | `ui.page-title` = `headline-small` → `headline-medium` |
| Section / tile / panel title | `title-large` (`ui.section-title`); denser rows `title-medium` |
| Body text, list primary line | `body-large` (default on `body`) |
| Supporting text, list secondary line | `body-medium`, `on-surface-variant` (`ui.supporting-text`) |
| Meta, timestamps, captions | `body-small` or `label-large` at weight 400 |
| Buttons, tabs, chips, links-as-labels | `label-large` |
| Rail captions, badges | `label-medium` / `label-small` |

Brand face (Roboto Flex) is used automatically for display/headline/title; plain
face (Roboto) for body/label. Keep running text to ~65 characters
(`max-width: 65ch`), sentence case everywhere, never ALL CAPS labels.

#### Shape — which corner for which surface
| Token | px | Use |
|---|---|---|
| `corner-extra-small` | 4 | Text fields (built in), focus-ring radius, the small corner of a chat bubble |
| `corner-small` | 8 | Chips, suggestion chips, badges, small hover backgrounds |
| `corner-medium` | 12 | Banners, code blocks, the media picker, small icon wells |
| `corner-large` | 16 | Lists, tonal panels, tiles, feed cards, chat bubbles, FAB, drawer end |
| `corner-extra-large` | 28 | Dialogs (built in), large empty-state icon wells |
| `corner-full` | pill | Buttons (built in), avatars, the rail indicator, nav rows |

Prefer logical corner properties for asymmetric radii
(`border-radius: var(--mat-sys-corner-large); border-end-end-radius: var(--mat-sys-corner-extra-small);`)
— shorter than a four-value shorthand, which matters for the component style
budget (see gotchas).

#### Spacing, touch and layout
- 4px grid (`spacing.space(n)`); 8px inside a group, 16px between blocks, 24px
  between sections. Page gutter 16px on compact, 24px from medium up.
- Touch targets ≥ 48px (icon buttons are 48; list rows ≥ 56, two-line rows 72).
- Window size classes = the `bp` breakpoints: compact < `sm` (600), medium ≥ `sm`,
  expanded ≥ `md` (840), large ≥ `lg` (1200).

#### Motion
- Easing tokens: `--app-ease-standard` (on-screen movement), `--app-ease-decelerate`
  (things entering), `--app-ease-accelerate` (things leaving).
- Durations: `--app-duration-short` 200ms (state changes, exits),
  `--app-duration-medium` 300ms (entrances, the drawer).
- Route change = **fade through** (view transitions): old screen 90ms out, new one
  210ms in with a slight scale. Persistent chrome (app bar, rail) carries its own
  `view-transition-name` so only the content region moves.
- The global `prefers-reduced-motion` rule in `styles.scss` neutralises all of it.

#### Accessibility floor
- Visible keyboard focus on everything interactive: Material components draw
  their own; custom elements use `ui.focus-ring`.
- Current destination: `routerLinkActive` + `ariaCurrentWhenActive="page"`.
- Icon-only buttons need `aria-label` **and** `title`. `<mat-icon>` is
  `aria-hidden` by default — never put meaning only in an icon.
- Errors `role="alert"`; progress/results `role="status"`; live lists
  `aria-live="polite"`.
- Modal drawer: `role="dialog" aria-modal="true"`, focus trapped and restored,
  Escape closes it, scrim click closes it.
- Landmarks: `header` (app bar), `nav aria-label="Main"`, `main`, `section`
  with a heading or `aria-label`.
- Colour contrast comes free from using role pairs — another reason not to invent
  colours.

#### Copy
- Sentence case. Buttons name the action: **Save**, **New todo**, **Delete** —
  not Submit/OK. The same word runs through the flow (Delete → confirm "Delete").
- Empty states say what to do next ("No todos here yet. Use New todo to add
  one."). Errors say what happened and what to try, in the interface's voice, and
  don't apologise.
- No unnecessary eyebrow labels above headings; no `→` appended to links.

### 2. Set up a new app
1. Angular 22 app, SCSS, standalone. `npm i @angular/material @angular/cdk`.
2. In `angular.json` → `build.options`: `"stylePreprocessorOptions": { "includePaths": ["src/styles"] }`
   and `"styles": ["src/styles.scss"]`.
3. Create `src/styles/_theme-colors.scss` — paste the generated palette below, or
   regenerate it with
   `ng generate @angular/material:theme-color --primary-color="#0A7E8C" --tertiary-color="#8A6D1C" --include-high-contrast=false --directory=src/styles/ --is-scss=true`
   (mind the **trailing slash** on `--directory`: without it the file lands as
   `src/styles_theme-colors.scss`; and the schematic refuses to overwrite an
   existing file). **Keep the house seeds for a consistent family of apps;**
   change them only for a genuinely different brand.
4. Add `_breakpoints.scss`, `_spacing.scss`, `_ui.scss`, then `styles.scss`
   (all below).
5. Replace the `<head>` fonts in `src/index.html` (below).
6. Add the three providers to `app.config.ts` (below).
7. Add the shell: `shared/destinations.ts`, `shared/nav-menu`, `shared/nav-bar`,
   `shared/profile-menu`, and `app.ts/html/scss` (section 4). Replace `AppName`,
   the destination list, and — if you don't have Clerk/`CurrentUserStore` — the
   two places that read the signed-in state and the admin link.
8. Build screens from the recipes (section 5). Run the review checklist
   (section 7) before merging a screen.

### 3. Foundations — copy these files

`src/index.html` `<head>`:
```html
<meta name="viewport" content="width=device-width, initial-scale=1" />
<!-- Browser chrome follows the app's surface colour (neutral tone 98 light / 6 dark). -->
<meta name="theme-color" content="#f6fafb" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="#101415" media="(prefers-color-scheme: dark)" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<!-- Material Symbols is the M3 icon set; display=block keeps the ligature name from flashing as text. -->
<link
  href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=block"
  rel="stylesheet"
/>
<!-- M3 type: Roboto Flex for the brand roles (display, headline, title), Roboto for body and labels. -->
<link
  href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Flex:opsz,wght@8..144,400..700&display=swap"
  rel="stylesheet"
/>
```
(The `theme-color` values are neutral tone 98 / 6 of the house palette — recompute
them if you change the seeds.)

`src/app/app.config.ts` — add to `providers`:
```ts
import { MAT_ICON_DEFAULT_OPTIONS } from '@angular/material/icon';
import { provideRouter, withComponentInputBinding, withViewTransitions } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

// withViewTransitions: route changes cross-fade (M3 "fade through").
provideRouter(routes, withComponentInputBinding(), withViewTransitions()),
// Every <mat-icon> is a Material Symbols Outlined glyph.
{ provide: MAT_ICON_DEFAULT_OPTIONS, useValue: { fontSet: 'material-symbols-outlined' } },
// Material's components need an animations driver.
provideAnimationsAsync(),
```

**`src/styles/_theme-colors.scss`**

<!-- embed: src/styles/_theme-colors.scss -->
```scss
// This file was generated by running 'ng generate @angular/material:theme-color'.
// Proceed with caution if making changes to this file.

@use 'sass:map';
@use '@angular/material' as mat;

// Note: Color palettes are generated from primary: #0A7E8C, tertiary: #8A6D1C
$_palettes: (
  primary: (
    0: #000000,
    10: #001f24,
    20: #00363d,
    25: #00424a,
    30: #004f58,
    35: #005b66,
    40: #006874,
    50: #178391,
    60: #3e9dac,
    70: #5db8c7,
    80: #7ad4e3,
    90: #99f0ff,
    95: #d1f8ff,
    98: #edfcff,
    99: #f6feff,
    100: #ffffff,
  ),
  secondary: (
    0: #000000,
    10: #001f24,
    20: #14353a,
    25: #204045,
    30: #2c4c51,
    35: #38575d,
    40: #446369,
    50: #5d7c82,
    60: #76969c,
    70: #90b1b7,
    80: #abccd3,
    90: #c7e8ef,
    95: #d5f7fd,
    98: #edfcff,
    99: #f6feff,
    100: #ffffff,
  ),
  tertiary: (
    0: #000000,
    10: #251a00,
    20: #3e2e00,
    25: #4c3900,
    30: #594400,
    35: #684f00,
    40: #765b06,
    50: #917322,
    60: #ad8d3a,
    70: #c9a751,
    80: #e7c269,
    90: #ffdf96,
    95: #ffefd1,
    98: #fff8f1,
    99: #fffbff,
    100: #ffffff,
  ),
  neutral: (
    0: #000000,
    10: #181c1d,
    20: #2d3132,
    25: #383c3d,
    30: #434748,
    35: #4f5354,
    40: #5b5f60,
    50: #737879,
    60: #8d9192,
    70: #a8acad,
    80: #c3c7c8,
    90: #dfe3e4,
    95: #eef1f2,
    98: #f6fafb,
    99: #f9fdfe,
    100: #ffffff,
    4: #0a0f10,
    6: #101415,
    12: #1c2021,
    17: #262b2c,
    22: #313636,
    24: #353a3b,
    87: #d7dbdb,
    92: #e5e9e9,
    94: #ebeeef,
    96: #f1f4f5,
  ),
  neutral-variant: (
    0: #000000,
    10: #131d1f,
    20: #283234,
    25: #333d3f,
    30: #3e494b,
    35: #4a5456,
    40: #566062,
    50: #6e797b,
    60: #889395,
    70: #a2adaf,
    80: #bdc8cb,
    90: #d9e4e7,
    95: #e8f3f5,
    98: #f0fbfe,
    99: #f6feff,
    100: #ffffff,
  ),
  error: (
    0: #000000,
    10: #410002,
    20: #690005,
    25: #7e0007,
    30: #93000a,
    35: #a80710,
    40: #ba1a1a,
    50: #de3730,
    60: #ff5449,
    70: #ff897d,
    80: #ffb4ab,
    90: #ffdad6,
    95: #ffedea,
    98: #fff8f7,
    99: #fffbff,
    100: #ffffff,
  ),
);

$_rest: (
  secondary: map.get($_palettes, secondary),
  neutral: map.get($_palettes, neutral),
  neutral-variant: map.get($_palettes, neutral-variant),
  error: map.get($_palettes, error),
);

$primary-palette: map.merge(map.get($_palettes, primary), $_rest);
$tertiary-palette: map.merge(map.get($_palettes, tertiary), $_rest);
```
<!-- /embed -->

**`src/styles/_breakpoints.scss`**

<!-- embed: src/styles/_breakpoints.scss -->
```scss
// Shared breakpoint scale — Material 3's window size classes: compact is
// everything below `sm` (phones; navigation is a modal drawer), medium
// starts at `sm` (tablets; a navigation rail), expanded at `md`, large at
// `lg`. Ported from insurly-ui's src/styles/_breakpoints.scss — see
// docs/frontend-conventions.md.
@use 'sass:map';
@use 'sass:meta';

$breakpoints: (
  sm: 600px,
  md: 840px,
  lg: 1200px,
);

// Accepts a key of $breakpoints or a raw length.
@function -width($bp) {
  @if meta.type-of($bp) == 'number' {
    @return $bp;
  }
  @if not map.has-key($breakpoints, $bp) {
    @error 'Unknown breakpoint `#{$bp}`. Expected one of #{map.keys($breakpoints)} or a length.';
  }
  @return map.get($breakpoints, $bp);
}

// Viewports at least as wide as $bp.
@mixin up($bp) {
  @media (min-width: -width($bp)) {
    @content;
  }
}

// Viewports narrower than $bp.
@mixin down($bp) {
  @media (max-width: -width($bp) - 1px) {
    @content;
  }
}
```
<!-- /embed -->

**`src/styles/_spacing.scss`**

<!-- embed: src/styles/_spacing.scss -->
```scss
// Shared spacing scale. `@use 'spacing';` from any stylesheet (src/styles
// is on the Sass include path). 4px base unit — `spacing.space(2)` is 8px,
// `spacing.space(4)` is 16px, and so on — keeps paddings/gaps/margins on a
// consistent grid instead of ad hoc pixel values. Ported from insurly-ui's
// src/styles/_spacing.scss — see docs/frontend-conventions.md.
@use 'sass:math';
@use 'sass:meta';

$unit: 4px;

// Accepts a unitless multiplier (steps of $unit) or a raw length, so an
// off-scale value can still be passed through the same call site.
@function space($n) {
  @if meta.type-of($n) != 'number' {
    @error '`space()` expects a unitless multiplier or a length, got #{meta.type-of($n)}.';
  }
  @if math.is-unitless($n) {
    @return $n * $unit;
  }
  @return $n;
}

// Named responsive padding steps. Pair with `breakpoints.up(md)` /
// `breakpoints.up(lg)` to step a container's padding up as the viewport
// grows — mobile is the base value, tablet and desktop layer on top of it.
$padding-mobile: 10px;
$padding-tablet: 15px;
$padding-desktop: 20px;

// A generous, one-off spacing value for gaps/margins that want more room
// than the padding scale above (e.g. a wide gap between nav items).
$spacing-large: 30px;
```
<!-- /embed -->

**`src/styles/_ui.scss`**

<!-- embed: src/styles/_ui.scss -->
```scss
// Material 3 building blocks shared by component stylesheets. `@use 'ui';`
// from any stylesheet (src/styles is on the Sass include path) and
// `@include ui.page-title;` etc. on the component's own namespaced class —
// see docs/frontend-conventions.md, "Design system: Material 3".
//
// Everything reads --mat-sys-* tokens (colour roles, type scale, shape
// scale, elevation) emitted by `mat.theme()` in styles.scss; never a hex
// value, so light/dark and any future re-seeding come for free.
@use 'breakpoints' as bp;

// Page title: headline-small on phones, headline-medium from medium up.
@mixin page-title {
  margin: 0;
  font: var(--mat-sys-headline-small);
  letter-spacing: var(--mat-sys-headline-small-tracking);

  @include bp.up(sm) {
    font: var(--mat-sys-headline-medium);
    letter-spacing: var(--mat-sys-headline-medium-tracking);
  }
}

@mixin section-title {
  margin: 0;
  font: var(--mat-sys-title-large);
  letter-spacing: var(--mat-sys-title-large-tracking);
}

// Secondary copy: body-medium in on-surface-variant.
@mixin supporting-text {
  margin: 0;
  font: var(--mat-sys-body-medium);
  letter-spacing: var(--mat-sys-body-medium-tracking);
  color: var(--mat-sys-on-surface-variant);
}

// A page-level message: errors sit in an error-container, notices in a
// secondary-container. Same shape/padding either way so they stack neatly.
@mixin banner($tone: error) {
  margin: 0;
  padding: 12px 16px;
  border-radius: var(--mat-sys-corner-medium);
  font: var(--mat-sys-body-medium);
  letter-spacing: var(--mat-sys-body-medium-tracking);
  overflow-wrap: anywhere;

  @if $tone == error {
    background: var(--mat-sys-error-container);
    color: var(--mat-sys-on-error-container);
  } @else {
    background: var(--mat-sys-secondary-container);
    color: var(--mat-sys-on-secondary-container);
  }
}

// M3 state layer for a custom interactive surface: an overlay in the
// content colour at 8% on hover and 10% on focus/press. The element
// clips it to its own shape via `border-radius: inherit`.
@mixin state-layer($color: currentColor) {
  position: relative;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: $color;
    opacity: 0;
    pointer-events: none;
    transition: opacity var(--app-duration-short) var(--app-ease-standard);
  }

  &:hover::before {
    opacity: 0.08;
  }

  &:focus-visible::before,
  &:active::before {
    opacity: 0.1;
  }
}

// The M3 focus ring for custom interactive elements (3px secondary,
// offset 2px) — Material's own components draw theirs.
@mixin focus-ring {
  &:focus-visible {
    outline: 3px solid var(--mat-sys-secondary);
    outline-offset: 2px;
  }
}

// A floating action button parked bottom-right, above the safe area.
@mixin fab-position {
  position: fixed;
  right: max(16px, env(safe-area-inset-right));
  bottom: max(16px, env(safe-area-inset-bottom));
  z-index: 5;

  @include bp.up(sm) {
    right: 24px;
    bottom: 24px;
  }
}

// Centred icon + one line of guidance, for an empty list or pane.
@mixin empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 16px;
  text-align: center;
  font: var(--mat-sys-body-large);
  color: var(--mat-sys-on-surface-variant);
}

// An M3 *filled* icon button (primary container, on-primary glyph) — the
// Material icon button has no filled appearance, so re-token it. Use on a
// `matIconButton` for the one decisive action in a row, e.g. send.
@mixin filled-icon-button {
  --mat-icon-button-icon-color: var(--mat-sys-on-primary);
  --mat-icon-button-state-layer-color: var(--mat-sys-on-primary);
  --mat-icon-button-disabled-icon-color: color-mix(
    in srgb,
    var(--mat-sys-on-surface) 38%,
    transparent
  );
  background: var(--mat-sys-primary);

  &[disabled] {
    background: color-mix(in srgb, var(--mat-sys-on-surface) 12%, transparent);
  }
}

// Destructive actions use the error role. Material's buttons read their
// colours from component tokens, so a plain `color:` doesn't reliably
// win — set the tokens instead. `text` is for a text button (Delete,
// Remove); `filled` for the confirming button in a dialog.
@mixin danger-button($appearance: text) {
  @if $appearance == filled {
    --mat-button-filled-container-color: var(--mat-sys-error);
    --mat-button-filled-label-text-color: var(--mat-sys-on-error);
    --mat-button-filled-state-layer-color: var(--mat-sys-on-error);
    --mat-button-filled-ripple-color: color-mix(in srgb, var(--mat-sys-on-error) 12%, transparent);
  } @else {
    --mat-button-text-label-text-color: var(--mat-sys-error);
    --mat-button-text-state-layer-color: var(--mat-sys-error);
    --mat-button-text-ripple-color: color-mix(in srgb, var(--mat-sys-error) 12%, transparent);
  }
}
```
<!-- /embed -->

**`src/styles.scss`**

<!-- embed: src/styles.scss -->
```scss
// Material 3 theme. `mat.theme()` defines the --mat-sys-* CSS variables
// (colour roles, type scale, shape scale, elevation, state layers) that
// Material components read; components in this app reference those same
// tokens through the mixins in src/styles/_ui.scss instead of hardcoding
// values, so changing the palette here restyles the whole app.
//
// The palettes come from `ng generate @angular/material:theme-color`
// (src/styles/_theme-colors.scss): a petrol-teal seed (#0A7E8C) for
// primary, ochre (#8A6D1C) for tertiary. Tertiary is spent on meaning —
// the AI destinations and "owner"/highlight badges — not decoration.
// The theme type is `color-scheme`, so every role resolves through
// `light-dark()` and follows the system setting.
@use '@angular/material' as mat;
@use 'breakpoints' as bp;
@use 'theme-colors' as theme;

html {
  @include mat.theme(
    (
      color: (
        primary: theme.$primary-palette,
        tertiary: theme.$tertiary-palette,
      ),
      // M3 pairs a brand face for display/headline/title with a plain
      // face for body/label. Roboto Flex is Roboto's variable sibling —
      // its optical-size axis keeps large headlines crisp.
      typography: (
          plain-family: (
            Roboto,
            system-ui,
            sans-serif,
          ),
          brand-family: (
            'Roboto Flex',
            Roboto,
            system-ui,
            sans-serif,
          ),
        ),
      density: 0,
    )
  );
  color-scheme: light dark;
  -webkit-text-size-adjust: 100%;
}

:root {
  // Shared page-layout constants — see `.App-page` below and
  // docs/frontend-conventions.md's "Layout: mobile-first, max width,
  // centered" section. Content never stretches edge-to-edge on a wide
  // monitor; the footer and page content line up on the same gutter
  // instead of each picking its own number. M3 margins: 16 on compact
  // windows, 24 from medium up.
  --app-page-max-width: 900px;
  // The whole shell (app bar contents, rail and page) sits in one centred
  // column no wider than this, so on a big monitor the menu and the account
  // button don't drift to opposite edges of the screen. Backgrounds still
  // run edge to edge.
  --app-shell-max-width: 1280px;
  --app-gutter: 16px;
  --app-bar-height: 64px;
  --app-rail-width: 80px;

  // M3 motion: emphasized easing for things that move on screen, plus
  // the two durations most transitions use.
  --app-ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --app-ease-decelerate: cubic-bezier(0.05, 0.7, 0.1, 1);
  --app-ease-accelerate: cubic-bezier(0.3, 0, 0.8, 0.15);
  --app-duration-short: 200ms;
  --app-duration-medium: 300ms;

  // Chart marks. M3's tonal steps are too muted for a data mark (they read
  // grey next to the grid), so charts get one validated teal per mode, near
  // the brand seed: >= 3:1 on surface-container-low, in the lightness band,
  // above the chroma floor (dataviz validator). Text never wears it.
  --app-chart-1: light-dark(#00897b, #12a3a8);

  @include bp.up(sm) {
    --app-gutter: 24px;
  }
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100dvh;
  font: var(--mat-sys-body-large);
  letter-spacing: var(--mat-sys-body-large-tracking);
  color: var(--mat-sys-on-surface);
  background: var(--mat-sys-surface);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a {
  color: var(--mat-sys-primary);
}

// Material Symbols Outlined (loaded in index.html) is the app's icon font:
// `MAT_ICON_DEFAULT_OPTIONS` in app.config.ts points every <mat-icon> at
// this class. The FILL axis is how M3 marks a selected state — add
// `is-filled` to swap outlined for filled, and it animates.
.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
  font-variation-settings:
    'FILL' 0,
    'wght' 400,
    'GRAD' 0,
    'opsz' 24;
  transition: font-variation-settings var(--app-duration-short) var(--app-ease-standard);

  &.is-filled {
    font-variation-settings:
      'FILL' 1,
      'wght' 400,
      'GRAD' 0,
      'opsz' 24;
  }
}

// Shared page-layout helpers. Apply `.App-page` to a route's top-level
// container alongside its own component class (`<div class="TodosList
// App-page">`) instead of that component defining its own
// `max-width`/`margin: 0 auto`/`padding` — one shared constant beats a
// different ad hoc pixel value per page.
.App-page {
  max-width: var(--app-page-max-width);
  margin: 0 auto;
  padding: var(--app-gutter);
}

.App-spacer {
  flex: 1 1 auto;
}

// Screen-reader-only text.
.App-visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

// Route changes cross-fade through the M3 "fade through" pattern: the old
// screen leaves quickly, the new one settles in with a slight scale. The
// app bar and rail carry their own `view-transition-name`, so only the
// content region moves.
@keyframes app-fade-out {
  to {
    opacity: 0;
  }
}

@keyframes app-fade-in {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
}

::view-transition-old(root) {
  animation: 90ms var(--app-ease-accelerate) both app-fade-out;
}

::view-transition-new(root) {
  animation: 210ms var(--app-ease-decelerate) 90ms both app-fade-in;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  ::view-transition-group(*),
  ::view-transition-old(*),
  ::view-transition-new(*) {
    animation: none !important;
  }
}
```
<!-- /embed -->


What the `_ui` mixins are for:

| Mixin | Use |
|---|---|
| `ui.page-title` | The `h1` of a page (responsive headline) |
| `ui.section-title` | A panel, tile or section heading (`title-large`) |
| `ui.supporting-text` | Secondary copy: `body-medium` in `on-surface-variant` |
| `ui.banner(error \| info)` | A page-level message in an error/secondary container; put it on the component's own `-error` class and set `role="alert"` in the template |
| `ui.state-layer($color)` | Hover 8% / focus-press 10% overlay for a custom interactive surface (list row, tile, chip) |
| `ui.focus-ring` | 3px secondary outline, 2px offset, for custom interactive elements |
| `ui.fab-position` | Fixed bottom-right, above the safe area (pair with `<a matFab extended>`) |
| `ui.empty-state` | Centred icon + one line of guidance for an empty list or pane |
| `ui.filled-icon-button` | Re-tokens a `matIconButton` as an M3 *filled* icon button (send, etc.) |
| `ui.danger-button` / `ui.danger-button(filled)` | Error-role text button (Delete, Remove) / filled confirming button in a dialog |

Include them on the component's **own namespaced class**
(`&-title { @include ui.page-title; }`) — never `@extend`, never a global class.
Global helpers in `styles.scss` stay `.App-…`.

### 4. The adaptive shell
Signed-in users get **destinations as a navigation rail** on medium windows and up
(≥ 600px) and as a **modal navigation drawer**, opened from the top app bar, on
compact ones. Signed-out visitors have nowhere to go, so they get just the bar
(with Sign in) and the public home page. The bar sits on `surface` and takes a
`surface-container` tint once the page scrolls. The rail sits *under* the bar and
sticks; the drawer slides in over a 32% scrim with a focus trap.

Destinations are declared **once** and read by the rail, the drawer and the Home
tiles — add a destination here and it appears everywhere. The Home tile for a
destination whose API link is missing shows "Not found" instead of a dead link.

**`src/app/shared/destinations.ts`** — the shape, then an example list (declare your own):

<!-- embed: src/app/shared/destinations.ts until="export const DESTINATIONS" -->
```ts
// The app's top-level destinations, in navigation order. NavMenu (rail and
// drawer) and the Home cards both read this list, so a destination is
// named, iconed and worded once.
export interface Destination {
  path: string;
  /** Short name in the navigation. */
  label: string;
  icon: string;
  /** Heading on the Home card. */
  title: string;
  /** One line on the Home card saying what the destination is for. */
  lead: string;
  /** Tertiary marks the AI destinations; everything else is primary. */
  tone: 'primary' | 'tertiary';
  /**
   * The link name on the user profile that must exist for the destination
   * to work (see CurrentUserStore.link); omit for Home, which needs none.
   */
  linkName?: string;
  /** Only shown to callers whose profile carries the `admin` link. */
  adminOnly?: boolean;
  /** Left off the Home cards (it is the page they sit on). */
  homeCard?: false;
}
```
<!-- /embed -->

```ts
export const DESTINATIONS: readonly Destination[] = [
  { path: '/', label: 'Home', icon: 'home', title: 'Home', lead: '', tone: 'primary', homeCard: false },
  {
    path: '/todos',
    label: 'Todos',
    icon: 'checklist',
    title: 'Todos',
    lead: 'Create, update and tag your todos.',
    tone: 'primary',
    linkName: 'todos',
  },
  {
    path: '/ask',
    label: 'Ask',
    icon: 'question_answer',
    title: 'Ask your data',
    lead: 'Ask about your todos and chats in plain English.',
    tone: 'tertiary',
    linkName: 'aiAssistant',
  },
  {
    path: '/admin',
    label: 'Admin',
    icon: 'admin_panel_settings',
    title: 'Admin',
    lead: 'Maintenance tools.',
    tone: 'primary',
    adminOnly: true,
  },
];
```

**`src/app/shared/nav-menu/nav-menu.ts`**

<!-- embed: src/app/shared/nav-menu/nav-menu.ts -->
```ts
import { Component, computed, inject, input, output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { CurrentUserStore } from '../../core/user/current-user.store';
import { DESTINATIONS } from '../destinations';

// The app's destinations as a Material 3 navigation rail (icon over label,
// for medium windows and up) or as the rows of a navigation drawer (icon
// beside label, inside the modal drawer on compact windows). Same list,
// same active state; the shell decides which shape to mount.
@Component({
  selector: 'app-nav-menu',
  imports: [RouterLink, RouterLinkActive, MatIconModule],
  templateUrl: './nav-menu.html',
  styleUrl: './nav-menu.scss',
})
export class NavMenu {
  readonly variant = input<'rail' | 'drawer'>('rail');
  /** Emits after a destination is chosen, so a modal drawer can close. */
  readonly navigated = output<void>();

  private readonly currentUser = inject(CurrentUserStore);

  protected readonly destinations = computed(() =>
    DESTINATIONS.filter(
      (destination) => !destination.adminOnly || !!this.currentUser.link('admin'),
    ),
  );
}
```
<!-- /embed -->

**`src/app/shared/nav-menu/nav-menu.html`**

<!-- embed: src/app/shared/nav-menu/nav-menu.html -->
```html
<nav
  class="NavMenu"
  [class.is-rail]="variant() === 'rail'"
  [class.is-drawer]="variant() === 'drawer'"
  aria-label="Main"
>
  @for (destination of destinations(); track destination.path) {
    <a
      class="NavMenu-item"
      [routerLink]="destination.path"
      routerLinkActive="is-active"
      ariaCurrentWhenActive="page"
      [routerLinkActiveOptions]="{ exact: destination.path === '/' }"
      (click)="navigated.emit()"
    >
      <span class="NavMenu-indicator">
        <mat-icon class="NavMenu-icon">{{ destination.icon }}</mat-icon>
      </span>
      <span class="NavMenu-label">{{ destination.label }}</span>
    </a>
  }
</nav>
```
<!-- /embed -->

**`src/app/shared/nav-menu/nav-menu.scss`**

<!-- embed: src/app/shared/nav-menu/nav-menu.scss -->
```scss
// Material 3 navigation, in two shapes that share one list:
//   .is-rail   — 56x32 active pill with the label beneath (medium windows up)
//   .is-drawer — full-width 56px rows, icon beside label (modal drawer)
// The selected destination gets a secondary-container indicator and a
// filled icon; the rest sit in on-surface-variant.
.NavMenu {
  display: flex;
  flex-direction: column;

  &.is-rail {
    gap: 12px;
    padding: 12px 0 24px;
  }

  &.is-drawer {
    padding: 0 12px 12px;
  }

  &-item {
    display: flex;
    text-decoration: none;
    color: var(--mat-sys-on-surface-variant);
    outline: none;
    -webkit-tap-highlight-color: transparent;

    &.is-active {
      color: var(--mat-sys-on-surface);
    }
  }

  &-indicator {
    position: relative;
    display: grid;
    place-items: center;
    transition: background-color var(--app-duration-short) var(--app-ease-standard);

    &::before {
      content: '';
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: var(--mat-sys-on-surface);
      opacity: 0;
      pointer-events: none;
      transition: opacity var(--app-duration-short) var(--app-ease-standard);
    }
  }

  &-label {
    min-width: 0;
  }
}

// The state layer sits on the whole row's hit area, so hovering the label
// lights the indicator too.
.NavMenu-item:hover .NavMenu-indicator::before {
  opacity: 0.08;
}

.NavMenu-item:focus-visible .NavMenu-indicator::before,
.NavMenu-item:active .NavMenu-indicator::before {
  opacity: 0.1;
}

.NavMenu-item:focus-visible .NavMenu-indicator {
  outline: 3px solid var(--mat-sys-secondary);
  outline-offset: 2px;
}

.NavMenu-item.is-active .NavMenu-indicator {
  background: var(--mat-sys-secondary-container);
  color: var(--mat-sys-on-secondary-container);
}

.NavMenu-item.is-active .NavMenu-icon {
  font-variation-settings:
    'FILL' 1,
    'wght' 400,
    'GRAD' 0,
    'opsz' 24;
}

// Rail: icon pill over a label-medium caption (bold when selected).
.NavMenu.is-rail .NavMenu-item {
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font: var(--mat-sys-label-medium);
  letter-spacing: var(--mat-sys-label-medium-tracking);
}

.NavMenu.is-rail .NavMenu-item.is-active {
  font-weight: 700;
}

.NavMenu.is-rail .NavMenu-indicator {
  width: 56px;
  height: 32px;
  border-radius: var(--mat-sys-corner-full);
}

.NavMenu.is-rail .NavMenu-label {
  text-align: center;
}

// Drawer: the row itself is the indicator, so the pill background moves
// from the icon wrapper up to the row.
.NavMenu.is-drawer .NavMenu-item {
  flex-direction: row;
  align-items: center;
  gap: 12px;
  height: 56px;
  padding: 0 16px;
  border-radius: var(--mat-sys-corner-full);
  font: var(--mat-sys-label-large);
  letter-spacing: var(--mat-sys-label-large-tracking);
  background: transparent;
  transition: background-color var(--app-duration-short) var(--app-ease-standard);
}

.NavMenu.is-drawer .NavMenu-item.is-active {
  background: var(--mat-sys-secondary-container);
  color: var(--mat-sys-on-secondary-container);
}

.NavMenu.is-drawer .NavMenu-item:hover {
  background: color-mix(in srgb, var(--mat-sys-on-surface) 8%, transparent);
}

.NavMenu.is-drawer .NavMenu-item.is-active:hover {
  background: color-mix(
    in srgb,
    var(--mat-sys-on-secondary-container) 8%,
    var(--mat-sys-secondary-container)
  );
}

.NavMenu.is-drawer .NavMenu-item:focus-visible {
  outline: 3px solid var(--mat-sys-secondary);
  outline-offset: 2px;
}

.NavMenu.is-drawer .NavMenu-indicator,
.NavMenu.is-drawer .NavMenu-item.is-active .NavMenu-indicator {
  background: transparent;
  color: inherit;
}

.NavMenu.is-drawer .NavMenu-indicator::before {
  display: none;
}

.NavMenu.is-drawer .NavMenu-item:focus-visible .NavMenu-indicator {
  outline: none;
}
```
<!-- /embed -->

**`src/app/shared/nav-bar/nav-bar.ts`**

<!-- embed: src/app/shared/nav-bar/nav-bar.ts -->
```ts
import { Component, inject, input, output, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { ProfileMenu } from '../profile-menu/profile-menu';

// App-wide top app bar, mounted once in app.html — the one place a
// signed-out visitor finds "Sign in" and a signed-in one finds the account
// menu, instead of every page rolling its own header. Destinations live in
// the navigation rail / drawer (NavMenu); on compact windows this bar
// carries the button that opens the drawer.
@Component({
  selector: 'app-nav-bar',
  imports: [RouterLink, MatButtonModule, MatIconModule, ProfileMenu],
  templateUrl: './nav-bar.html',
  styleUrl: './nav-bar.scss',
  host: { '(window:scroll)': 'onScroll()' },
})
export class NavBar {
  protected readonly auth = inject(AuthStore);

  /** Show the navigation-drawer button (signed in, compact window). */
  readonly showMenuButton = input(false);
  readonly menuRequested = output<void>();

  // M3 top app bars sit on the page surface and pick up a tonal container
  // once content scrolls beneath them.
  protected readonly scrolled = signal(false);

  protected onScroll(): void {
    this.scrolled.set(window.scrollY > 0);
  }

  protected signIn(): void {
    void this.auth.signIn();
  }
}
```
<!-- /embed -->

**`src/app/shared/nav-bar/nav-bar.html`**

<!-- embed: src/app/shared/nav-bar/nav-bar.html -->
```html
<header class="NavBar" [class.is-scrolled]="scrolled()">
  <div class="NavBar-inner">
    @if (showMenuButton()) {
      <button
        matIconButton
        type="button"
        class="NavBar-menu"
        aria-label="Open navigation menu"
        (click)="menuRequested.emit()"
      >
        <mat-icon>menu</mat-icon>
      </button>
    }

    <a class="NavBar-brand" routerLink="/">AppName</a>
    <span class="App-spacer"></span>

    @if (auth.isSignedIn()) {
      <app-profile-menu />
    } @else {
      <button matButton="tonal" type="button" (click)="signIn()">Sign in</button>
    }
  </div>
</header>
```
<!-- /embed -->

**`src/app/shared/nav-bar/nav-bar.scss`**

<!-- embed: src/app/shared/nav-bar/nav-bar.scss -->
```scss
@use 'ui';

// The host is what sticks: a sticky element only stays put inside its
// parent's box, and a sticky <header> inside a host of its own height would
// scroll away with the page.
:host {
  position: sticky;
  top: 0;
  z-index: 10;
  display: block;
}

// Small top app bar: 64px, on the page surface, tonal once scrolled. The
// surface spans the window; its contents line up with the shell column.
.NavBar {
  height: var(--app-bar-height);
  background: var(--mat-sys-surface);
  color: var(--mat-sys-on-surface);
  view-transition-name: app-bar;
  transition: background-color var(--app-duration-short) var(--app-ease-standard);

  &.is-scrolled {
    background: var(--mat-sys-surface-container);
  }

  &-inner {
    display: flex;
    align-items: center;
    gap: 8px;
    height: 100%;
    max-width: var(--app-shell-max-width);
    margin: 0 auto;
    padding: 0 16px 0 var(--app-gutter);
  }

  // The drawer button takes the place of the left gutter's first 8px.
  &-menu {
    margin-left: -12px;
  }

  &-brand {
    color: var(--mat-sys-on-surface);
    text-decoration: none;
    font: var(--mat-sys-title-large);
    letter-spacing: var(--mat-sys-title-large-tracking);
    padding: 4px 8px;
    margin-left: -8px;
    border-radius: var(--mat-sys-corner-small);

    @include ui.focus-ring;
  }
}
```
<!-- /embed -->

**`src/app/shared/profile-menu/profile-menu.ts`**

<!-- embed: src/app/shared/profile-menu/profile-menu.ts -->
```ts
import { Component, computed, inject } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { CurrentUserStore } from '../../core/user/current-user.store';

// Only mounted by NavBar once `auth.isSignedIn()` is true — this component
// doesn't need its own signed-out branch. Just the account's own actions:
// the app's destinations live in the navigation rail / drawer.
@Component({
  selector: 'app-profile-menu',
  imports: [RouterLink, MatIconModule, MatMenuModule],
  templateUrl: './profile-menu.html',
  styleUrl: './profile-menu.scss',
})
export class ProfileMenu {
  protected readonly auth = inject(AuthStore);
  protected readonly currentUser = inject(CurrentUserStore);

  // The avatar shows the first letter of the profile name; until /me has
  // loaded it falls back to a generic account icon.
  protected readonly initial = computed(() => this.currentUser.me()?.name?.trim().charAt(0) ?? '');

  protected async signOut(): Promise<void> {
    await this.auth.signOut();
  }
}
```
<!-- /embed -->

**`src/app/shared/profile-menu/profile-menu.html`**

<!-- embed: src/app/shared/profile-menu/profile-menu.html -->
```html
<button
  class="ProfileMenu-trigger"
  type="button"
  [matMenuTriggerFor]="menu"
  aria-label="Account menu"
  aria-haspopup="menu"
  title="Account menu"
>
  @if (initial(); as letter) {
    <span class="ProfileMenu-avatar" aria-hidden="true">{{ letter }}</span>
  } @else {
    <mat-icon class="ProfileMenu-avatar-icon">account_circle</mat-icon>
  }
</button>

<mat-menu #menu="matMenu" xPosition="before">
  @if (currentUser.me(); as me) {
    <div class="ProfileMenu-header">
      <span class="ProfileMenu-name">{{ me.name }}</span>
      @if (me.email) {
        <span class="ProfileMenu-email">{{ me.email }}</span>
      }
    </div>
  }
  <a mat-menu-item routerLink="/profile">
    <mat-icon>person</mat-icon>
    <span>Profile</span>
  </a>
  <button mat-menu-item type="button" (click)="signOut()">
    <mat-icon>logout</mat-icon>
    <span>Sign out</span>
  </button>
</mat-menu>
```
<!-- /embed -->

**`src/app/shared/profile-menu/profile-menu.scss`**

<!-- embed: src/app/shared/profile-menu/profile-menu.scss -->
```scss
@use 'ui';

// The account button is an avatar: the user's initial on a
// primary-container disc, 40px (48px touch target via the padding).
.ProfileMenu {
  &-trigger {
    display: grid;
    place-items: center;
    width: 48px;
    height: 48px;
    padding: 0;
    border: 0;
    border-radius: var(--mat-sys-corner-full);
    background: transparent;
    color: var(--mat-sys-on-surface-variant);
    cursor: pointer;

    @include ui.state-layer(var(--mat-sys-on-surface));
    @include ui.focus-ring;
  }

  &-avatar {
    display: grid;
    place-items: center;
    width: 40px;
    height: 40px;
    border-radius: var(--mat-sys-corner-full);
    background: var(--mat-sys-primary-container);
    color: var(--mat-sys-on-primary-container);
    font: var(--mat-sys-title-medium);
    text-transform: uppercase;
  }

  &-avatar-icon {
    width: 40px;
    height: 40px;
    font-size: 40px;
  }

  // Who is signed in, at the top of the menu: not a menu item, so it
  // doesn't take part in keyboard navigation.
  &-header {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 12px 16px;
    margin-bottom: 4px;
    border-bottom: 1px solid var(--mat-sys-outline-variant);
    min-width: 12rem;
  }

  &-name {
    font: var(--mat-sys-title-small);
    letter-spacing: var(--mat-sys-title-small-tracking);
    color: var(--mat-sys-on-surface);
  }

  &-email {
    font: var(--mat-sys-body-small);
    letter-spacing: var(--mat-sys-body-small-tracking);
    color: var(--mat-sys-on-surface-variant);
    overflow-wrap: anywhere;
  }
}
```
<!-- /embed -->

**`src/app/app.ts`**

<!-- embed: src/app/app.ts -->
```ts
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { A11yModule } from '@angular/cdk/a11y';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterOutlet } from '@angular/router';
import { map } from 'rxjs';

import { environment } from '../environments/environment';
import { AuthStore } from './core/auth/auth.store';
import { NavBar } from './shared/nav-bar/nav-bar';
import { NavMenu } from './shared/nav-menu/nav-menu';

// The Material 3 adaptive shell. Signed-in visitors get destinations as a
// navigation rail on medium windows and up (>= 600px) and as a modal
// navigation drawer, opened from the top app bar, on compact ones. A
// signed-out visitor has nowhere to navigate to, so the shell is just the
// bar and the page.
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, A11yModule, NavBar, NavMenu],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly version = environment.version;
  protected readonly auth = inject(AuthStore);

  // Breakpoints.XSmall is (max-width: 599.98px) — the M3 compact window class.
  protected readonly compact = toSignal(
    inject(BreakpointObserver)
      .observe(Breakpoints.XSmall)
      .pipe(map((state) => state.matches)),
    { requireSync: true },
  );

  protected readonly showRail = computed(() => this.auth.isSignedIn() && !this.compact());
  protected readonly showMenuButton = computed(() => this.auth.isSignedIn() && this.compact());

  protected readonly menuOpen = signal(false);

  protected openMenu(): void {
    this.menuOpen.set(true);
  }

  protected closeMenu(): void {
    this.menuOpen.set(false);
  }
}
```
<!-- /embed -->

**`src/app/app.html`**

<!-- embed: src/app/app.html -->
```html
<div class="AppShell">
  <app-nav-bar [showMenuButton]="showMenuButton()" (menuRequested)="openMenu()" />

  <div class="AppShell-body">
    @if (showRail()) {
      <aside class="AppShell-rail">
        <app-nav-menu variant="rail" />
      </aside>
    }

    <div class="AppShell-main">
      <router-outlet />
      <footer class="AppShell-footer">v{{ version }}</footer>
    </div>
  </div>

  @if (showMenuButton() && menuOpen()) {
    <div
      class="AppShell-scrim"
      aria-hidden="true"
      animate.enter="AppShell-scrim-enter"
      animate.leave="AppShell-scrim-leave"
      (click)="closeMenu()"
    ></div>
    <aside
      class="AppShell-drawer"
      role="dialog"
      aria-modal="true"
      aria-label="Navigation"
      cdkTrapFocus
      [cdkTrapFocusAutoCapture]="true"
      animate.enter="AppShell-drawer-enter"
      animate.leave="AppShell-drawer-leave"
      (keydown.escape)="closeMenu()"
    >
      <p class="AppShell-drawer-title">AppName</p>
      <app-nav-menu variant="drawer" (navigated)="closeMenu()" />
    </aside>
  }
</div>
```
<!-- /embed -->

**`src/app/app.scss`**

<!-- embed: src/app/app.scss -->
```scss
// Bar on top; below it the navigation rail (medium windows up) beside the
// routed page. The page column stretches so a page's own empty space sits
// above the footer, not below it.
.AppShell {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;

  // The rail and the page share one centred column (--app-shell-max-width).
  &-body {
    flex: 1 1 auto;
    display: flex;
    width: 100%;
    max-width: var(--app-shell-max-width);
    min-width: 0;
    margin: 0 auto;
  }

  // Sticks under the app bar and scrolls on its own if the window is short.
  &-rail {
    position: sticky;
    top: var(--app-bar-height);
    align-self: flex-start;
    flex: none;
    width: var(--app-rail-width);
    height: calc(100dvh - var(--app-bar-height));
    overflow-y: auto;
    background: var(--mat-sys-surface);
    view-transition-name: app-rail;
  }

  &-main {
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    flex-direction: column;
  }

  // Discrete build-version marker — useful for confirming which deploy is
  // live without giving an otherwise chrome-less app a header just for it.
  &-footer {
    margin-top: auto;
    padding: 12px var(--app-gutter);
    font: var(--mat-sys-label-small);
    letter-spacing: var(--mat-sys-label-small-tracking);
    color: var(--mat-sys-outline);
    text-align: left;
  }

  // Modal navigation drawer (compact windows): a scrim over the page and a
  // surface-container-low panel sliding in from the start edge.
  &-scrim {
    position: fixed;
    inset: 0;
    z-index: 20;
    background: color-mix(in srgb, var(--mat-sys-scrim) 32%, transparent);
  }

  &-drawer {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 21;
    display: flex;
    flex-direction: column;
    width: min(360px, calc(100vw - 56px));
    overflow-y: auto;
    background: var(--mat-sys-surface-container-low);
    color: var(--mat-sys-on-surface);
    border-radius: 0 var(--mat-sys-corner-large) var(--mat-sys-corner-large) 0;
    box-shadow: var(--mat-sys-level1);
    overscroll-behavior: contain;
  }

  &-drawer-title {
    margin: 0;
    padding: 20px 28px 12px;
    font: var(--mat-sys-title-large);
    letter-spacing: var(--mat-sys-title-large-tracking);
    color: var(--mat-sys-on-surface-variant);
  }

  &-scrim-enter {
    animation: app-scrim-in var(--app-duration-medium) var(--app-ease-standard);
  }

  &-scrim-leave {
    animation: app-scrim-out var(--app-duration-short) var(--app-ease-standard) forwards;
  }

  &-drawer-enter {
    animation: app-drawer-in var(--app-duration-medium) var(--app-ease-decelerate);
  }

  &-drawer-leave {
    animation: app-drawer-out var(--app-duration-short) var(--app-ease-accelerate) forwards;
  }
}

@keyframes app-scrim-in {
  from {
    opacity: 0;
  }
}

@keyframes app-scrim-out {
  to {
    opacity: 0;
  }
}

@keyframes app-drawer-in {
  from {
    transform: translateX(-100%);
  }
}

@keyframes app-drawer-out {
  to {
    transform: translateX(-100%);
  }
}
```
<!-- /embed -->


Shell notes:
- `NavMenu` reads `CurrentUserStore.link('admin')` for `adminOnly` destinations and
  `App` reads `AuthStore.isSignedIn()`. Swap those two reads for your app's
  role/auth check; nothing else in the shell knows about them.
- The footer is a discreet build-version marker (`environment.version`); drop it
  if you don't want one.
- The `AppShell-*` and `NavMenu-*` state classes (`is-active`, `is-rail`,
  `is-drawer`) follow the naming rule above; the compound selectors are top-level
  blocks with the full class name.

### 5. Screen recipes
Each recipe is the M3 answer to a recurring need. Class names are examples — use
your component's own namespace.

**Page skeleton.** A route's top-level element carries `.App-page` beside its own
class; the title is the page's only `h1`.
```html
<div class="TodosList App-page">
  <header class="TodosList-header">
    <h1 class="TodosList-title">My todos</h1>
  </header>
  <!-- filter, list, empty/error states -->
  <a matFab extended class="TodosList-fab" routerLink="/todos/new">
    <mat-icon>add</mat-icon>
    New todo
  </a>
</div>
```
```scss
@use 'ui';
.TodosList {
  display: flex; flex-direction: column; align-items: flex-start; gap: 16px;
  &-title { @include ui.page-title; }
  &-fab { @include ui.fab-position; }
}
```

**Grouped list** (todos, groups, members, admin tools, tags). One surface, hairlines
between rows, a 72px two-line row, leading control/avatar, trailing actions.
Leave clearance for the FAB (`margin-bottom: 72px`) on FAB pages.
```scss
&-items {
  align-self: stretch; margin: 0 0 72px; padding: 0; list-style: none;
  border-radius: var(--mat-sys-corner-large);
  background: var(--mat-sys-surface-container-low);
  overflow: hidden;
}
&-item {
  display: flex; align-items: center; gap: 4px; min-height: 72px; padding: 8px 8px 8px 4px;
  & + & { border-top: 1px solid var(--mat-sys-outline-variant); }
}
```
A row that is itself a link uses `@include ui.state-layer(var(--mat-sys-on-surface));`
plus a focus outline with a negative offset (`outline-offset: -3px`) so it isn't
clipped by the list's `overflow: hidden`. A list of *actionable state* (todos)
uses a leading toggle icon button (`radio_button_unchecked` → `check_circle` with
`is-filled`), strikes the title through and dims the row when done, and shows an
overdue due-date in `error`.

**Avatar.** A 40px disc with the initial: `display: grid; place-items: center;
width: 40px; height: 40px; border-radius: var(--mat-sys-corner-full);
background: var(--mat-sys-primary-container); color: var(--mat-sys-on-primary-container);
font: var(--mat-sys-title-medium); text-transform: uppercase;`. Use
`secondary-container` for a person inside another entity's list (members).

**Tonal panel for a short form** (create group, add tag, post composer). Not a
card, not a dialog — an inline panel that opens above the list.
```scss
&-form {
  padding: 16px;
  border-radius: var(--mat-sys-corner-large);
  background: var(--mat-sys-surface-container-low);
}
```
Fields are `mat-form-field appearance="outline" subscriptSizing="dynamic"`; native
selects use `matNativeControl`. Actions right-aligned: text **Cancel**, filled
**Save**.

**Empty state.** `@include ui.empty-state;` with a 48px primary icon, a
`title-large` heading and one `body-medium` line saying what to do next. Keep the
class name your spec looks for (`.TodosList-empty`).

**Error / notice banner.**
```scss
&-error { @include ui.banner(error); }   // <p class="X-error" role="alert">…</p>
```

**Filter → segmented button; sections → tabs.** A handful of exclusive filters
(`All / New / Active / Closed`) is a `mat-button-toggle-group` (M3 segmented
button; shows a check on the selected one). Switching *sections of one page*
(Posts / Members / Followers) is M3 primary tabs:
```html
<nav mat-tab-nav-bar aria-label="Sections" [tabPanel]="panel">
  <a mat-tab-link [active]="section() === 'posts'" (click)="section.set('posts')">Posts</a>
  <a mat-tab-link [active]="section() === 'members'" (click)="section.set('members')">Members (24)</a>
</nav>
<mat-tab-nav-panel #panel> <!-- the section's content --> </mat-tab-nav-panel>
```

**Overflow menu** for rarely-used and destructive actions, beside at most one
primary and one secondary visible button:
```html
<button matIconButton type="button" aria-label="More group actions" title="More" [matMenuTriggerFor]="more">
  <mat-icon>more_vert</mat-icon>
</button>
<mat-menu #more="matMenu" xPosition="before">
  <button mat-menu-item type="button" (click)="edit()"><mat-icon>edit</mat-icon><span>Edit group</span></button>
  <button mat-menu-item type="button" class="X-danger" (click)="remove()"><mat-icon>delete</mat-icon><span>Delete group</span></button>
</mat-menu>
```
```scss
&-danger { --mat-menu-item-label-text-color: var(--mat-sys-error); --mat-menu-item-icon-color: var(--mat-sys-error); }
```

**Confirmation dialog.** `MatDialog` + a shared `ConfirmDialog`. A destructive
confirm button gets `ui.danger-button(filled)`; the cancel is a text button. Title
and confirm label use the same verb (Delete todo → **Delete**).

**Home tile** (a destination on the landing page). A whole-surface link, one
`title-large` line and one supporting line; icon in a 48px `primary-container`
well (`tertiary-container` for the accent role). Compact: a row (icon beside
text, `display: grid; grid-template-columns: auto 1fr`); from `sm`: a tall column
tile. Unavailable destinations render the same shape without the link and with
the error colour.

**Chat / composer.** Bubbles: the user's in `primary-container` (right), the
other party's in `surface-container-high` (left); large corners with one
`extra-small` corner on the speaker's side. Composer: outlined field + a filled
icon button (`ui.filled-icon-button`, `aria-label="Send message"`), pinned at the
bottom of the thread (`position: sticky; bottom: 0` on a page that scrolls, or a
fixed-height shell whose message list scrolls). Suggestion chips: 32px, 1px
`outline`, `corner-small`, `label-large`, `ui.state-layer`.

**Content card** (a feed post; anything whose item has a title, a description
and maybe media). An M3 filled card: `surface-container-low`, `corner-large`,
padding 16 (20/24 from `sm`). Top to bottom: a **byline** (40px avatar, author in
`title-small`, then context and a relative time in `body-small`), the **title** in
`title-large` (an `h2`), the **description** in `body-medium`
`on-surface-variant` clamped to three lines, **media** full-width at 16:9
(`object-fit: cover`, `corner-medium`), then a row of text-button **actions**.
The whole card opens the item: the title link carries a stretched `::after`
(`position: absolute; inset: 0`), the card tints on
`:has(.X-title:hover)` and shows the focus ring on `:has(.X-title:focus-visible)`,
and everything else interactive inside (links in the byline, the action row's
buttons, media players, credit links) is `position: relative; z-index: 1` so it
stays its own target. Don't nest interactive elements inside the title link.
The detail page uses the same surface for the item itself, with its discussion
below it. Times read relative (`relativeTime` pipe: "5 hours ago", "yesterday",
then "Sep 12") inside `<time datetime>` with the full timestamp in `title`.
A toggle button with `aria-pressed` keeps a stable name ("Like (12)"), never
one that flips between Like and Unlike.

**Insights / charts** (the admin engagement page is the reference). Decide the
form before the colour: a handful of headline numbers is a **KPI row** of stat
tiles (label, value in `headline-medium`, a delta "vs previous N days" with a
`trending_up/down/flat` icon — direction is never colour alone); change over time
is a **column chart per metric**. Measures on different scales (likes vs groups)
get **small multiples**, never two y-axes. A single series has no legend — its
title names it. Marks: columns ≤ 24px wide with a 2px gap, 4px rounded top and
square at the baseline, hairline `outline-variant` grid with clean ticks
(1/2/5×10ⁿ), the peak labelled and nothing else, text in text tokens. Marks wear
`--app-chart-1` (M3 tonal steps read grey as data marks; this token was run
through a palette validator for contrast ≥ 3:1, lightness band and chroma in both
modes — re-validate if you change it). Every chart is interactive: hover and
arrow keys show a tooltip (value first, date second) and it has an `aria-label`
summary; every number is also in a table view (`<details>` "Daily numbers").
Filters (a period segmented button) sit in one row above everything they scope;
switching keeps the previous numbers on screen dimmed until the new ones arrive
(`linkedSignal` over the resource). Lay out in real pixels (measure the width
with a `ResizeObserver`, guarded for tests/SSR) so text and corners stay crisp.

**Expandable detail** (`<details>`): a 32px `label-large` summary with a chevron
icon that rotates 180° when open; the revealed block on `surface-container`,
`corner-medium`.

**Hero** (public landing only): `headline-large` → `display-small`, left-aligned,
max ~20ch, one supporting line at `max-width: 52ch`, one filled button. Nothing
else competes with it.

### 6. Gotchas (each one cost time)
- **`matIconButton` has no filled appearance** — use `ui.filled-icon-button`.
  `matButton` does: `"filled" | "tonal" | "outlined" | "elevated"` (text is the
  default).
- **Button colours come from component tokens.** A plain `color: var(--mat-sys-error)`
  on a `matButton` doesn't reliably win — set the tokens (`ui.danger-button`).
  Menu items likewise: `--mat-menu-item-label-text-color` / `-icon-color`.
- **`mat-card appearance="filled"`** defaults to `surface-container-highest`;
  override `--mat-card-filled-container-color` to `surface-container-low` to match
  lists and panels.
- **`mat-tab-nav-bar` requires `[tabPanel]`** (a `mat-tab-nav-panel`). `mat-tab-link`
  on an `<a>` without `href` works: Enter/Space trigger the click.
- **A routed component's host element is the flex item**, not the root `div` inside
  it. If its content must scroll inside a fixed-height shell, give the host
  `:host { display: flex; flex-direction: column; flex: 1 1 auto; min-height: 0; }`
  or the inner `flex`/`min-height: 0` never applies and the page overflows.
- **`white-space: pre-wrap` shows the template's leading space.** For user text use
  `pre-line`, or keep the interpolation tight (`<p>{{ text }}</p>`).
- **Component style budget** (4 kB warning per stylesheet): prefer logical corner
  properties over four-value `border-radius`, delete dead rules, and lean on the
  shared mixins instead of repeating long declarations.
- **Icons:** use Material Symbols names — never the legacy `favorite_border` /
  `chat_bubble_outline` aliases; show a filled state with `is-filled`. The font
  link needs `display=block`.
- **`animate.enter` / `animate.leave`** (Angular's CSS animation hooks) drive the
  drawer and scrim; the classes must run `@keyframes`. Use `@if` for the element so
  `cdkTrapFocus` + `[cdkTrapFocusAutoCapture]="true"` capture on open and restore
  focus on close.
- **`view-transition-name` on persistent chrome** (app bar, rail) or the whole page
  cross-fades including them.
- **Unit tests run without `matchMedia`**, so `BreakpointObserver` never reports
  compact: a signed-in `App` test gets the rail. Stub the auth store with a
  provider (`{ provide: AuthStore, useValue: { isSignedIn: () => true } }`);
  `patchState` isn't available on a signalStore's public type.
- **A failed `httpResource` throws from `value()`.** Any `computed()` that reads
  `resource.value()` blows up once the request fails, so the page sticks on
  "Loading…" instead of showing its error. Read through a guard —
  `data = computed(() => (res.hasValue() ? res.value() : undefined))` — and derive
  everything else from `data()`. Test it: flush a 500 and assert the store reads
  empty with an error message.
- **Put `position: sticky` on the component's host, not an element inside it.**
  A sticky element only stays put within its parent's box; a sticky `<header>`
  inside an `<app-nav-bar>` host of the same height scrolls away with the page.
  `:host { position: sticky; top: 0; display: block; }`. Verify it by scrolling
  and checking the element's `getBoundingClientRect().top` is still 0 — a colour
  check alone won't catch it.
- **Screenshot full pages at the height you need.** A Playwright `fullPage`
  capture of a page taller than the viewport resizes the viewport mid-capture;
  anything laid out from a `ResizeObserver` (charts) can be caught half
  re-rendered — blank or stretched — even though the app is fine. Use a viewport
  tall enough for the page, or `clip`.
- **Keep the class names your specs query** (`.TodosList-empty`, `.TodoForm-title`,
  `mat-button-toggle button`) when restyling.
- **Tests that stub a store's `me()`**: `Object.defineProperty(store, 'me', { value: () => … })`
  works because `me` is a class field.

### 7. Verifying and reviewing a screen
Before merging a screen, check it at **390px and 1280px, light and dark**.
Because most screens sit behind sign-in, verify visually with a throwaway harness
rather than by hand: a scratch copy of the app (outside the repo) whose `AuthStore`
is replaced by a stub that reports "signed in", `environment.apiUrl = ''`, and
Playwright `page.route('**/api/**', …)` returning fixture envelopes; take
screenshots at both widths and in both colour schemes
(`browser.newContext({ colorScheme: 'dark', viewport: … })`). Also script the
behavioural checks screenshots can't show: drawer focus trap / Escape / focus
restore, rail active state and `aria-current`, resize across 600px, no console
errors with view transitions on.

Review checklist:
- [ ] Only `--mat-sys-*` tokens and `--app-*` variables; no hex, no raw radii, no shadows.
- [ ] Every container has its `on-` pair; reads in dark.
- [ ] One filled button; create action is a FAB; rare actions in an overflow menu.
- [ ] Lists are grouped surfaces with hairlines; rows ≥ 56px; touch targets ≥ 48px.
- [ ] `h1` present once; landmarks and labels correct; icon-only buttons labelled.
- [ ] Visible focus on custom interactive elements (`ui.focus-ring` / `ui.state-layer`).
- [ ] Error `role="alert"`, results `role="status"`; empty and loading states written.
- [ ] Mobile-first (`bp.up`), no horizontal scroll at 390px, content capped on wide screens —
      check at 1920px and 2560px too, not just 1280px.
- [ ] Motion only in response to the user or a route change; reduced motion respected.
- [ ] Copy: sentence case, action verbs, same word through the flow.
- [ ] Error state checked by failing the request (500), not only the happy path.
- [ ] Production build shows no new budget warnings; Prettier clean on touched files.
- [ ] `npm run docs:check` passes.

## Component SCSS class naming
Every class in a component stylesheet is namespaced with the component's
class name (PascalCase, exactly as it appears in the `.ts`), then a
single **flat, kebab-case suffix**. No BEM `__` / `--`, no SMACSS-style
nesting past one level. Example — component class `UserDashboard`, in
`user-dashboard.scss`:
`.UserDashboard { &-container {} &-header {} &-section-header {} &-section-header-label {} }`.

- **One** root `.ComponentName { }` block. Inside it, `&-…` selectors go
  two levels deep at most:
  1. the flat, kebab-case suffix (`&-container`, `&-rows`);
  2. one nested selector on *that* element for its own state or
     pseudo-class/element — `&:hover`, `&.is-active`,
     `&.is-active::after`, `&:hover, &.is-open`.
  A trailing pseudo-class or child/descendant combinator written
  directly on the level-1 selector (`&-edit:hover`, `&-rows > div`,
  `&-rows dd`) still counts as level 1, not a nested rule.
  **Never nest a third level of `&`.**
- Prefer giving an element **its own** `is-*` state class over reaching
  across to a relative's — bind it in the template alongside whatever
  else already drives the state (e.g. a chevron that flips with its
  button's menu: `[class.is-open]="trigger.menuOpen"` on the `<svg>`
  itself, not just the `<button>`). That keeps the selector a plain
  level-2 compound (`&.is-open`) and the CSS doesn't need to know the
  parent's markup. Reach for a **descendant** selector — the other side
  spelled out as a full class name rather than `&`, e.g. inside
  `&-chevron { }`: `.ComponentName-toggle.is-open & { }` — only when you
  don't control the other element's template (a third-party
  component-library host class, say).
- Anything that would need a third level, or a compound/descendant
  selector that doesn't fit the level-2 shapes above (a library class on
  an unrelated element, say), goes in a **separate top-level block with
  the full class name** instead —
  `.ComponentName-count-toggle.mat-button-toggle-group { }` — never a
  deeper nested `&`. Rationale: every selector for a component still
  greps by the component name and sorts together, and a flat block can
  be moved or renamed without untangling nested `&`.
- **Responsive overrides are mobile-first and stay inside the `&-…`
  block they affect** — never collected into a separate `@media` section
  elsewhere in the file. Base declarations in the block target the
  smallest viewport; `@include bp.up($breakpoint) { … }` (see shared
  mixins below) layers on wider-viewport overrides right next to the
  property they change, e.g.
  `&-container { padding-left: 10px; @include bp.up(md) { padding-left: 20px; } }`.
  This is a mixin call, not a selector nesting level, so it doesn't count
  toward the two-levels-deep limit above.
- Flatten former BEM parts straight into the suffix: `.stat__value` →
  `.ComponentName-stat-value`; `.board-state--error` →
  `.ComponentName-board-state-error`; camelCase → kebab-case
  (`errorDot` → `error-dot`).
- Exception — dynamic **state classes** stay unprefixed and shared:
  `is-active`, `is-open`, `is-done`, `is-current`, `is-locked`. They only
  appear in a compound/descendant selector against a namespaced class
  (`.SomeFeature-ledger-link.is-current`) and are toggled with
  `[class.is-current]` in the template.
- Shared style partials that aren't one component still take a single
  namespace: `account-shared.scss` → `.AccountPanel-…`,
  `steps/step-form.scss` → `.StepForm-…`, `admin-form.scss` →
  `.AdminForm-…`. Global helpers in `styles.scss` use `.App-…`
  (`.App-page`, `.App-spacer`).
- Shared mixins (`@include ui.page-title;`) are included on the component's
  **own** namespaced class — never `@extend`, never a global class.
- `:host`, `:host …`, bare element/attribute selectors and `@keyframes`
  are untouched — this rule is only about class names. (A routed component
  that must fill or scroll inside a shell needs a `:host { display: flex; … }`
  rule: its host element, not its root `div`, is the layout item.)

## Layout: mobile-first, max width, centered
This app is used from a phone as much as from a
desktop — layout is mobile-first (base styles target the smallest
viewport, wider-viewport rules layer on top via `bp.up()`, never the
reverse), and content never stretches edge-to-edge on a wide monitor.

- **Two widths, two jobs.** `--app-shell-max-width` (`1280px`) caps the whole
  shell — the app bar's contents, the navigation rail and the page column sit
  in one centred column, so on a 24" or 27" monitor the menu and the account
  button don't end up at opposite edges of the screen. Surfaces (the app bar's
  background) still run edge to edge; only their contents are capped.
  `--app-page-max-width` caps a page's content inside that column.
- `styles.scss` defines `--app-page-max-width` (`900px`) and
  `--app-gutter` (`16px` on compact windows, `24px` from `sm` up — M3's
  margins) as the one shared source of truth, plus an
  `.App-page` utility class (`max-width: var(--app-page-max-width);
  margin: 0 auto; padding: var(--app-gutter);`) and an `.App-spacer`
  utility (`flex: 1 1 auto`, for pushing a flex sibling to the far end —
  the app bar uses it to park the account button at the end).
- Apply `.App-page` to a route's top-level container **alongside** its
  own component class (`<div class="TodosShell App-page">`) instead of
  that component defining its own `max-width`/`margin: 0 auto`/`padding`.
  One shared constant beats a different ad hoc pixel value per page
  (pages used to hand-roll their own 1000px, 900px, 700px, … before this existed).
- Nested routes only need `.App-page` once, on the shared ancestor — e.g.
  a feature shell carries it, so the routed pages underneath it don't need
  their own.
- A page that's intentionally narrower than the app-wide width for its
  own reason (a compact profile card, a reading-width paragraph) keeps
  its own bespoke constraint instead of fighting `.App-page` — e.g.
  `ProfilePage` stays a deliberate 34rem column, and
  `Home-lead` caps at `60ch` for readable line length while its ancestor
  still carries `.App-page`. The rule `.App-page` replaces is "no shared
  system behind this number," not "every page must be identical width."
- An app-shell region that's meant to span the full viewport on purpose
  (the navigation rail, the app bar) is not "a page" and doesn't get
  `.App-page` — only the content region next to it does.
- A page that must fill the viewport (a chat) sizes itself from the shell's
  variables — `height: calc(100dvh - var(--app-bar-height) - 44px)` (44px is the
  footer) — and gives its routed component's host `display: flex` so the message
  list can scroll inside it.

## Shared SCSS mixins
Keep shared SCSS mixins in `src/styles/`, wired onto the Sass include
path via `stylePreprocessorOptions.includePaths: ["src/styles"]` in
`angular.json`'s `build.options` (needed once per app — without it,
`@use 'breakpoints' as bp;` from a component stylesheet won't resolve).
That import style — `@use 'breakpoints' as bp;` / `@use 'spacing';` —
works from any stylesheet once wired. Adjust the specific values below
per app.

- `breakpoints` (`sm: 600px`, `md: 840px`, `lg: 1200px` — the M3 window size
  classes) exposes
  `bp.up($bp)` (min-width — the one to reach for, since layout is
  mobile-first) and `bp.down($bp)` (max-width, for the rare case a style
  needs to be capped instead of grown). Both accept a scale key or a raw
  length (`bp.up(700px)` when a one-off value doesn't match the named
  scale — don't force it onto the nearest key just to use a name).
  Replaces every raw `@media (min-width: …)` in component SCSS.
- `spacing` exposes `spacing.space($n)` — a 4px-unit multiplier
  (`spacing.space(2)` = 8px, `spacing.space(4)` = 16px) for paddings,
  margins and gaps instead of ad hoc pixel values.
- `ui` — the Material 3 building blocks (page/section titles, supporting text,
  banner, state layer, focus ring, FAB position, empty state, filled icon button,
  danger button). Full source and usage in "Design system: Material 3" above;
  `@use 'ui';` then `@include ui.page-title;` on the component's own class.
- `theme-colors` — the generated M3 tonal palettes, `@use`d only by
  `styles.scss`.
- A `forms` partial (Material `mat-form-field` layout helpers —
  `forms.field-grid`, `forms.field-columns($n, $stack-below)`,
  `forms.full-row`, `forms.actions`) is part of the portable template
  this section is copied from, but only apply it in an app that actually
  uses Angular Material forms. This app hand-rolls its own form markup
  (see e.g. `doctor-form.scss`), so it isn't ported here — don't add it
  speculatively.
