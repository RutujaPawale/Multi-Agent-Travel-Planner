package com.travelplanner.api.dto;

import java.time.OffsetDateTime;
import java.util.UUID;

public class AgentRunDto {
    private UUID id;
    private String agentName;
    private Object inputData;
    private Object outputData;
    private String status;
    private String errorMessage;
    private OffsetDateTime createdAt;

    public AgentRunDto() {}

    public AgentRunDto(UUID id, String agentName, Object inputData, Object outputData, String status, String errorMessage, OffsetDateTime createdAt) {
        this.id = id;
        this.agentName = agentName;
        this.inputData = inputData;
        this.outputData = outputData;
        this.status = status;
        this.errorMessage = errorMessage;
        this.createdAt = createdAt;
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getAgentName() {
        return agentName;
    }

    public void setAgentName(String agentName) {
        this.agentName = agentName;
    }

    public Object getInputData() {
        return inputData;
    }

    public void setInputData(Object inputData) {
        this.inputData = inputData;
    }

    public Object getOutputData() {
        return outputData;
    }

    public void setOutputData(Object outputData) {
        this.outputData = outputData;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
