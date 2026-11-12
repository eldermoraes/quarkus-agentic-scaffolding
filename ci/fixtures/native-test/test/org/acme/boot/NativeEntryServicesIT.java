package org.acme.boot;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.quarkus.test.common.QuarkusTestResource;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusIntegrationTest;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.WebSocket;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

/**
 * CI fixture, not a shipped template. Run by ci/build-from-templates.sh --native against the
 * native executable (prod profile) with every model pointed at the fake Ollama: a native image
 * fails on a missing reflection registration or resource only when that code path runs, so this
 * drives the two paths that failed natively before (#152, #153): a triage over the WebSocket,
 * and a RAG question answered from the ingested sample document.
 */
@QuarkusIntegrationTest
@QuarkusTestResource(FakeOllama.class)
class NativeEntryServicesIT {

    private static final ObjectMapper JSON = new ObjectMapper();

    /** A sentence of the sample RAG document, ci/fixtures/boot-test/rag/refund-policy.md. */
    private static final String SAMPLE_DOCUMENT_TEXT = "Refunds are issued within 14 days of purchase";

    @TestHTTPResource("/ws/triage")
    URI triageSocket;

    @TestHTTPResource("/boot/rag")
    URI ragProbe;

    @BeforeEach
    void forgetEarlierRequests() {
        FakeOllama.reset();
    }

    @Test
    void triageOverTheWebSocketReportsDone() throws Exception {
        List<JsonNode> updates = new CopyOnWriteArrayList<>();
        CompletableFuture<JsonNode> last = new CompletableFuture<>();
        URI ws = URI.create(triageSocket.toString().replaceFirst("^http", "ws"));
        WebSocket socket = HttpClient.newHttpClient().newWebSocketBuilder()
                .buildAsync(ws, new WebSocket.Listener() {
                    private final StringBuilder text = new StringBuilder();

                    @Override
                    public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean complete) {
                        text.append(data);
                        if (complete) {
                            try {
                                JsonNode update = JSON.readTree(text.toString());
                                updates.add(update);
                                String state = update.path("state").asText();
                                if (state.equals("DONE") || state.equals("ERROR")) {
                                    last.complete(update);
                                }
                            } catch (Exception e) {
                                last.completeExceptionally(e);
                            }
                            text.setLength(0);
                        }
                        webSocket.request(1);
                        return null;
                    }
                })
                .get(30, TimeUnit.SECONDS);
        socket.sendText("{\"ticket\": \"I was charged twice for order 1234.\"}", true).get(30, TimeUnit.SECONDS);

        JsonNode report = last.get(60, TimeUnit.SECONDS);
        socket.abort();

        assertEquals("DONE", report.path("state").asText(), () -> "updates: " + updates);
        assertFalse(report.path("result").path("recommendation").asText().isBlank(), report::toString);
        assertTrue(FakeOllama.requests().stream().anyMatch(request -> FakeOllama.userTurns(request).stream()
                .anyMatch(turn -> turn.contains("I was charged twice for order 1234."))));
    }

    @Test
    void ragAnswerCarriesTheIngestedDocument() throws Exception {
        HttpResponse<String> response = HttpClient.newHttpClient().send(
                HttpRequest.newBuilder(ragProbe)
                        .header("Content-Type", "text/plain")
                        .POST(HttpRequest.BodyPublishers.ofString("How long do refunds take?"))
                        .build(),
                HttpResponse.BodyHandlers.ofString());

        assertEquals(200, response.statusCode(), response::body);
        assertTrue(response.body().contains("stub answer"), response::body);
        assertTrue(FakeOllama.requests().stream().anyMatch(request -> FakeOllama.userTurns(request).stream()
                .anyMatch(turn -> turn.contains(SAMPLE_DOCUMENT_TEXT))),
                () -> "requests: " + FakeOllama.requests());
    }
}
