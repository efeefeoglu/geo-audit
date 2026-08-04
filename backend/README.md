# Geo Audit API

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

Send `POST /api/audit` with `{"url":"https://example.com"}`. Interactive API documentation is available at `/docs`.

Configuration uses environment variables prefixed with `GEO_AUDIT_`, including
`GEO_AUDIT_REQUEST_TIMEOUT_SECONDS`, `GEO_AUDIT_BROWSER_TIMEOUT_MS`, and
`GEO_AUDIT_MAX_RESPONSE_BYTES`.

## Container

```bash
docker build -t geo-audit-api .
docker run --rm -p 8000:8000 geo-audit-api
```
