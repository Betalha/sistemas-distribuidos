package music;

/** java -jar ... rest|graphql|soap|grpc : um processo por tecnologia, na porta 8000. */
public class Main {
    public static void main(String[] a) throws Exception {
        switch (a[0]) {
            case "rest" -> Rest.start(8000);
            case "graphql" -> GraphQl.start(8000);
            case "soap" -> Soap.start(8000);
            case "grpc" -> Grpc.start(8000);
            default -> throw new IllegalArgumentException(a[0]);
        }
    }
}
