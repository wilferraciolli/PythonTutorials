# Angular frontend conventions (portable)

Reusable conventions extracted from this project's frontend setup, stripped
of project-specific names/paths. Copy this file into another Angular app
and adjust the concrete mixin/store names to that app's domain.

Assumes: Angular (standalone components, no NgModules), Signals API,
Vitest, Prettier, SCSS.

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
The UI follows [Material 3](https://m3.material.io) through Angular Material's
M3 theme (`mat.theme()` in `src/styles.scss`). Shared building blocks live in
`src/styles/_ui.scss` (`@use 'ui';`).

- **Tokens, not values.** Colour, type, shape and elevation come from the
  `--mat-sys-*` variables — no hex codes, no raw pixel radii
  (`--mat-sys-corner-*`), no ad hoc shadows. Depth is tonal: pick a
  `surface-container-*` role rather than adding a shadow.
- **Palette.** Generated from seed colours with
  `ng generate @angular/material:theme-color` into
  `src/styles/_theme-colors.scss` (primary petrol-teal, tertiary ochre).
  Re-run it with different seeds to re-theme; nothing else changes.
- **Light and dark** follow the system (`color-scheme: light dark`; every role
  resolves through `light-dark()`). Always use role pairs
  (`surface-container-low` + `on-surface`, `primary-container` +
  `on-primary-container`) so both themes read.
- **Roles carry meaning.** Primary is actions and selection; tertiary marks the
  AI destinations and ownership badges; error is failures and destructive
  actions (`ui.banner(error)`, `ui.danger-button`). Don't spend a role on
  decoration.
- **Type.** Use the scale — `font: var(--mat-sys-title-large)` — or the
  `ui.page-title` / `ui.section-title` / `ui.supporting-text` mixins. Roboto
  Flex is the brand face (display, headline, title); Roboto is body and label.
  Keep running text to ~65 characters (`max-width: 65ch`).
- **Layout and navigation** follow the M3 window size classes, which are the
  `bp` breakpoints (`sm` 600, `md` 840, `lg` 1200): compact windows get a modal
  navigation drawer opened from the top app bar, medium and up get a navigation
  rail. `DESTINATIONS` (`shared/destinations.ts`) is the one list both — and the
  Home tiles — read, so add a destination there. Signed-out visitors get no
  navigation, just the bar and Home.
- **Buttons.** One filled button per view. Tonal is the secondary action, text
  the tertiary. A page's create action is a FAB (`ui.fab-position`); rarely used
  actions go in an overflow menu (`more_vert`), with destructive ones in the
  error colour.
- **Lists** are one grouped `surface-container-low` surface with an
  `outline-variant` hairline between rows — not a stack of bordered cards.
  Custom interactive surfaces get `ui.state-layer` and `ui.focus-ring`.
- **Icons** are Material Symbols Outlined (every `<mat-icon>` defaults to it via
  `MAT_ICON_DEFAULT_OPTIONS`). Add `is-filled` to show a selected or active
  state (the FILL axis animates). Use the Symbols name, not the legacy
  `*_border` / `*_outline` aliases.
- **Motion** uses the `--app-ease-*` / `--app-duration-*` tokens. Route changes
  cross-fade (view transitions); the drawer and scrim slide and fade. All of it
  is switched off under `prefers-reduced-motion`.

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
- `:host`, `:host …`, bare element/attribute selectors and `@keyframes`
  are untouched — this rule is only about class names.

## Layout: mobile-first, max width, centered
This app is used from a phone as much as from a
desktop — layout is mobile-first (base styles target the smallest
viewport, wider-viewport rules layer on top via `bp.up()`, never the
reverse), and content never stretches edge-to-edge on a wide monitor.

- `styles.scss` defines `--app-page-max-width` (`1120px`) and
  `--app-gutter` (`24px`) as the one shared source of truth, plus an
  `.App-page` utility class (`max-width: var(--app-page-max-width);
  margin: 0 auto; padding: var(--app-gutter);`) and an `.App-spacer`
  utility (`flex: 1 1 auto`, for pushing a flex sibling to the far end —
  see `nav-bar.scss`'s `-actions`, though that one predates this and
  still sets `margin-inline-start: auto` directly; either is fine).
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
  `ProfilePage`/`ProfileEditPage` stay a deliberate 420px card, and
  `Home-lead` caps at `60ch` for readable line length while its ancestor
  still carries `.App-page`. The rule `.App-page` replaces is "no shared
  system behind this number," not "every page must be identical width."
- An app-shell region that's meant to span the full viewport on purpose
  (`AdminShell`'s sidebar) is not "a page" and doesn't get `.App-page` —
  only the content region next to it does.

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
- A `forms` partial (Material `mat-form-field` layout helpers —
  `forms.field-grid`, `forms.field-columns($n, $stack-below)`,
  `forms.full-row`, `forms.actions`) is part of the portable template
  this section is copied from, but only apply it in an app that actually
  uses Angular Material forms. This app hand-rolls its own form markup
  (see e.g. `doctor-form.scss`), so it isn't ported here — don't add it
  speculatively.
