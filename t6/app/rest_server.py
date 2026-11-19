"""REST: recursos + verbos HTTP. uvicorn rest_server:app"""
from fastapi import FastAPI, HTTPException
import data

app = FastAPI()


def found(x):
    if x is None:
        raise HTTPException(404)
    return x


def crud(kind):
    @app.get(f"/{kind}")
    async def l(): return data.list_(kind)

    @app.get(f"/{kind}/{{id}}")
    async def g(id: int): return found(data.get(kind, id))

    @app.post(f"/{kind}", status_code=201)
    async def c(body: dict): return data.create(kind, body)

    @app.put(f"/{kind}/{{id}}")
    async def u(id: int, body: dict): return found(data.update(kind, id, body))

    @app.delete(f"/{kind}/{{id}}", status_code=204)
    async def d(id: int): found(data.delete(kind, id) or None)


for k in data.KINDS:
    crud(k)


@app.get("/users/{id}/playlists")
async def pu(id: int): return data.playlists_of_user(id)


@app.get("/playlists/{id}/songs")
async def sp(id: int): return data.songs_of_playlist(id)


@app.get("/songs/{id}/playlists")
async def ps(id: int): return data.playlists_with_song(id)
