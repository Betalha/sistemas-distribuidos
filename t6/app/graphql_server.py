"""GraphQL: um único endpoint /graphql, o cliente escolhe os campos. uvicorn graphql_server:app"""
import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from typing import Optional
import data


@strawberry.type
class Song:
    id: int
    title: str
    artist: str
    album: str

    @strawberry.field
    def playlists(self) -> list["Playlist"]:
        return [mk_pl(p) for p in data.playlists_with_song(self.id)]


@strawberry.type
class Playlist:
    id: int
    name: str
    user_id: int
    song_ids: list[int]

    @strawberry.field
    def songs(self) -> list[Song]:
        return [Song(**s) for s in data.songs_of_playlist(self.id)]


@strawberry.type
class User:
    id: int
    name: str
    email: str

    @strawberry.field
    def playlists(self) -> list[Playlist]:
        return [mk_pl(p) for p in data.playlists_of_user(self.id)]


def mk_pl(d): return Playlist(**d)


@strawberry.type
class Query:
    users: list[User] = strawberry.field(resolver=lambda: [User(**d) for d in data.list_("users")])
    songs: list[Song] = strawberry.field(resolver=lambda: [Song(**d) for d in data.list_("songs")])
    playlists: list[Playlist] = strawberry.field(resolver=lambda: [mk_pl(d) for d in data.list_("playlists")])

    @strawberry.field
    def user(self, id: int) -> Optional[User]:
        d = data.get("users", id); return User(**d) if d else None

    @strawberry.field
    def song(self, id: int) -> Optional[Song]:
        d = data.get("songs", id); return Song(**d) if d else None

    @strawberry.field
    def playlist(self, id: int) -> Optional[Playlist]:
        d = data.get("playlists", id); return mk_pl(d) if d else None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name: str, email: str) -> User:
        return User(**data.create("users", {"name": name, "email": email}))

    @strawberry.mutation
    def update_user(self, id: int, name: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
        d = data.update("users", id, {k: v for k, v in dict(name=name, email=email).items() if v is not None})
        return User(**d) if d else None

    @strawberry.mutation
    def delete_user(self, id: int) -> bool: return data.delete("users", id)

    @strawberry.mutation
    def create_song(self, title: str, artist: str, album: str) -> Song:
        return Song(**data.create("songs", dict(title=title, artist=artist, album=album)))

    @strawberry.mutation
    def update_song(self, id: int, title: Optional[str] = None, artist: Optional[str] = None,
                    album: Optional[str] = None) -> Optional[Song]:
        d = data.update("songs", id, {k: v for k, v in dict(title=title, artist=artist, album=album).items() if v is not None})
        return Song(**d) if d else None

    @strawberry.mutation
    def delete_song(self, id: int) -> bool: return data.delete("songs", id)

    @strawberry.mutation
    def create_playlist(self, name: str, user_id: int, song_ids: list[int]) -> Playlist:
        return mk_pl(data.create("playlists", dict(name=name, user_id=user_id, song_ids=song_ids)))

    @strawberry.mutation
    def update_playlist(self, id: int, name: Optional[str] = None,
                        song_ids: Optional[list[int]] = None) -> Optional[Playlist]:
        d = data.update("playlists", id, {k: v for k, v in dict(name=name, song_ids=song_ids).items() if v is not None})
        return mk_pl(d) if d else None

    @strawberry.mutation
    def delete_playlist(self, id: int) -> bool: return data.delete("playlists", id)


app = FastAPI()
app.include_router(GraphQLRouter(strawberry.Schema(Query, Mutation), graphql_ide=None), prefix="/graphql")
