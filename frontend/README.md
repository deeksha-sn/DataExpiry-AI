# DATAEXPIRY frontend

React 18, TypeScript, and Vite interface for the existing DATAEXPIRY API.

## Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL Vite prints (usually `http://localhost:5173`). The UI can start without the backend, but record pages need the API at `http://localhost:8000`; Vite proxies `/api` there. Start the backend separately with `uvicorn app.main:app --reload --port 8000` from `backend`.

## Pages

- `/` — dashboard totals and visual summaries based on records returned by the API.
- `/inventory` — searchable inventory with category, sensitivity, status, expiry, mismatch, and recommendation filters.
- `/records?id=CUS-1001` — record detail lookup; the page also accepts an ID entered in its search field.
- `/expiry` — expiry, review, and completed queues. “Queue review” is a temporary browser-session UI action; it does not update the API or delete data.
- `/purpose-mismatch` — records whose API response has `purpose_mismatch: true`.
- `/ai-insights` — AI-related fields present in record API responses.

The policy and audit routes are integration placeholders; no policy engine or audit API is implemented by this frontend.

## API integration

The centralized client is `src/services/api.ts`. It consumes:

- `GET /api/health` for the connection indicator.
- `GET /api/data` with `category`, `status`, `sensitivity`, `limit`, and `offset` query parameters.
- `GET /api/data/{record_id}` for record detail lookup.
- `POST /api/data` is available in the client for record creation; the current pages do not call it.

The dashboard, inventory, expiry, purpose mismatch, and AI insight views use the existing records endpoint. The frontend has no mock record or AI result data. If the backend returns default values for optional AI fields, the UI displays those API values as received. AI and purpose-analysis endpoints can be connected when they are added by the responsible team members.

## Manual page walkthrough

With the backend and seeded database running, open each route listed above. On the inventory page, try a text search and each filter, then open a record. Verify the details page shows the API fields, including optional AI values or their unavailable messages. Check the dashboard counts against the inventory, inspect expiry and mismatch queues, and disconnect the backend to see loading/error and API connection states.
