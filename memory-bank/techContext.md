# Tech Context: ConsultEase System

## 1. Hardware Stack

### Central System
*   **Compute**: Raspberry Pi 4
*   **Operating System**: Raspberry Pi OS (Bookworm 64-bit, as specified)
*   **Display**: 10.1-inch touchscreen (1024x600 resolution)
*   **Input**: USB RFID IC Reader

### Faculty Desk Unit
*   **Microcontroller**: ESP32
*   **Display**: 2.4-inch TFT SPI Screen (ST7789 driver)
*   **Connectivity**: Wi-Fi (for MQTT), Bluetooth Low Energy (BLE) for beacon detection.
*   **Beacon System**: Faculty members will carry personal BLE beacons. The system will be configured with each faculty's unique BLE identifier (e.g., MAC address or a specific advertising UUID).

## 2. Software Stack & Technologies

### Central System (Raspberry Pi)
*   **Programming Language**: Python
*   **UI Framework**: PyQt5
*   **Database**: PostgreSQL (to be installed and configured as part of the project)
*   **Communication Protocol**: MQTT (e.g., using Paho MQTT Python client; broker to be set up, e.g., Mosquitto on RPi)
*   **Asynchronous Programming**: Python `threading` or `asyncio` libraries.
*   **RFID Integration**: Python library for USB RFID reader (e.g., `pyserial` if it presents as a serial device, or a dedicated library if available).

### Faculty Desk Unit (ESP32)
*   **Programming Environment**: C/C++ (typically using Arduino IDE or ESP-IDF - Espressif IoT Development Framework)
*   **Libraries**:
    *   TFT display library (e.g., Adafruit GFX, TFT_eSPI for ST7789)
    *   BLE libraries for scanning (ESP32's built-in BLE capabilities).
    *   MQTT client library (e.g., PubSubClient).
    *   WiFi connectivity libraries.
    *   JSON parsing library (if needed, e.g., ArduinoJson).

## 3. Development Environment
*   **Central System**: 
    *   Code editor/IDE (e.g., VS Code, Thonny on RPi).
    *   Python environment management (e.g., `venv`).
*   **Faculty Desk Unit**:
    *   Arduino IDE or PlatformIO with VS Code for ESP32 development.
*   **Version Control**: Git (recommended).

## 4. Network Configuration
*   Both Central System and Faculty Desk Units require network connectivity (Wi-Fi or Ethernet for RPi, Wi-Fi for ESP32) to communicate via MQTT.
*   An MQTT broker needs to be accessible by all components (will be self-hosted on the RPi, e.g., Mosquitto, and set up as part of the project).
*   PostgreSQL server will be installed and configured on the Raspberry Pi as part of the project.

## 5. Key Technical Constraints & Considerations
*   **Real-time performance**: For MQTT messaging and UI updates.
*   **Resource limitations on ESP32**: Memory and processing power need to be managed efficiently.
*   **BLE RSSI Reliability**: RSSI-based presence detection can be affected by environmental factors; thresholding and debouncing logic will be important.
*   **Screen Real Estate**: UI design must be optimized for the specified screen sizes (1024x600 for RPi, small 2.4" for ESP32).
*   **Database Schema Design**: Needs to be robust to support all required data and relationships for students, faculty, and consultations.
*   **Security**: Password protection for admin interface is specified. MQTT and database access should also be secured. 