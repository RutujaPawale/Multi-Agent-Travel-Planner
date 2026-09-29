package com.travelplanner.api.controller;

import com.travelplanner.api.dto.TripRequestDto;
import com.travelplanner.api.dto.TripResponseDto;
import com.travelplanner.api.service.TripService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class TripController {

    private final TripService tripService;

    public TripController(TripService tripService) {
        this.tripService = tripService;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "service", "api-service"
        ));
    }

    @PostMapping("/trips")
    public ResponseEntity<TripResponseDto> createTrip(@RequestBody TripRequestDto request) {
        TripResponseDto response = tripService.createAndPlanTrip(request);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/trips")
    public ResponseEntity<List<TripResponseDto>> getAllTrips() {
        return ResponseEntity.ok(tripService.getAllTrips());
    }

    @GetMapping("/trips/{id}")
    public ResponseEntity<TripResponseDto> getTripById(@PathVariable UUID id) {
        return ResponseEntity.ok(tripService.getTripById(id));
    }
}
