package org.acme.boot;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import io.quarkus.test.common.QuarkusTestResourceLifecycleManager;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.Executors;

/**
 * CI fixture, not a shipped template: a stand-in for the Ollama HTTP API. Every chat model the
 * application configures (default, "main", "smaller") is pointed at it, so the boot test needs
 * no live model, and it records each chat request so tests can assert what the application
 * actually sent: which model, how many turns, which text.
 *
 * Answers: plain text for a plain request; for a request that carries a JSON schema (a
 * record-returning service) a JSON object with every schema property filled in. A test can
 * queue different answers with {@link #answerNextWith(String...)}.
 *
 * The recording API ({@link #requests()}, {@link #userTurns(JsonNode)}, {@link #reset()},
 * {@link #answerNextWith(String...)}) is the seam later regression tests build on (model routing,
 * retrieval scoping, output validation, request isolation): keep these signatures stable.
 * Copied into the generated project's src/test/java by ci/boot_overlay.py.
 */
public class FakeOllama implements QuarkusTestResourceLifecycleManager {

    private static final ObjectMapper JSON = new ObjectMapper();
    private static final List<JsonNode> REQUESTS = new CopyOnWriteArrayList<>();
    private static final ConcurrentLinkedDeque<String> QUEUED_ANSWERS = new ConcurrentLinkedDeque<>();

    private HttpServer server;

    @Override
    public Map<String, String> start() {
        try {
            server = HttpServer.create(new InetSocketAddress("localhost", 0), 0);
        } catch (IOException e) {
            throw new IllegalStateException("could not start the fake Ollama", e);
        }
        server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
        server.createContext("/api/chat", FakeOllama::chat);
        server.start();
        String url = "http://localhost:" + server.getAddress().getPort();
        return Map.of(
                "quarkus.langchain4j.ollama.base-url", url,
                "quarkus.langchain4j.ollama.main.base-url", url,
                "quarkus.langchain4j.ollama.smaller.base-url", url);
    }

    @Override
    public void stop() {
        if (server != null) {
            server.stop(0);
        }
    }

    /** Forgets recorded requests and queued answers; call it before each test. */
    public static void reset() {
        REQUESTS.clear();
        QUEUED_ANSWERS.clear();
    }

    /** The next chat requests get these message contents, in order, instead of the default. */
    public static void answerNextWith(String... contents) {
        QUEUED_ANSWERS.addAll(List.of(contents));
    }

    /** Every chat request received since the last reset, as the JSON the application sent. */
    public static List<JsonNode> requests() {
        return List.copyOf(REQUESTS);
    }

    /** The text of the user turns of one recorded request, oldest first. */
    public static List<String> userTurns(JsonNode request) {
        List<String> turns = new ArrayList<>();
        for (JsonNode message : request.path("messages")) {
            if ("user".equals(message.path("role").asText())) {
                turns.add(message.path("content").asText());
            }
        }
        return turns;
    }

    private static void chat(HttpExchange exchange) throws IOException {
        JsonNode request = JSON.readTree(exchange.getRequestBody());
        REQUESTS.add(request);
        String queued = QUEUED_ANSWERS.poll();
        String content = queued != null ? queued : defaultAnswer(request.path("format"));

        ObjectNode response = JSON.createObjectNode();
        response.put("model", request.path("model").asText());
        response.put("created_at", "2026-01-01T00:00:00Z");
        response.putObject("message").put("role", "assistant").put("content", content);
        response.put("done", true);
        response.put("done_reason", "stop");
        response.put("prompt_eval_count", 1);
        response.put("eval_count", 1);

        byte[] body = JSON.writeValueAsBytes(response);
        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(200, body.length);
        try (var out = exchange.getResponseBody()) {
            out.write(body);
        }
    }

    private static String defaultAnswer(JsonNode format) {
        return format.isObject() ? fill(format).toString() : "stub answer";
    }

    /** Builds a value that satisfies a JSON schema: every property present, strings non-blank. */
    private static JsonNode fill(JsonNode schema) {
        if (schema.has("enum")) {
            return schema.get("enum").get(0);
        }
        return switch (schema.path("type").asText("string")) {
            case "object" -> {
                ObjectNode object = JSON.createObjectNode();
                schema.path("properties").fields()
                        .forEachRemaining(property -> object.set(property.getKey(), fill(property.getValue())));
                yield object;
            }
            case "array" -> JSON.createArrayNode();
            case "integer", "number" -> JSON.getNodeFactory().numberNode(1);
            case "boolean" -> JSON.getNodeFactory().booleanNode(true);
            default -> JSON.getNodeFactory().textNode("stub value");
        };
    }
}
