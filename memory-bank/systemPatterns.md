# System Patterns: ConsultEase System

## 1. System Architecture Overview
ConsultEase employs a distributed architecture consisting of:
*   **A Central System**: Raspberry Pi acting as a server and main interaction point for students and administrators.
*   **Multiple Faculty Desk Units**: ESP32-based clients displaying information and detecting faculty presence.

Communication between the Central System and Faculty Desk Units is facilitated by an **MQTT (Message Queuing Telemetry Transport) broker**. This ensures asynchronous and decoupled messaging.

## 2. Key Architectural Patterns

### Central System (Raspberry Pi)
*   **Model-View-Controller (MVC)-like Structure**: Explicitly requested in the specification.
    *   **Models**: Data structures for Faculty, Student, Consultation.
    *   **Views**: PyQt UI components (Authentication, Dashboard, Admin Interface).
    *   **Controllers**: Business logic, data handling, UI event management.
*   **Service Layer**: Encapsulates interactions with external systems/concerns.
    *   `RFIDService`: Handles RFID reading and validation.
    *   `MQTTService`: Manages MQTT subscriptions and publications.
    *   `DatabaseService`: Interfaces with the PostgreSQL database.
*   **Database**: PostgreSQL relational database for persistent storage of faculty, student, and consultation data.
*   **Asynchronous Operations**: Required for UI responsiveness, particularly for background tasks like RFID scanning and MQTT communication (e.g., using Python's `threading` or `asyncio`).

### Faculty Desk Unit (ESP32)
*   **Modular Design**: Separated modules for core functionalities.
    *   `DisplayModule`: Manages the TFT screen.
    *   `BLEModule`: Handles BLE scanning and presence detection.
    *   `MQTTModule`: Manages MQTT connectivity and message processing.
*   **Event-Driven**: The main loop will integrate these modules, reacting to events like incoming MQTT messages or BLE detection changes.
*   **Real-Time Status Updates**: BLE detection logic for presence, publishing status via MQTT.

## 3. Communication Patterns
*   **Publish-Subscribe via MQTT**: 
    *   Faculty Desk Units publish status updates (e.g., `consultease/faculty/{faculty_id}/status`).
    *   Central System subscribes to these status updates.
    *   Central System publishes consultation requests (e.g., `consultease/faculty/{faculty_id}/requests`).
    *   Faculty Desk Units subscribe to relevant request topics.
*   **Backward Compatibility Topics**: Support for `professor/status` and `professor/messages` as specified.

## 4. Data Management
*   **Centralized Database**: PostgreSQL on the Central System is the source of truth for student and faculty data.
*   **CRUD Operations**: Standard database operations for managing entities.

## 5. User Interface (UI) Design
*   **Central System**: PyQt-based graphical user interface with distinct screens for authentication, main dashboard, and administration.
*   **Faculty Desk Unit**: Custom interface on a 2.4-inch TFT display, optimized for readability.

## 6. Error Handling and Logging
*   **Graceful Degradation**: Connection failures (MQTT, database) should be handled gracefully.
*   **Comprehensive Logging**: System-wide logging for operations and errors on both Central System and Faculty Desk Units. 