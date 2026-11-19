"""Mesma carga nas 4 tecnologias. Uso: locust -f locustfile.py RestUser|GraphqlUser|SoapUser|GrpcUser --host ..."""
import random, re, time
from locust import HttpUser, User, between

U, S, P = 50, 200, 150  # tamanho dos dados semeados (data.seed)


class Workload:
    """Mix de leituras (as 5 consultas do enunciado) + ciclo de escrita (criar, alterar, remover)."""
    wait_time = between(0.05, 0.15)

    def lu(self): self.do("list_users")
    def ls(self): self.do("list_songs")
    def pu(self): self.do("playlists_of_user", random.randint(1, U))
    def sp(self): self.do("songs_of_playlist", random.randint(1, P))
    def ps(self): self.do("playlists_with_song", random.randint(1, S))
    def w(self):
        i = self.do("create_user")
        self.do("update_user", i)
        self.do("delete_user", i)


# pesos: o locust não coleta @task de mixin, então a tabela vai em `tasks` de cada classe
W = {Workload.lu: 1, Workload.ls: 1, Workload.pu: 3, Workload.sp: 3, Workload.ps: 2, Workload.w: 1}


# ---------- REST ----------
class RestUser(Workload, HttpUser):
    tasks = W
    T = {
        "list_users": lambda a: ("GET", "/users", None),
        "list_songs": lambda a: ("GET", "/songs", None),
        "playlists_of_user": lambda a: ("GET", f"/users/{a}/playlists", None),
        "songs_of_playlist": lambda a: ("GET", f"/playlists/{a}/songs", None),
        "playlists_with_song": lambda a: ("GET", f"/songs/{a}/playlists", None),
        "create_user": lambda a: ("POST", "/users", {"name": "n", "email": "e@x"}),
        "update_user": lambda a: ("PUT", f"/users/{a}", {"name": "novo"}),
        "delete_user": lambda a: ("DELETE", f"/users/{a}", None),
    }

    def do(self, op, a=None):
        m, path, body = self.T[op](a)
        r = self.client.request(m, path, json=body, name=op)
        return r.json()["id"] if op == "create_user" and r.ok else None


# ---------- GraphQL (as consultas pedem só os campos necessários) ----------
class GraphqlUser(Workload, HttpUser):
    tasks = W
    Q = {
        "list_users": lambda a: ("{ users { id name email } }", {}),
        "list_songs": lambda a: ("{ songs { id title artist album } }", {}),
        "playlists_of_user": lambda a: ("query($i:Int!){ user(id:$i){ playlists{ id name userId songIds } } }", {"i": a}),
        "songs_of_playlist": lambda a: ("query($i:Int!){ playlist(id:$i){ songs{ id title artist album } } }", {"i": a}),
        "playlists_with_song": lambda a: ("query($i:Int!){ song(id:$i){ playlists{ id name userId songIds } } }", {"i": a}),
        "create_user": lambda a: ('mutation{ createUser(name:"n", email:"e@x"){ id } }', {}),
        "update_user": lambda a: ('mutation($i:Int!){ updateUser(id:$i, name:"novo"){ id } }', {"i": a}),
        "delete_user": lambda a: ("mutation($i:Int!){ deleteUser(id:$i) }", {"i": a}),
    }

    def do(self, op, a=None):
        q, v = self.Q[op](a)
        with self.client.post("/graphql", json={"query": q, "variables": v}, name=op, catch_response=True) as r:
            j = r.json() if r.ok else {}
            if not r.ok or j.get("errors") or j.get("data") is None:
                r.failure("erro graphql")
            elif op == "create_user":
                return j["data"]["createUser"]["id"]


# ---------- SOAP ----------
def env(op, **p):
    body = "".join(f"<{k}>{v}</{k}>" for k, v in p.items())
    return ('<?xml version="1.0"?><soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
            f"<soap:Body><{op}>{body}</{op}></soap:Body></soap:Envelope>")


class SoapUser(Workload, HttpUser):
    tasks = W
    T = {
        "list_users": lambda a: env("ListUsers"),
        "list_songs": lambda a: env("ListSongs"),
        "playlists_of_user": lambda a: env("ListPlaylistsByUser", user_id=a),
        "songs_of_playlist": lambda a: env("ListSongsByPlaylist", playlist_id=a),
        "playlists_with_song": lambda a: env("ListPlaylistsBySong", song_id=a),
        "create_user": lambda a: env("CreateUser", name="n", email="e@x"),
        "update_user": lambda a: env("UpdateUser", id=a, name="novo"),
        "delete_user": lambda a: env("DeleteUser", id=a),
    }

    def do(self, op, a=None):
        r = self.client.post("/soap", data=self.T[op](a), headers={"Content-Type": "application/soap+xml"}, name=op)
        return int(re.search(r"<id>(\d+)</id>", r.text).group(1)) if op == "create_user" and r.ok else None


# ---------- gRPC ----------
class GrpcUser(Workload, User):
    tasks = W
    abstract = False

    def on_start(self):
        import grpc.experimental.gevent as g; g.init_gevent()
        import grpc, music_pb2 as pb, music_pb2_grpc as rpc
        self.pb, self.stub = pb, rpc.MusicStub(grpc.insecure_channel(self.host))

    def do(self, op, a=None):
        pb = self.pb
        T = {
            "list_users": ("ListUsers", pb.Empty()), "list_songs": ("ListSongs", pb.Empty()),
            "playlists_of_user": ("ListPlaylistsByUser", pb.Id(id=a)),
            "songs_of_playlist": ("ListSongsByPlaylist", pb.Id(id=a)),
            "playlists_with_song": ("ListPlaylistsBySong", pb.Id(id=a)),
            "create_user": ("CreateUser", pb.User(name="n", email="e@x")),
            "update_user": ("UpdateUser", pb.User(id=a or 0, name="novo")),
            "delete_user": ("DeleteUser", pb.Id(id=a or 0)),
        }
        rpc_name, req = T[op]
        t, exc, r = time.perf_counter(), None, None
        try:
            r = getattr(self.stub, rpc_name)(req)
        except Exception as e:
            exc = e
        self.environment.events.request.fire(
            request_type="gRPC", name=op, response_time=(time.perf_counter() - t) * 1000,
            response_length=r.ByteSize() if r is not None else 0, exception=exc, context={})
        return r.id if op == "create_user" and r is not None else None
