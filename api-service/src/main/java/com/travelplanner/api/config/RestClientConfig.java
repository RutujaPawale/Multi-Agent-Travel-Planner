package com.travelplanner.api.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Configuration
public class RestClientConfig {

    @Value("${agent-service.url:http://localhost:8000}")
    private String agentServiceUrl;

    @Value("${agent-service.connect-timeout-seconds:15}")
    private int connectTimeoutSeconds;

    @Value("${agent-service.read-timeout-seconds:120}")
    private int readTimeoutSeconds;

    @Bean
    public RestClient agentRestClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofSeconds(connectTimeoutSeconds));
        requestFactory.setReadTimeout(Duration.ofSeconds(readTimeoutSeconds));

        return RestClient.builder()
                .baseUrl(agentServiceUrl)
                .requestFactory(requestFactory)
                .build();
    }
}
