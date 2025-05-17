#ifndef CONFIG_H
#define CONFIG_H

// --- WiFi Configuration ---
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// --- MQTT Configuration ---
#define MQTT_BROKER_HOST "IP_ADDRESS_OF_RASPBERRY_PI" // Replace with RPi's actual IP
#define MQTT_BROKER_PORT 1883
#define MQTT_CLIENT_ID_PREFIX "FacultyDeskUnit_" // Will append BLE ID for uniqueness
#define MQTT_STATUS_TOPIC_TEMPLATE "consultease/faculty/%s/status" // %s will be FACULTY_BLE_IDENTIFIER
#define MQTT_REQUEST_TOPIC_TEMPLATE "consultease/faculty/%s/requests" // %s will be FACULTY_BLE_IDENTIFIER
// Backward compatibility topics (optional, implement if needed)
// #define MQTT_PROFESSOR_STATUS_TOPIC "professor/status"
// #define MQTT_PROFESSOR_MESSAGES_TOPIC "professor/messages"

// --- Faculty Identification ---
// EACH FACULTY DESK UNIT MUST HAVE A UNIQUE BLE IDENTIFIER FOR THEIR BEACON
// This is the BLE Address or a unique part of the advertising data of the faculty's personal beacon.
#define FACULTY_PERSONAL_BEACON_ID "AA:BB:CC:DD:EE:FF" // Placeholder: REPLACE with actual BLE beacon MAC or unique ID

// --- BLE Beacon Detection ---
#define BLE_SCAN_DURATION_SECONDS 5 // Duration for each BLE scan cycle
#define BLE_RSSI_THRESHOLD -75      // RSSI threshold for presence detection (dBm, adjust based on testing)
#define PRESENCE_TIMEOUT_SECONDS 15 // Seconds without beacon detection to become "Unavailable"

// --- Display Configuration ---
#define FACULTY_NAME "Dr. Placeholder" // Replace with actual faculty name or load dynamically if possible later

#endif // CONFIG_H 