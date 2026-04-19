package com.milewatch;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * MileWatch Backend — Spring Boot Application Entry Point
 *
 * This is the API gateway that sits between the React frontend and the
 * Flask ML microservice. It handles:
 * - REST API endpoints for the frontend
 * - Persistence of scored delivery attempts
 * - Communication with the Flask ML service for scoring
 * - Dashboard statistics aggregation
 */
@SpringBootApplication
public class MileWatchApplication {

    public static void main(String[] args) {
        SpringApplication.run(MileWatchApplication.class, args);
    }
}
