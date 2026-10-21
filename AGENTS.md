
## Project rules

- Notice Saathi is a TanStack Start frontend with a FastAPI backend (`backend/`); its API contract (/analyze, /reexplain, /speak, /reminder.ics) is documented in README.md. The frontend communicates with the backend via `src/lib/api.ts` with graceful error handling and timeouts; no fake demo fallback.
- All user-facing strings live in `src/lib/strings.ts` (en + hi) behind the `t()` helper; colors/fonts are semantic tokens in `src/styles.css` (cream/green/amber/red, Baloo 2 + Mukta).
