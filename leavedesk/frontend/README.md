# LeaveDesk frontend

React 18 + TypeScript + Vite, React Router, TanStack Query, React Hook Form + Zod. Built to `dist/`, which FastAPI serves at `/` (`app/spa.py`); the API is `/api/v1`, same origin. R31 foundation: later slices import these primitives instead of copying them.

```bash
npm ci
npm run dev        # Vite on :5173, proxies /api to :8000
npm run lint && npm run typecheck && npm test && npm run build
npm run e2e        # Playwright + axe; `--project=ui-system` checks every P1 screen at 360/1280 px in both themes with a mocked API; E2E_BASE_URL defaults to http://localhost:8000
                   # PLAYWRIGHT_CHROMIUM_PATH=/path/to/chromium uses a preinstalled browser
```

## Components (`src/components/ui`)

Styling is plain CSS: `src/styles/tokens.css` (semantic tokens, light and dark; components never use raw values), `app.css` (base, forms) and `components.css`. `node scripts/check-contrast.mjs` verifies the AA pairs in both themes.

| Component | Use |
|---|---|
| `Button`, `ButtonLink` | `primary` (one per view), `secondary`, `ghost`, `danger`; `size`, `loading`; 44 px minimum |
| `Card`, `Section`, `PageHeader` | Page structure; header has title, muted subtitle, one primary action |
| `StatusBadge` | Icon plus label for pending/approved/rejected/cancelled; never colour alone |
| `LeaveTypeTag` | Takes the API value as is; a missing type (masked Sick) renders neutral "Off" |
| `DateText`, `DaysText` | "Mon 2 Nov 2026"; days with "½" (`lib/days.ts`) |
| `DataList` | Table from 768 px, stacked list below; `compact` for the dashboard list |
| `Alert`, `EmptyState`, `Skeleton`, `Loading`, `Toast` | Feedback and loading states, announced via aria-live |
| `Field`, `TextField`, `Select`, `DateField`, `FormError`, `ErrorSummary`, `useFormFocusFirstError` | Forms (R31b-d) |
| `ConfirmDialog` | Destructive confirm: focus on "Keep", Escape keeps, focus trapped (R31e) |
| `Layout`, `HrNav`, `ThemeToggle`, `NotificationBell`, `AvatarMenu` | App shell: top tabs, bottom tab bar below 768 px |

Theme: System (default), Light or Dark, kept in `localStorage` (`lib/theme.ts`, per browser, never sent to the API). `public/theme-init.js` applies it before first paint as a same-origin script, so the CSP is unchanged.

`src/SampleForm.tsx` shows the form pieces wired together with RHF + Zod.

Other shared code: `src/lib/dates.ts` (`formatDate`, `parseDate`, `todayIso`, `COMPANY_TZ`), `src/api/client.ts` (CSRF header, 401 redirect to `/sign-in?next=...`, `safeNext`), `src/api/problem.ts` (parses the spec 6.1 envelope and `problem+json`), `src/styles/` (no inline styles, because CSP is `style-src 'self'`).

## Manual AA checklist (axe covers only part of AA; tick in each UI PR)

- [ ] Keyboard only: every action reachable, visible focus, no traps except dialogs
- [ ] Zoom to 200% and 320 px wide: no loss of content, no horizontal scroll
- [ ] Screen reader: labels, errors and the summary are announced; dialogs announce title and consequence
- [ ] Status never conveyed by colour alone (text or icon present)
- [ ] New colours checked: text 4.5:1, UI components and focus ring 3:1
- [ ] Dates shown as "Ddd D Mon YYYY" everywhere
- [ ] Failed submit keeps input and focuses the first error
- [ ] Destructive actions name the consequence and default focus to "Keep"
