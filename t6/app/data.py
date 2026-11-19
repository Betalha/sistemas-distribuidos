"""Armazenamento em memória compartilhado pelas 4 implementações (mesmo dado, mesma lógica)."""
import itertools, random

KINDS = ("users", "songs", "playlists")
_db = {k: {} for k in KINDS}
_seq = {k: itertools.count(1) for k in KINDS}


def create(kind, d):
    d = {**d, "id": next(_seq[kind])}
    _db[kind][d["id"]] = d
    return d


def get(kind, id):
    return _db[kind].get(id)


def list_(kind):
    return list(_db[kind].values())


def update(kind, id, fields):
    d = _db[kind].get(id)
    if d is not None:
        d.update({k: v for k, v in fields.items() if k != "id"})
    return d


def delete(kind, id):
    return _db[kind].pop(id, None) is not None


# consultas pedidas no enunciado
def playlists_of_user(uid):
    return [p for p in _db["playlists"].values() if p["user_id"] == uid]


def songs_of_playlist(pid):
    p = _db["playlists"].get(pid)
    return [] if p is None else [_db["songs"][s] for s in p["song_ids"] if s in _db["songs"]]


def playlists_with_song(sid):
    return [p for p in _db["playlists"].values() if sid in p["song_ids"]]


def seed(n_users=50, n_songs=200, per_user=3, per_playlist=10):
    r = random.Random(42)  # determinístico: os 4 serviços sobem com os mesmos dados
    for i in range(n_users):
        create("users", {"name": f"user{i+1}", "email": f"user{i+1}@mail.com"})
    for i in range(n_songs):
        create("songs", {"title": f"song{i+1}", "artist": f"artist{i % 20}", "album": f"album{i % 40}"})
    for u in range(1, n_users + 1):
        for j in range(per_user):
            create("playlists", {"name": f"pl{u}-{j}", "user_id": u,
                                 "song_ids": r.sample(range(1, n_songs + 1), per_playlist)})


seed()
