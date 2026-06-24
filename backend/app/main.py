from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, posts, comments, admin
from app.core.config import settings

app = FastAPI(title="UTOO", version="0.1.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

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


@app.get("/health")
async def health():
    return {"status": "ok"}


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
