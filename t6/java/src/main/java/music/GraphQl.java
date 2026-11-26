package music;

import com.fasterxml.jackson.core.type.TypeReference;
import graphql.*;
import graphql.schema.*;
import graphql.schema.idl.*;
import java.io.InputStreamReader;
import java.util.*;

/** GraphQL: um endpoint /graphql. O esquema (schema.graphqls) é o SDL gerado pelo Strawberry do lado Python. */
class GraphQl {
    static void start(int port) throws Exception {
        var sdl = new SchemaParser().parse(new InputStreamReader(GraphQl.class.getResourceAsStream("/schema.graphqls")));
        var w = RuntimeWiring.newRuntimeWiring();
        w.type("Query", t -> {
            for (String k : Data.KINDS) t.dataFetcher(k, e -> Data.list(k));
            t.dataFetcher("user", e -> Data.get("users", e.getArgument("id")));
            t.dataFetcher("song", e -> Data.get("songs", e.getArgument("id")));
            return t.dataFetcher("playlist", e -> Data.get("playlists", e.getArgument("id")));
        });
        w.type("User", t -> t.dataFetcher("playlists", e -> Data.playlistsOfUser(id(e))));
        w.type("Song", t -> t.dataFetcher("playlists", e -> Data.playlistsWithSong(id(e))));
        w.type("Playlist", t -> t
            .dataFetcher("songs", e -> Data.songsOfPlaylist(id(e)))
            .dataFetcher("userId", e -> src(e).get("user_id"))
            .dataFetcher("songIds", e -> src(e).get("song_ids")));
        w.type("Mutation", t -> {
            for (var en : Map.of("users", "User", "songs", "Song", "playlists", "Playlist").entrySet()) {
                String k = en.getKey(), n = en.getValue();
                t.dataFetcher("create" + n, e -> Data.create(k, args(e)));
                t.dataFetcher("update" + n, e -> {
                    var a = args(e); a.values().removeIf(Objects::isNull);   // campos omitidos não alteram
                    return Data.update(k, e.getArgument("id"), a);
                });
                t.dataFetcher("delete" + n, e -> Data.delete(k, e.getArgument("id")));
            }
            return t;
        });
        GraphQL gql = GraphQL.newGraphQL(new SchemaGenerator().makeExecutableSchema(sdl, w.build())).build();
        Http.serve(port, "/graphql", (x, body) -> {
            Map<String, Object> req = Rest.J.readValue(body, new TypeReference<>() {});
            @SuppressWarnings("unchecked") var vars = (Map<String, Object>) req.getOrDefault("variables", Map.of());
            var r = gql.execute(ExecutionInput.newExecutionInput().query((String) req.get("query")).variables(vars).build());
            Http.send(x, 200, "application/json", Rest.J.writeValueAsBytes(r.toSpecification()));
        });
    }

    @SuppressWarnings("unchecked")
    static Map<String, Object> src(DataFetchingEnvironment e) { return (Map<String, Object>) e.getSource(); }

    static int id(DataFetchingEnvironment e) { return (Integer) src(e).get("id"); }

    /** Argumentos GraphQL (camelCase) -> campos do dado (snake_case), sem o id. */
    static Map<String, Object> args(DataFetchingEnvironment e) {
        var m = new LinkedHashMap<String, Object>();
        e.getArguments().forEach((k, v) -> { if (!k.equals("id")) m.put(k.equals("userId") ? "user_id" : k.equals("songIds") ? "song_ids" : k, v); });
        return m;
    }
}
