package org.acme.boot;

import io.smallrye.common.annotation.RunOnVirtualThread;
import jakarta.inject.Inject;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import org.acme.rag.RagAssistant;

/**
 * CI fixture, not a shipped template: a REST edge for the RAG assistant, which the templates
 * expose to no client of their own. A native integration test reaches the executable only over
 * HTTP, so ci/build-from-templates.sh --native copies this into src/main/java and
 * NativeEntryServicesIT asks its question here.
 */
@Path("/boot/rag")
public class RagProbeResource {

    @Inject
    RagAssistant ragAssistant;

    @POST
    @Produces(MediaType.TEXT_PLAIN)
    @RunOnVirtualThread
    public String ask(String question) {
        return ragAssistant.ask(question);
    }
}
