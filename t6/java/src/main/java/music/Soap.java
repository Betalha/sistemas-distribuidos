package music;

import java.io.ByteArrayInputStream;
import java.util.*;
import java.util.function.Function;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.*;

/** SOAP 1.2 escrito à mão (um POST /soap, operação = nome do 1º filho do Body), igual ao soap_server.py. Sem WSDL. */
class Soap {
    static final String NS = "http://www.w3.org/2003/05/soap-envelope";
    static final String ENV = "<?xml version=\"1.0\"?><soap:Envelope xmlns:soap=\"" + NS + "\"><soap:Body>%s</soap:Body></soap:Envelope>";
    static final Map<String, Function<Map<String, Object>, Object>> OPS = new HashMap<>();

    static {
        for (var e : Map.of("users", "User", "songs", "Song", "playlists", "Playlist").entrySet()) {
            String k = e.getKey(), n = e.getValue();
            OPS.put("List" + n + "s", p -> Data.list(k));
            OPS.put("Get" + n, p -> Data.get(k, (Integer) p.get("id")));
            OPS.put("Create" + n, p -> Data.create(k, p));
            OPS.put("Update" + n, p -> Data.update(k, (Integer) p.get("id"), p));
            OPS.put("Delete" + n, p -> Map.of("deleted", Data.delete(k, (Integer) p.get("id"))));
        }
        OPS.put("ListPlaylistsByUser", p -> Data.playlistsOfUser((Integer) p.get("user_id")));
        OPS.put("ListSongsByPlaylist", p -> Data.songsOfPlaylist((Integer) p.get("playlist_id")));
        OPS.put("ListPlaylistsBySong", p -> Data.playlistsWithSong((Integer) p.get("song_id")));
    }

    static String esc(String s) { return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"); }

    static void xml(StringBuilder sb, String tag, Object v) {
        sb.append('<').append(tag).append('>');
        if (v instanceof Map<?, ?> m) m.forEach((k, x) -> xml(sb, (String) k, x));
        else if (v instanceof List<?> l) l.forEach(x -> xml(sb, tag.endsWith("_ids") ? "song_id" : "item", x));
        else sb.append(esc(String.valueOf(v)));
        sb.append("</").append(tag).append('>');
    }

    static Map<String, Object> cast(Map<String, Object> p) {
        for (String k : List.of("id", "user_id", "playlist_id", "song_id"))
            if (p.containsKey(k)) p.put(k, Integer.parseInt((String) p.get(k)));
        if (p.containsKey("song_ids")) {
            var ids = new ArrayList<Integer>();
            for (String s : ((String) p.get("song_ids")).split(",")) if (!s.isEmpty()) ids.add(Integer.parseInt(s));
            p.put("song_ids", ids);
        }
        return p;
    }

    static byte[] fault(String msg) { return (ENV.formatted("<soap:Fault><soap:Reason><soap:Text>" + esc(msg) + "</soap:Text></soap:Reason></soap:Fault>")).getBytes(); }

    static void start(int port) throws Exception {
        var f = DocumentBuilderFactory.newInstance();
        f.setNamespaceAware(true);
        f.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        Http.serve(port, "/soap", (x, body) -> {
            String type = "application/soap+xml";
            try {
                Document d = f.newDocumentBuilder().parse(new ByteArrayInputStream(body));
                Node b = d.getElementsByTagNameNS(NS, "Body").item(0).getFirstChild();
                while (b.getNodeType() != Node.ELEMENT_NODE) b = b.getNextSibling();
                var p = new LinkedHashMap<String, Object>();
                for (Node c = b.getFirstChild(); c != null; c = c.getNextSibling())
                    if (c.getNodeType() == Node.ELEMENT_NODE) p.put(c.getLocalName(), c.getTextContent());
                Object r = OPS.get(b.getLocalName()).apply(cast(p));
                if (r == null) { Http.send(x, 500, type, fault("not found")); return; }
                var sb = new StringBuilder();
                xml(sb, b.getLocalName() + "Response", r);
                Http.send(x, 200, type, ENV.formatted(sb).getBytes());
            } catch (Exception e) {
                Http.send(x, 500, type, fault(e.getClass().getSimpleName()));
            }
        });
    }
}
