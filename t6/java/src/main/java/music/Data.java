package music;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** Armazenamento em memória compartilhado pelas 4 implementações (espelha app/data.py). Seguro para várias threads. */
public class Data {
    public static final List<String> KINDS = List.of("users", "songs", "playlists");
    static final Map<String, Map<Integer, Map<String, Object>>> db = new HashMap<>();
    static final Map<String, AtomicInteger> seq = new HashMap<>();

    static {
        try {
            // seed.json é o mesmo estado semeado do Python (random.Random(42)), então os 8 serviços partem dos mesmos dados
            Map<String, List<Map<String, Object>>> seed = new ObjectMapper().readValue(
                Data.class.getResourceAsStream("/seed.json"), new com.fasterxml.jackson.core.type.TypeReference<>() {});
            for (String k : KINDS) {
                db.put(k, new ConcurrentHashMap<>());
                int max = 0;
                for (var d : seed.get(k)) {
                    int id = (Integer) d.get("id");
                    db.get(k).put(id, new LinkedHashMap<>(d));
                    max = Math.max(max, id);
                }
                seq.put(k, new AtomicInteger(max));
            }
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    public static Map<String, Object> create(String kind, Map<String, Object> d) {
        var n = new LinkedHashMap<>(d);
        n.put("id", seq.get(kind).incrementAndGet());
        db.get(kind).put((Integer) n.get("id"), n);
        return n;
    }

    public static Map<String, Object> get(String kind, int id) { return db.get(kind).get(id); }

    public static List<Map<String, Object>> list(String kind) { return new ArrayList<>(db.get(kind).values()); }

    /** Troca o mapa inteiro (copy-on-write), assim quem está serializando não vê o mapa mudar. */
    public static Map<String, Object> update(String kind, int id, Map<String, Object> fields) {
        return db.get(kind).computeIfPresent(id, (i, old) -> {
            var n = new LinkedHashMap<>(old);
            fields.forEach((k, v) -> { if (!k.equals("id")) n.put(k, v); });
            return n;
        });
    }

    public static boolean delete(String kind, int id) { return db.get(kind).remove(id) != null; }

    @SuppressWarnings("unchecked")
    static List<Integer> ids(Map<String, Object> p) { return (List<Integer>) p.get("song_ids"); }

    public static List<Map<String, Object>> playlistsOfUser(int uid) {
        return db.get("playlists").values().stream().filter(p -> p.get("user_id").equals(uid)).toList();
    }

    public static List<Map<String, Object>> songsOfPlaylist(int pid) {
        var p = db.get("playlists").get(pid);
        return p == null ? List.of() : ids(p).stream().map(db.get("songs")::get).filter(Objects::nonNull).toList();
    }

    public static List<Map<String, Object>> playlistsWithSong(int sid) {
        return db.get("playlists").values().stream().filter(p -> ids(p).contains(sid)).toList();
    }
}
