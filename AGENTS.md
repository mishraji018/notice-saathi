<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Project rules

- Notice Saathi is a TanStack Start adaptation of the user's Next.js 14 spec (Next.js is not supported on this stack); its backend API contract (/analyze, /reexplain, /speak, /reminder.ics) is documented in README.md. The app stays frontend-only with a demo fallback in `src/lib/api.ts` → `src/lib/demo.ts`; do not add a backend unless the user asks.
- All user-facing strings live in `src/lib/strings.ts` (en + hi) behind the `t()` helper; colors/fonts are semantic tokens in `src/styles.css` (cream/green/amber/red, Baloo 2 + Mukta).
