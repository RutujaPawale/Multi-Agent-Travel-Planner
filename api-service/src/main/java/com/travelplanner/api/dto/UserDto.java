package com.travelplanner.api.dto;

import java.time.OffsetDateTime;
import java.util.UUID;

public class UserDto {
    private UUID id;
    private String email;
    private String name;
    private OffsetDateTime createdAt;

    public UserDto() {}

    public UserDto(UUID id, String email, String name, OffsetDateTime createdAt) {
        this.id = id;
        this.email = email;
        this.name = name;
        this.createdAt = createdAt;
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
