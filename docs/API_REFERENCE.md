# API Reference (Short)

Base URL: `http://localhost:8000`

- Swagger UI: `/docs`
- Health: `GET /health/`

## Endpoints

1. Upload documents

- `POST /api/upload`
- Query params: `use_default_files` (bool, default true)
- Multipart alternative: form files under key `files`
- Response: `{ session_id, summary, files }`

2. Regenerate embeddings

- `POST /api/generate-embeddings`
- Body: `{ session_id }`
- Use when you changed files or want to rebuild vectors.

3. Feasibility report

- `POST /api/feasibility`
- Body:
  - `session_id` (string, required)
  - `use_intelligent_processing` (bool, default true)
  - `development_context` (string, optional)
- Response: `{ feasibility, thinking, outputs_path }`

4. Generate plan (Reflection)

- `POST /api/generate-plan`
- Body:
  - `session_id` (string, required)
  - `use_intelligent_processing` (bool, default true)
  - `max_iterations` (int, default 5)
- Response: `{ final_plan, steps, outputs_path }`

5. Utilities

- `GET /api/document-types`
- `GET /api/sessions/{id}`
- `DELETE /api/sessions/{id}`
- `GET /api/file-content?file_path=...` (only reads from `outputs/` and `data/uploads/`)

## Minimal flow (cURL on Windows cmd)

```cmd
:: 1) Use default sample PDFs
curl -X POST "http://localhost:8000/api/upload?use_default_files=true"

:: 2) Feasibility (copy the session_id from step 1)
curl -X POST http://localhost:8000/api/feasibility ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"<SESSION_ID>\",\"use_intelligent_processing\":true}"

:: 3) Plan
del output.json 2>nul & curl -X POST http://localhost:8000/api/generate-plan ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"<SESSION_ID>\",\"use_intelligent_processing\":true,\"max_iterations\":5}"
```

Outputs saved under `outputs/`. To inspect a file via API:

```cmd
curl "http://localhost:8000/api/file-content?file_path=outputs\project_plan_<SESSION_ID>.md"
```
