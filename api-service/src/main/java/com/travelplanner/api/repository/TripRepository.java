package com.travelplanner.api.repository;

import com.travelplanner.api.model.Trip;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface TripRepository extends JpaRepository<Trip, UUID> {
    List<Trip> findAllByOrderByCreatedAtDesc();
    List<Trip> findByUserIdOrderByCreatedAtDesc(UUID userId);
    Optional<Trip> findByIdAndUserId(UUID id, UUID userId);
}
