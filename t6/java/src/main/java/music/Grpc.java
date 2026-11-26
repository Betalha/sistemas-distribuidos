package music;

import io.grpc.*;
import io.grpc.stub.StreamObserver;
import java.util.*;
import java.util.function.Function;
import music.MusicOuterClass.*;

/** gRPC (HTTP/2 + protobuf), contrato = o mesmo music.proto do Python. */
class Grpc extends MusicGrpc.MusicImplBase {
    static <T> void reply(StreamObserver<T> o, T v) {
        if (v == null) { o.onError(Status.NOT_FOUND.withDescription("not found").asRuntimeException()); return; }
        o.onNext(v); o.onCompleted();
    }

    static Map<String, Object> m(Object... kv) {
        var r = new LinkedHashMap<String, Object>();
        for (int i = 0; i < kv.length; i += 2) r.put((String) kv[i], kv[i + 1]);
        return r;
    }

    // dado <-> mensagem
    @SuppressWarnings("unchecked")
    static User user(Map<String, Object> d) { return d == null ? null : User.newBuilder().setId((Integer) d.get("id")).setName((String) d.get("name")).setEmail((String) d.get("email")).build(); }
    static Map<String, Object> d(User u) { return m("id", u.getId(), "name", u.getName(), "email", u.getEmail()); }
    static Song song(Map<String, Object> d) { return d == null ? null : Song.newBuilder().setId((Integer) d.get("id")).setTitle((String) d.get("title")).setArtist((String) d.get("artist")).setAlbum((String) d.get("album")).build(); }
    static Map<String, Object> d(Song s) { return m("id", s.getId(), "title", s.getTitle(), "artist", s.getArtist(), "album", s.getAlbum()); }
    static Playlist pl(Map<String, Object> d) { return d == null ? null : Playlist.newBuilder().setId((Integer) d.get("id")).setName((String) d.get("name")).setUserId((Integer) d.get("user_id")).addAllSongIds(Data.ids(d)).build(); }
    static Map<String, Object> d(Playlist p) { return m("id", p.getId(), "name", p.getName(), "user_id", p.getUserId(), "song_ids", new ArrayList<>(p.getSongIdsList())); }
    static Users users(List<Map<String, Object>> l) { return Users.newBuilder().addAllItems(l.stream().map(Grpc::user).toList()).build(); }
    static Songs songs(List<Map<String, Object>> l) { return Songs.newBuilder().addAllItems(l.stream().map(Grpc::song).toList()).build(); }
    static Playlists pls(List<Map<String, Object>> l) { return Playlists.newBuilder().addAllItems(l.stream().map(Grpc::pl).toList()).build(); }
    static Map<String, Object> noId(Map<String, Object> d) { d.remove("id"); return d; }
    static Empty E = Empty.getDefaultInstance();

    public void listUsers(Empty r, StreamObserver<Users> o) { reply(o, users(Data.list("users"))); }
    public void getUser(Id r, StreamObserver<User> o) { reply(o, user(Data.get("users", r.getId()))); }
    public void createUser(User r, StreamObserver<User> o) { reply(o, user(Data.create("users", noId(d(r))))); }
    public void updateUser(User r, StreamObserver<User> o) { reply(o, user(Data.update("users", r.getId(), d(r)))); }
    public void deleteUser(Id r, StreamObserver<Empty> o) { reply(o, Data.delete("users", r.getId()) ? E : null); }

    public void listSongs(Empty r, StreamObserver<Songs> o) { reply(o, songs(Data.list("songs"))); }
    public void getSong(Id r, StreamObserver<Song> o) { reply(o, song(Data.get("songs", r.getId()))); }
    public void createSong(Song r, StreamObserver<Song> o) { reply(o, song(Data.create("songs", noId(d(r))))); }
    public void updateSong(Song r, StreamObserver<Song> o) { reply(o, song(Data.update("songs", r.getId(), d(r)))); }
    public void deleteSong(Id r, StreamObserver<Empty> o) { reply(o, Data.delete("songs", r.getId()) ? E : null); }

    public void listPlaylists(Empty r, StreamObserver<Playlists> o) { reply(o, pls(Data.list("playlists"))); }
    public void getPlaylist(Id r, StreamObserver<Playlist> o) { reply(o, pl(Data.get("playlists", r.getId()))); }
    public void createPlaylist(Playlist r, StreamObserver<Playlist> o) { reply(o, pl(Data.create("playlists", noId(d(r))))); }
    public void updatePlaylist(Playlist r, StreamObserver<Playlist> o) { reply(o, pl(Data.update("playlists", r.getId(), d(r)))); }
    public void deletePlaylist(Id r, StreamObserver<Empty> o) { reply(o, Data.delete("playlists", r.getId()) ? E : null); }

    public void listPlaylistsByUser(Id r, StreamObserver<Playlists> o) { reply(o, pls(Data.playlistsOfUser(r.getId()))); }
    public void listSongsByPlaylist(Id r, StreamObserver<Songs> o) { reply(o, songs(Data.songsOfPlaylist(r.getId()))); }
    public void listPlaylistsBySong(Id r, StreamObserver<Playlists> o) { reply(o, pls(Data.playlistsWithSong(r.getId()))); }

    static void start(int port) throws Exception {
        ServerBuilder.forPort(port).addService(new Grpc()).build().start().awaitTermination();
    }
}
