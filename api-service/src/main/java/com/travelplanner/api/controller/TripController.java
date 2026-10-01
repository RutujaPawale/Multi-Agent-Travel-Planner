package com.travelplanner.api.controller;

import com.travelplanner.api.dto.TripRequestDto;
import com.travelplanner.api.dto.TripResponseDto;
import com.travelplanner.api.security.UserPrincipal;
import com.travelplanner.api.service.TripService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
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
    public ResponseEntity<TripResponseDto> createTrip(
            @RequestBody TripRequestDto request,
            @AuthenticationPrincipal UserPrincipal principal
    ) {
        TripResponseDto response = tripService.createAndPlanTrip(request, principal.getId());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/trips")
    public ResponseEntity<List<TripResponseDto>> getUserTrips(
            @AuthenticationPrincipal UserPrincipal principal
    ) {
        return ResponseEntity.ok(tripService.getUserTrips(principal.getId()));
    }

    @GetMapping("/trips/{id}")
    public ResponseEntity<?> getTripById(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal
    ) {
        try {
            TripResponseDto trip = tripService.getUserTripById(id, principal.getId());
            return ResponseEntity.ok(trip);
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("error", e.getMessage()));
        }
    }

    @DeleteMapping("/trips/{id}")
    public ResponseEntity<?> deleteTrip(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal
    ) {
        try {
            tripService.deleteUserTrip(id, principal.getId());
            return ResponseEntity.noContent().build();
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of("error", e.getMessage()));
        }
    }
}
