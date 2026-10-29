# LeaveDesk frontend

React 18 + TypeScript + Vite, React Router, TanStack Query, React Hook Form + Zod. Built to `dist/`, which FastAPI serves at `/` (`app/spa.py`); the API is `/api/v1`, same origin. R31 foundation: later slices import these primitives instead of copying them.

```bash
npm ci
npm run dev        # Vite on :5173, proxies /api to :8000
npm run lint && npm run typecheck && npm test && npm run build
npm run e2e        # Playwright + axe at 360x640; E2E_BASE_URL defaults to http://localhost:8000
```

## Primitives (`src/ui`)

| Component | Use |
|---|---|
| `Field` | Visible label, hint and error around any control; passes `id`, `aria-invalid`, `aria-describedby` to a render prop (R31b) |
| `TextField`, `Select` | `Field` + input/select, `forwardRef` so React Hook Form `register` works |
| `DateField` | Shows and accepts "Mon 2 Nov 2026"; value in and out is ISO (R31c) |
| `FormError` | Error text with icon and hidden "Error:" prefix, so colour is never the only signal |
| `ErrorSummary` | `role="alert"` list of what to fix, each linking to its field |
| `useFormFocusFirstError(submitCount, errorCount)` | Returns the form ref; focuses the first `aria-invalid` control after a failed submit (R31d) |
| `ConfirmDialog` | Destructive confirm: states the exact consequence, focus starts on "Keep", Escape keeps, Tab trapped (R31e) |
| `Button` | 44 px minimum target; `primary`, `secondary`, `danger` |
| `Layout`, `Nav` | Skip link, landmark header/main, wrapping nav with 44 px links |
| `Toast` (`useToast`) | Persistent until dismissed; icon and text, not colour alone |

`src/SampleForm.tsx` shows the pieces wired together with RHF + Zod. Copy its shape for new forms.

Other shared code: `src/lib/dates.ts` (`formatDate`, `parseDate`, `todayIso`, `COMPANY_TZ`), `src/api/client.ts` (CSRF header, 401 redirect to `/sign-in?next=...`, `safeNext`), `src/api/problem.ts` (parses the spec 6.1 envelope and `problem+json`), `src/styles/tokens.css` (AA-checked colours; no inline styles, because CSP is `style-src 'self'`).

## Manual AA checklist (axe covers only part of AA; tick in each UI PR)

- [ ] Keyboard only: every action reachable, visible focus, no traps except dialogs
- [ ] Zoom to 200% and 320 px wide: no loss of content, no horizontal scroll
- [ ] Screen reader: labels, errors and the summary are announced; dialogs announce title and consequence
- [ ] Status never conveyed by colour alone (text or icon present)
- [ ] New colours checked: text 4.5:1, UI components and focus ring 3:1
- [ ] Dates shown as "Ddd D Mon YYYY" everywhere
- [ ] Failed submit keeps input and focuses the first error
- [ ] Destructive actions name the consequence and default focus to "Keep"
