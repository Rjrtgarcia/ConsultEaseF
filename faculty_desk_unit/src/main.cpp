// Faculty Desk Unit - Main

#include <Arduino.h>
#include "config.h"
#include "display_module.h"
#include "ble_module.h"
#include "mqtt_module.h"

// --- Global State Variables ---
bool is_faculty_present = false;
unsigned long last_beacon_seen_time = 0;
unsigned long last_status_publish_time = 0;
const unsigned long STATUS_PUBLISH_INTERVAL = 5000; // Publish status every 5 seconds regardless of change
String current_wifi_status_str = "WiFi: Init";
String current_mqtt_status_str = "MQTT: Init";

// --- Forward Declarations for MQTT Message Handling (Phase 3) ---
void handle_incoming_mqtt_message(const char* topic, const char* payload);

void setup() {
    Serial.begin(115200);
    while (!Serial) { delay(10); }
    Serial.println("\nConsultEase Faculty Desk Unit - Booting...");

    display_init();
    Serial.println("Display Initialized.");

    ble_init();
    Serial.println("BLE Initialized.");

    // Use a unique part of BLE ID or MAC for MQTT client ID suffix
    // For simplicity, using a fixed part of the beacon ID defined in config
    // Ensure FACULTY_PERSONAL_BEACON_ID is set in config.h
    const char* facultyIdForMqtt = FACULTY_PERSONAL_BEACON_ID; // Or a shorter, URL-safe version
    mqtt_init(facultyIdForMqtt, FACULTY_PERSONAL_BEACON_ID);
    mqtt_set_callback(handle_incoming_mqtt_message); // For Phase 3
    Serial.println("MQTT Initialized.");

    display_set_status("Initializing...", false);
    last_beacon_seen_time = millis(); // Initialize to prevent immediate timeout
    Serial.println("Setup Complete. Starting main loop.");
}

void update_presence_and_publish_status() {
    bool beacon_detected_this_cycle = ble_check_beacon_presence(FACULTY_PERSONAL_BEACON_ID, BLE_RSSI_THRESHOLD);
    unsigned long current_time = millis();
    bool previous_presence_state = is_faculty_present;

    if (beacon_detected_this_cycle) {
        is_faculty_present = true;
        last_beacon_seen_time = current_time;
    } else {
        if (current_time - last_beacon_seen_time > (PRESENCE_TIMEOUT_SECONDS * 1000)) {
            is_faculty_present = false;
        }
        // If not seen this cycle, but still within timeout, is_faculty_present remains true from previous cycle.
    }

    // Update display and publish MQTT status if presence changed or if publish interval met
    if (is_faculty_present != previous_presence_state || (current_time - last_status_publish_time > STATUS_PUBLISH_INTERVAL)) {
        const char* status_str = is_faculty_present ? "Available" : "Unavailable";
        display_set_status(status_str, is_faculty_present);
        
        // Construct simple JSON payload for status
        char status_payload[50];
        snprintf(status_payload, sizeof(status_payload), "{\"status\": \"%s\"}", status_str);
        
        if (mqtt_publish_status(FACULTY_PERSONAL_BEACON_ID, status_payload)) {
            Serial.printf("Status '%s' published for %s\n", status_str, FACULTY_PERSONAL_BEACON_ID);
        } else {
            Serial.printf("Failed to publish status '%s' for %s\n", status_str, FACULTY_PERSONAL_BEACON_ID);
        }
        last_status_publish_time = current_time;
    }
}

void update_connection_status_display(){
    bool wifi_conn = (WiFi.status() == WL_CONNECTED);
    bool mqtt_conn = mqtt_is_connected();
    String new_wifi_str = wifi_conn ? "WiFi: OK" : "WiFi: ERR";
    String new_mqtt_str = mqtt_conn ? "MQTT: OK" : "MQTT: ERR";

    if(new_wifi_str != current_wifi_status_str || new_mqtt_str != current_mqtt_status_str){
        current_wifi_status_str = new_wifi_str;
        current_mqtt_status_str = new_mqtt_str;
        display_show_connection_status(current_wifi_status_str.c_str(), current_mqtt_status_str.c_str());
    }
}

// --- MQTT Message Handler (Phase 3 Placeholder) ---
void handle_incoming_mqtt_message(const char* topic, const char* payload) {
    Serial.printf("[Main] MQTT Message Received - Topic: %s, Payload: %s\n", topic, payload);
    
    // Check if it's a consultation request for this faculty unit
    // mqtt_request_topic is already formatted for this specific faculty in mqtt_init
    if (String(topic) == mqtt_request_topic) {
        Serial.println("Received a consultation request for this unit.");
        
        // For MVP, we will attempt to parse key fields if they exist for a richer display.
        // A more robust solution would use ArduinoJson for parsing.
        // Simple parsing assuming payload is like: 
        // {"student_name": "Jane Doe", "course_code": "PHY202", "subject": "Black Holes", ...}
        String payload_str = String(payload);
        String student_name = "Unknown Student";
        String course_code = "N/A";
        String subject = "No Subject";
        String details = payload_str; // Default to full payload if parsing fails

        // Basic parsing (prone to errors if format changes, ArduinoJson is better)
        int student_name_idx = payload_str.indexOf("\"student_name\": \"");
        if (student_name_idx != -1) {
            int start = student_name_idx + 18; // length of "\"student_name\": \""
            int end = payload_str.indexOf("\"", start);
            if (end != -1) student_name = payload_str.substring(start, end);
        }

        int subject_idx = payload_str.indexOf("\"subject\": \"");
        if (subject_idx != -1) {
            int start = subject_idx + 13; // length of "\"subject\": \""
            int end = payload_str.indexOf("\"", start);
            if (end != -1) subject = payload_str.substring(start, end);
        }
        
        int course_idx = payload_str.indexOf("\"course_code\": \"");
        if (course_idx != -1) {
            int start = course_idx + 17; // length of "\"course_code\": \""
            int end = payload_str.indexOf("\"", start);
            if (end != -1) course_code = payload_str.substring(start, end);
        }
        
        // Prepare a formatted message for the display
        char display_title[50];
        snprintf(display_title, sizeof(display_title), "Request: %s", subject.c_str());
        
        char display_msg[200];
        snprintf(display_msg, sizeof(display_msg), "From: %s\nCourse: %s\nDetails: %s", 
                 student_name.c_str(), course_code.c_str(), payload_str.c_str()); // Show full payload in details for now
        
        // Display the message. For MVP, it shows one at a time.
        // A list/queue of requests would be a post-MVP improvement.
        display_show_message(display_title, display_msg, 0); // Show indefinitely until next status or message
    } else {
        Serial.printf("Ignoring message on unhandled topic: %s\n", topic);
    }
}

unsigned long last_ble_check_time = 0;
const unsigned long BLE_CHECK_INTERVAL = (BLE_SCAN_DURATION_SECONDS + 1) * 1000; // e.g., 5s scan + 1s buffer

void loop() {
    unsigned long current_time = millis();

    // Handle MQTT connection and incoming messages
    mqtt_loop();

    // Periodically check BLE presence and update status
    if (current_time - last_ble_check_time > BLE_CHECK_INTERVAL) {
        update_presence_and_publish_status();
        last_ble_check_time = current_time;
    }
    
    // Update WiFi/MQTT connection status on display (less frequently)
    static unsigned long last_conn_display_update = 0;
    if(current_time - last_conn_display_update > 2500){ // Update every 2.5s
        update_connection_status_display();
        last_conn_display_update = current_time;
    }

    // Add other non-blocking tasks here if needed
    delay(10); // Small delay to be cooperative
} 