# Project Brief: ConsultEase System

## 1. Introduction
ConsultEase is a system designed to enhance interaction and consultation availability between students and faculty members. It comprises two main integrated components: a Central System running on a Raspberry Pi and multiple Faculty Desk Units based on ESP32 microcontrollers.

## 2. Project Goal
The primary goal is to provide a streamlined and real-time system for students to check faculty availability, request consultations, and receive updates, while allowing faculty to manage their availability and view incoming requests efficiently.

## 3. Key Components
1.  **Central System (Raspberry Pi)**:
    *   User Interface (PyQt) for students and administrators.
    *   RFID authentication for students.
    *   Faculty availability dashboard.
    *   Consultation request submission.
    *   Admin interface for managing faculty, students, and system settings.
    *   PostgreSQL database backend.
    *   MQTT communication hub.

2.  **Faculty Desk Unit (ESP32)**:
    *   Display for consultation requests and faculty status.
    *   BLE beacon detection for automatic presence updates.
    *   MQTT communication for receiving requests and publishing status.

## 4. Scope
The project includes the design, development, documentation, and testing of both hardware and software components as detailed in the System Development Specification. This includes:
*   UI/UX design and implementation.
*   Backend logic for database interaction, MQTT communication, and asynchronous processing.
*   Firmware development for the ESP32 units.
*   BLE integration for presence detection.
*   Comprehensive documentation for setup, usage, and maintenance.
*   Thorough testing of all system functionalities.

## 5. Success Criteria
*   Reliable and real-time updates of faculty availability.
*   Efficient processing of consultation requests.
*   Secure authentication for students and administrators.
*   User-friendly interfaces for all user types.
*   Robust and well-documented system. 