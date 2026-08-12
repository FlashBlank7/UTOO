import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
from app.api.v1 import auth, posts, comments, admin, agent, reports, schools, boards, moderator_applications, management
from app.core.config import settings

app = FastAPI(title="UTOO", version="0.1.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"
LILIES_FRONTEND_URL = os.getenv("LILIES_FRONTEND_URL", "http://127.0.0.1:3000").rstrip("/")
PROXY_HOP_BY_HOP_HEADERS = {
    b"connection",
    b"keep-alive",
    b"proxy-authenticate",
    b"proxy-authorization",
    b"te",
    b"trailer",
    b"transfer-encoding",
    b"upgrade",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["comments"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(schools.router, prefix="/api/v1/schools", tags=["schools"])
app.include_router(boards.router, prefix="/api/v1/boards", tags=["boards"])
app.include_router(moderator_applications.router, prefix="/api/v1/moderator-applications", tags=["moderator-applications"])
app.include_router(management.router, prefix="/api/v1/management", tags=["management"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.api_route(
    "/lilies",
    methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@app.api_route(
    "/lilies/{full_path:path}",
    methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@app.api_route(
    "/api/platform",
    methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@app.api_route(
    "/api/platform/{full_path:path}",
    methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def serve_lilies(request: Request, full_path: str = ""):
    """Expose the Lilies standalone server through UTOO's single public port."""

    public_path = request.url.path
    upstream_path = f"/lilies{public_path}" if public_path.startswith("/api/platform") else public_path
    target = f"{LILIES_FRONTEND_URL}{upstream_path}"
    if request.url.query:
        target = f"{target}?{request.url.query}"

    request_headers = [
        (name, value)
        for name, value in request.headers.raw
        if name.lower() not in PROXY_HOP_BY_HOP_HEADERS and name.lower() != b"host"
    ]
    client = httpx.AsyncClient(timeout=None, follow_redirects=False)
    try:
        upstream_request = client.build_request(
            request.method,
            target,
            headers=request_headers,
            content=await request.body(),
        )
        upstream = await client.send(upstream_request, stream=True)
    except httpx.HTTPError as exc:
        await client.aclose()
        raise HTTPException(status_code=503, detail="Lilies module is unavailable") from exc

    response_headers = {
        name.decode("latin-1"): value.decode("latin-1")
        for name, value in upstream.headers.raw
        if name.lower() not in PROXY_HOP_BY_HOP_HEADERS
    }

    async def close_upstream() -> None:
        await upstream.aclose()
        await client.aclose()

    return StreamingResponse(
        upstream.aiter_raw(),
        status_code=upstream.status_code,
        headers=response_headers,
        background=BackgroundTask(close_upstream),
    )


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    requested_path = (STATIC_DIR / full_path).resolve()
    try:
        requested_path.relative_to(STATIC_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found") from None

    if requested_path.is_file():
        return FileResponse(requested_path)

    if INDEX_HTML.is_file():
        return FileResponse(INDEX_HTML)

    raise HTTPException(status_code=404, detail="Frontend build not found")
