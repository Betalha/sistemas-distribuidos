package music;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;

/** REST: recursos + verbos HTTP, JSON (mesmas rotas do rest_server.py). */
class Rest {
    static final ObjectMapper J = new ObjectMapper();

    static void start(int port) throws Exception {
        Http.serve(port, "/", (x, body) -> {
            String[] p = x.getRequestURI().getPath().substring(1).split("/");
            String m = x.getRequestMethod();
            Object r = null; int code = 200;
            if (!Data.KINDS.contains(p[0])) { Http.send(x, 404, "text/plain", new byte[0]); return; }
            try {
                if (p.length == 1 && m.equals("GET")) r = Data.list(p[0]);
                else if (p.length == 1 && m.equals("POST")) { r = Data.create(p[0], J.readValue(body, new TypeReference<Map<String, Object>>() {})); code = 201; }
                else if (p.length == 2) {
                    int id = Integer.parseInt(p[1]);
                    switch (m) {
                        case "GET" -> r = Data.get(p[0], id);
                        case "PUT" -> r = Data.update(p[0], id, J.readValue(body, new TypeReference<Map<String, Object>>() {}));
                        case "DELETE" -> { r = Data.delete(p[0], id) ? "" : null; code = 204; }
                        default -> { Http.send(x, 405, "text/plain", new byte[0]); return; }
                    }
                } else if (p.length == 3 && m.equals("GET")) {
                    int id = Integer.parseInt(p[1]);
                    r = switch (p[0] + "/" + p[2]) {
                        case "users/playlists" -> Data.playlistsOfUser(id);
                        case "playlists/songs" -> Data.songsOfPlaylist(id);
                        case "songs/playlists" -> Data.playlistsWithSong(id);
                        default -> null;
                    };
                }
            } catch (NumberFormatException e) { Http.send(x, 422, "text/plain", new byte[0]); return; }
            if (r == null) { Http.send(x, 404, "text/plain", new byte[0]); return; }
            Http.send(x, code, "application/json", code == 204 ? new byte[0] : J.writeValueAsBytes(r));
        });
    }
}
