package music;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.concurrent.Executors;

/** Servidor HTTP comum a REST, GraphQL e SOAP (o equivalente ao uvicorn do lado Python). */
class Http {
    interface Handler { void handle(HttpExchange x, byte[] body) throws Exception; }

    static void serve(int port, String path, Handler h) throws IOException {
        var s = HttpServer.create(new InetSocketAddress(port), 1024);
        s.createContext(path, x -> {
            try { h.handle(x, x.getRequestBody().readAllBytes()); }
            catch (Exception e) { send(x, 500, "text/plain", e.toString().getBytes()); }
        });
        s.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
        s.start();
    }

    static void send(HttpExchange x, int code, String type, byte[] b) throws IOException {
        x.getResponseHeaders().set("Content-Type", type);
        if (code == 204 || b.length == 0) { x.sendResponseHeaders(code, -1); }
        else { x.sendResponseHeaders(code, b.length); x.getResponseBody().write(b); }
        x.close();
    }
}
