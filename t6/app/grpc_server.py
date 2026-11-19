"""gRPC (HTTP/2 + protobuf). python grpc_server.py"""
import asyncio, grpc
import data, music_pb2 as pb, music_pb2_grpc as rpc


def todict(m):
    v = {f.name: getattr(m, f.name) for f in m.DESCRIPTOR.fields}
    return {k: x if isinstance(x, (str, int)) else list(x) for k, x in v.items()}


class Svc:
    pass


def on(rpc_name, fn):
    async def h(self, req, ctx):
        r = fn(req)
        if r is None:
            await ctx.abort(grpc.StatusCode.NOT_FOUND, "not found")
        return r
    setattr(Svc, rpc_name, h)


for kind, name in (("users", "User"), ("songs", "Song"), ("playlists", "Playlist")):
    M, L = getattr(pb, name), getattr(pb, name + "s")
    on(f"List{name}s", lambda r, k=kind, L=L: L(items=data.list_(k)))
    on(f"Get{name}", lambda r, k=kind, M=M: (lambda d: d and M(**d))(data.get(k, r.id)))
    on(f"Create{name}", lambda r, k=kind, M=M: M(**data.create(k, {x: v for x, v in todict(r).items() if x != "id"})))
    on(f"Update{name}", lambda r, k=kind, M=M: (lambda d: d and M(**d))(data.update(k, r.id, todict(r))))
    on(f"Delete{name}", lambda r, k=kind: pb.Empty() if data.delete(k, r.id) else None)
on("ListPlaylistsByUser", lambda r: pb.Playlists(items=data.playlists_of_user(r.id)))
on("ListSongsByPlaylist", lambda r: pb.Songs(items=data.songs_of_playlist(r.id)))
on("ListPlaylistsBySong", lambda r: pb.Playlists(items=data.playlists_with_song(r.id)))


async def main():
    s = grpc.aio.server()
    rpc.add_MusicServicer_to_server(Svc(), s)
    s.add_insecure_port("[::]:8000")
    await s.start()
    await s.wait_for_termination()


asyncio.run(main())
