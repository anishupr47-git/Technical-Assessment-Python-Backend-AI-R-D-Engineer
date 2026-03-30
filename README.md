# Unified Customer Activity Service

## What this project does
This project builds one clean backend layer on top of two different external systems.
During sync, it pulls data from both APIs, converts the data into one internal format, and stores it in a local SQLite database.
After data is stored, you can read it using simple FastAPI endpoints.
This gives one unified view of customer + support activity data instead of calling each external system directly.

Main work done in this project:
- Connect to CRM API (`/users`) to fetch customers.
- Connect to Support API (`/posts`) to fetch tickets.
- Normalize both responses into internal customer and activity models.
- Store data in SQLite using SQLAlchemy models.
- Protect against duplicates using unique constraints and create checks.
- Expose unified APIs for customers and activities.
- Support filtering on `/activities` by `source` and `type`.
- Add optional AI activity metadata (`ai_summary`, `ai_category`, `ai_priority`).
- I have also added simple comments in the code to explain what each part is doing.

### Why sync still works if AI fails or key is missing
AI is treated as an optional enrichment step, not a required step.

- If `GEMINI_API_KEY` is missing, the app uses fallback rule-based classification.
- If Gemini request fails (timeout, network, API error), the app catches the error.
- The activity is still saved without AI fields.
- This design keeps `/sync` reliable and prevents partial system failure.

## Tech stack
- FastAPI
- SQLAlchemy
- SQLite
- requests
- Pydantic
- python-dotenv

## Project files
```text
app/
  main.py
  database.py
  models.py
  schemas.py
  crud.py
  services.py
  integrations.py

requirements.txt
README.md

```

## Setup
1. Go to project folder
```bash
cd d:\Documents\Assignment-Hyperce
```

2. Create virtual environment
```bash
python -m venv .venv
```

3. Activate virtual environment
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

4. Install dependencies
```bash
pip install -r requirements.txt
```

5. Create `.env` file in project root
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

If `GEMINI_API_KEY` is empty, fallback classification is used.

## Security notes
- Do not push `.env` to GitHub or any public repo.
- Do not share API keys in screenshots, videos, or README.
- Keep secrets only in local `.env` (or secure secret manager in real projects).
- If a key is leaked, rotate the key and replace it.

## Run server
```bash
uvicorn app.main:app --reload
```

- API base URL: http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

## How to test in browser (Swagger)
Use Swagger as the main test method.

1. Open `http://127.0.0.1:8000/docs`
2. Run `POST /sync` using **Try it out** -> **Execute**
3. Run `GET /customers`
4. Run `GET /customers/{id}/activities` (example id: `1`)
5. Run `GET /activities`
6. Test filters on `GET /activities`:
- `source = support`
- `type = ticket`

## API endpoints
1. `POST /sync`
- Fetches from external APIs
- Normalizes and stores data
- Prevents duplicate inserts on repeated sync

2. `GET /customers`
- Returns all customers

3. `GET /customers/{id}/activities`
- Returns all activities for a customer

4. `GET /activities`
- Returns all activities
- Supports filters `source` and `type`

## Optional terminal testing (secondary)
```bash
curl -X POST http://127.0.0.1:8000/sync
curl http://127.0.0.1:8000/customers
curl http://127.0.0.1:8000/customers/1/activities
curl "http://127.0.0.1:8000/activities?source=support"
curl "http://127.0.0.1:8000/activities?type=ticket"
```

## Where the data comes from
Data is fetched from JSONPlaceholder mock APIs:
- `https://jsonplaceholder.typicode.com/users`
- `https://jsonplaceholder.typicode.com/posts`

Important notes:
- This is external sample/mock data, not production business data.
- This app does not randomly generate customer or ticket rows.
- Data is fetched during `POST /sync`.
- Running `/sync` many times does not create duplicates.

## Normalization rules
Customers (CRM):
- `id -> external_id`
- `name -> name`
- `email -> email`
- `source = crm`

Activities (Support):
- `id -> external_id`
- `userId -> customer_external_id`
- `type = ticket`
- `title -> title`
- `body -> content`
- `source = support`

Note: API responses expose assignment-friendly output fields.

## Error handling
- If external API call fails, error is added in sync response and app continues.
- If a row has invalid or missing required fields, that row is skipped.
- If activity cannot find matching customer, activity is skipped and counted.
- If AI fails, activity is still saved without AI metadata.

## Assumptions
These are the main assumptions made for this assignment:
- External IDs from the APIs stay stable, so we can map records safely.
- We sync CRM customers first, then support activities.
- Support `userId` matches CRM customer external id.
- Full sync is enough for this assignment (no incremental cursor needed).
- SQLite is enough for local development and demo.
- Duplicate checks should exist in both app code and database rules.
- If a row is invalid, we skip that row and continue sync.
- AI metadata is optional and should never block normal sync.
- For this source, activity `type` is always `ticket`.

## Design decisions
Main design decisions in this project:
- Keep clear file split: `integrations`, `services`, `crud`, `models`, `schemas`. These are used to make it easy for the team to understand where data comes from and how each part is working.
- Keep sync flow simple: fetch -> normalize -> validate -> save.
- Use DB unique rules on `(external_id, source)` to avoid duplicates.
- Handle errors step by step so one failure does not stop everything.
- Keep AI step optional and separate from core data save flow.
- Use simple function-based code (no heavy class setup).
- Use SQLite for quick local setup and easy review.
- Keep endpoints small, each with one clear responsibility.
- Use small type hints (example: `def root() -> dict[str, str]`) so it is easy for the team to understand what a function returns.
- Return sync counters so behavior is easy to check.

### File purpose (easy team review)
These files are split this way to make review easier and show where each task is done:
- `app/integrations.py` is used to call external APIs and normalize raw data.
- `app/services.py` is used to run sync flow and business logic.
- `app/crud.py` is used to read/write database records.
- `app/models.py` is used to define database tables.
- `app/schemas.py` is used to define API response shapes.
- `app/database.py` is used to create DB engine and session.
- `app/main.py` is used to define API routes and connect everything.

## Open-ended answers

### 1) How to scale this system for millions of activities per day?
- Move from SQLite to PostgreSQL for better production performance.
- Run sync in background workers so API requests stay fast.
- Use batch insert/upsert instead of saving one row at a time.
- Add indexes and table partitioning for faster large queries.
- Add monitoring and alerts for failures, slow jobs, and sync lag.

### 2) How to add new integrations easily?
- Keep one common internal format for customer and activity data.
- For each new source, add one fetch function and one normalize function.
- Keep mapping logic in `integrations.py`, not in route handlers.
- Reuse current CRUD save flow and duplicate checks.
- Add tests with sample payloads for each new integration.

### 3) How to handle updates/deletes in source systems?
- Use stable `external_id + source` as the main reference key.
- Use upsert logic to update existing rows when source data changes.
- Track source update time and last sync time.
- Use soft delete when source data is removed.
- Run periodic reconciliation jobs to catch data drift.

## Required env vars
- `GEMINI_API_KEY` (optional)
- `GEMINI_MODEL` (optional)

## Quick test steps
1. Start server
2. Open Swagger docs in browser
3. Run `POST /sync`
4. Run `GET /customers`
5. Run `GET /activities`
6. Run `POST /sync` again and confirm duplicates are skipped