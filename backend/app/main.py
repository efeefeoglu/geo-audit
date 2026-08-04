import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .auditor import run_audit
from .models import AuditRequest, AuditResponse

app = FastAPI(title="Geo Audit API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.post("/api/audit", response_model=AuditResponse, response_model_by_alias=True)
async def audit(payload: AuditRequest) -> AuditResponse:
    try:
        return await run_audit(str(payload.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (httpx.TimeoutException, RuntimeError) as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Target returned HTTP {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Unable to fetch the target website") from exc
