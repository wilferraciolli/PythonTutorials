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

export const DESTINATIONS: readonly Destination[] = [
  {
    path: '/',
    label: 'Home',
    icon: 'home',
    title: 'Home',
    lead: '',
    tone: 'primary',
    homeCard: false,
  },
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
    path: '/tags',
    label: 'Tags',
    icon: 'sell',
    title: 'Tags',
    lead: 'See every tag and what it is attached to.',
    tone: 'primary',
    homeCard: false,
  },
  {
    path: '/workers-ai',
    label: 'AI chat',
    icon: 'smart_toy',
    title: 'AI chat',
    lead: 'Talk to Cloudflare Workers AI or Groq.',
    tone: 'tertiary',
    linkName: 'aiChats',
  },
  {
    path: '/ask',
    label: 'Ask',
    icon: 'question_answer',
    title: 'Ask your data',
    lead: 'Ask about your todos, chats, groups and posts in plain English.',
    tone: 'tertiary',
    linkName: 'aiAssistant',
  },
  {
    path: '/timeline',
    label: 'Timeline',
    icon: 'dynamic_feed',
    title: 'Timeline',
    lead: "Posts from your groups: everything, what you follow, or what's popular.",
    tone: 'primary',
    linkName: 'timelineAll',
  },
  {
    path: '/groups',
    label: 'Groups',
    icon: 'groups',
    title: 'Groups',
    lead: 'Find, create and join groups, public or private.',
    tone: 'primary',
    linkName: 'groups',
  },
  {
    path: '/admin',
    label: 'Admin',
    icon: 'admin_panel_settings',
    title: 'Admin',
    lead: 'Maintenance tools, such as recalculating post stats.',
    tone: 'primary',
    adminOnly: true,
  },
];
