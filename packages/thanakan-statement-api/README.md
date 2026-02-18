# thanakan-statement-api

FastAPI service for Thai bank PDF statement parsing.

## Features

- Upload PDF bank statements (KBank, BBL, SCB)
- Parse transactions with automatic bank detection
- Consolidate statements by account
- Validate balance continuity
- Export to Excel, CSV, or JSON

## Usage

```bash
# Development
mise run api

# Production
mise run api:prod
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/parse` | Upload and parse PDF statements |
| POST | `/api/v1/consolidate` | Consolidate by account |
| POST | `/api/v1/validate` | Validate balance continuity |
| POST | `/api/v1/export/excel` | Export to Excel |
| POST | `/api/v1/export/csv` | Export to CSV (zip) |
| POST | `/api/v1/export/json` | Export to JSON |
| GET | `/health` | Health check |
