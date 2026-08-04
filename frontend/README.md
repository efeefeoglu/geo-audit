# Geo Audit frontend

A dependency-free frontend for the Geo Audit API.

## Local development

Start the backend on port 8000, then serve this directory on port 3000:

```bash
cd frontend
python -m http.server 3000
```

Open <http://localhost:3000>. The API base URL is configured by the
`geo-audit-api-url` meta tag in `index.html`.

## Vercel deployment

Deploy the repository root as the Vercel project root. The root-level
`vercel.json` maps `/` and the frontend's root-relative asset requests to the
static files in this directory. Without those rewrites, Vercel looks for an
`index.html` at the repository root and the homepage returns 404.
