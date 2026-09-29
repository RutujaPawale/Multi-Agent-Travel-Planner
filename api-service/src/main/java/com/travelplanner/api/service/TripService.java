package com.travelplanner.api.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.travelplanner.api.client.AgentServiceClient;
import com.travelplanner.api.dto.AgentRunDto;
import com.travelplanner.api.dto.TripRequestDto;
import com.travelplanner.api.dto.TripResponseDto;
import com.travelplanner.api.model.AgentRun;
import com.travelplanner.api.model.Trip;
import com.travelplanner.api.repository.AgentRunRepository;
import com.travelplanner.api.repository.TripRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class TripService {

    private static final Logger log = LoggerFactory.getLogger(TripService.class);
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    private final TripRepository tripRepository;
    private final AgentRunRepository agentRunRepository;
    private final AgentServiceClient agentServiceClient;
    private final ObjectMapper objectMapper;

    public TripService(TripRepository tripRepository,
                       AgentRunRepository agentRunRepository,
                       AgentServiceClient agentServiceClient,
                       ObjectMapper objectMapper) {
        this.tripRepository = tripRepository;
        this.agentRunRepository = agentRunRepository;
        this.agentServiceClient = agentServiceClient;
        this.objectMapper = objectMapper;
    }

    public TripResponseDto createAndPlanTrip(TripRequestDto request) {
        // 1. Initial persistence of trip
        Trip trip = new Trip();
        trip.setOrigin(request.getOrigin());
        trip.setDestination(request.getDestination());
        trip.setStartDate(request.getStartDate());
        trip.setEndDate(request.getEndDate());
        trip.setBudget(request.getBudget());
        trip.setPreferences(request.getPreferences());
        trip.setStatus("IN_PROGRESS");

        trip = tripRepository.saveAndFlush(trip);
        UUID tripId = trip.getId();

        // 2. Invoke Agent Service (LangGraph orchestration)
        try {
            String startDateStr = request.getStartDate().format(DATE_FORMATTER);
            String endDateStr = request.getEndDate().format(DATE_FORMATTER);
            Double budgetDouble = request.getBudget().doubleValue();

            String agentResponseJson = agentServiceClient.planTrip(
                    tripId.toString(),
                    request.getOrigin(),
                    request.getDestination(),
                    startDateStr,
                    endDateStr,
                    budgetDouble,
                    request.getPreferences()
            );

            trip.setItineraryResult(agentResponseJson);
            trip.setStatus("COMPLETED");
        } catch (Exception e) {
            log.error("Trip planning orchestration failed for trip {}: {}", tripId, e.getMessage());
            trip.setStatus("FAILED");
            trip.setItineraryResult("{\"error\": \"" + e.getMessage().replace("\"", "'") + "\"}");
        }

        trip = tripRepository.save(trip);

        // 3. Assemble response DTO with database-logged agent steps
        return mapToDto(trip);
    }

    @Transactional(readOnly = true)
    public List<TripResponseDto> getAllTrips() {
        return tripRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(this::mapToDto)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public TripResponseDto getTripById(UUID id) {
        Trip trip = tripRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Trip not found with id: " + id));
        return mapToDto(trip);
    }

    private TripResponseDto mapToDto(Trip trip) {
        TripResponseDto dto = new TripResponseDto();
        dto.setId(trip.getId());
        dto.setOrigin(trip.getOrigin());
        dto.setDestination(trip.getDestination());
        dto.setStartDate(trip.getStartDate());
        dto.setEndDate(trip.getEndDate());
        dto.setBudget(trip.getBudget());
        dto.setPreferences(trip.getPreferences());
        dto.setStatus(trip.getStatus());
        dto.setCreatedAt(trip.getCreatedAt());

        // Parse JSON itinerary if present
        if (trip.getItineraryResult() != null && !trip.getItineraryResult().isBlank()) {
            try {
                Object parsed = objectMapper.readValue(trip.getItineraryResult(), new TypeReference<Map<String, Object>>() {});
                dto.setItineraryResult(parsed);
            } catch (Exception e) {
                dto.setItineraryResult(trip.getItineraryResult());
            }
        }

        // Fetch associated agent execution runs from database
        List<AgentRun> runs = agentRunRepository.findByTripIdOrderByCreatedAtAsc(trip.getId());
        List<AgentRunDto> runDtos = new ArrayList<>();
        for (AgentRun run : runs) {
            Object inputObj = parseJsonOrRaw(run.getInputData());
            Object outputObj = parseJsonOrRaw(run.getOutputData());
            runDtos.add(new AgentRunDto(
                    run.getId(),
                    run.getAgentName(),
                    inputObj,
                    outputObj,
                    run.getStatus(),
                    run.getErrorMessage(),
                    run.getCreatedAt()
            ));
        }
        dto.setAgentRuns(runDtos);

        return dto;
    }

    private Object parseJsonOrRaw(String json) {
        if (json == null || json.isBlank()) return null;
        try {
            return objectMapper.readValue(json, Object.class);
        } catch (Exception e) {
            return json;
        }
    }
}
