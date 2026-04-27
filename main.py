import httpx
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()
GITHUB_API = "https://api.github.com"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/{username}")
async def get_gists(
    username: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API}/users/{username}/gists",
            params={"page": page, "per_page": per_page},
        )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    return {
        "user": username,
        "page": page,
        "per_page": per_page,
        "gists": [
            {
                "id": g["id"],
                "description": g.get("description") or "No description",
                "url": g["html_url"],
            }
            for g in response.json()
        ],
    }