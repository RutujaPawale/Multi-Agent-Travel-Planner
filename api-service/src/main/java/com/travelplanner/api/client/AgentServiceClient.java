package com.travelplanner.api.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.HashMap;
import java.util.Map;

@Component
public class AgentServiceClient {

    private static final Logger log = LoggerFactory.getLogger(AgentServiceClient.class);
    private final RestClient agentRestClient;

    public AgentServiceClient(RestClient agentRestClient) {
        this.agentRestClient = agentRestClient;
    }

    public String planTrip(String tripId, String origin, String destination, String startDate, String endDate, Double budget, String preferences) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("trip_id", tripId);
        payload.put("origin", origin);
        payload.put("destination", destination);
        payload.put("start_date", startDate);
        payload.put("end_date", endDate);
        payload.put("budget", budget);
        payload.put("preferences", preferences != null ? preferences : "");

        log.info("Dispatching orchestration request to agent-service for trip {}: {} -> {}", tripId, origin, destination);

        try {
            return agentRestClient.post()
                    .uri("/plan-trip")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(payload)
                    .retrieve()
                    .body(String.class);
        } catch (Exception e) {
            log.error("Failed to execute agent-service planning workflow: {}", e.getMessage(), e);
            throw new RuntimeException("Agent service orchestration failed: " + e.getMessage(), e);
        }
    }
}
