#include "mqtt_module.h"
#include "config.h"
#include "Arduino.h"

WiFiClient espWiFiClient;
PubSubClient mqttClient(espWiFiClient);
mqtt_message_callback_t external_mqtt_callback = nullptr;

char mqtt_status_topic[100];
char mqtt_request_topic[100];
char mqtt_client_id[100];

unsigned long lastReconnectAttempt = 0;

void _callback_wrapper(char* topic, byte* payload, unsigned int length) {
    payload[length] = '\0'; // Null terminate payload
    String topic_str = String(topic);
    String payload_str = String((char*)payload);
    Serial.printf("MQTT Message Arrived - Topic: %s, Payload: %s\n", topic_str.c_str(), payload_str.c_str());

    if (external_mqtt_callback) {
        external_mqtt_callback(topic_str.c_str(), payload_str.c_str());
    }
}

void _connect_wifi() {
    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) { // Try for 10 seconds
        delay(500);
        Serial.print(".");
        attempts++;
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected!");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\nWiFi connection FAILED. Rebooting in 10s to retry...");
        delay(10000);
        ESP.restart();
    }
}

bool _reconnect_mqtt() {
    if (mqttClient.connected()) {
        return true;
    }
    Serial.print("Attempting MQTT connection...");
    Serial.print("Client ID: "); Serial.println(mqtt_client_id);
    Serial.print("Broker: "); Serial.print(MQTT_BROKER_HOST); Serial.print(":"); Serial.println(MQTT_BROKER_PORT);

    if (mqttClient.connect(mqtt_client_id)) {
        Serial.println("MQTT Connected!");
        // Subscribe to topics
        mqttClient.subscribe(mqtt_request_topic);
        Serial.print("Subscribed to: "); Serial.println(mqtt_request_topic);
        // Add other subscriptions if needed (e.g., backward compatibility)
        // mqttClient.subscribe(MQTT_PROFESSOR_MESSAGES_TOPIC);
        return true;
    } else {
        Serial.print("MQTT Connection failed, rc=");
        Serial.print(mqttClient.state());
        Serial.println(" Retrying in 5 seconds...");
        return false;
    }
}

void mqtt_init(const char* unique_client_id_suffix, const char* faculty_ble_id) {
    snprintf(mqtt_client_id, sizeof(mqtt_client_id), "%s%s", MQTT_CLIENT_ID_PREFIX, unique_client_id_suffix);
    snprintf(mqtt_status_topic, sizeof(mqtt_status_topic), MQTT_STATUS_TOPIC_TEMPLATE, faculty_ble_id);
    snprintf(mqtt_request_topic, sizeof(mqtt_request_topic), MQTT_REQUEST_TOPIC_TEMPLATE, faculty_ble_id);

    _connect_wifi();
    mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    mqttClient.setCallback(_callback_wrapper);
    lastReconnectAttempt = 0; // Ensure first connection attempt happens quickly
}

void mqtt_set_callback(mqtt_message_callback_t callback) {
    external_mqtt_callback = callback;
}

void mqtt_loop() {
    if (!mqttClient.connected()) {
        unsigned long now = millis();
        if (now - lastReconnectAttempt > 5000) { // Retry every 5 seconds
            lastReconnectAttempt = now;
            if (_reconnect_mqtt()) {
                lastReconnectAttempt = 0; // Reset timer on successful connect
            }
        }
    } else {
        mqttClient.loop(); // Allow the MQTT client to process incoming messages and maintain connection
    }
}

bool mqtt_is_connected() {
    return mqttClient.connected() && (WiFi.status() == WL_CONNECTED);
}

bool mqtt_publish_status(const char* faculty_ble_id, const char* status_payload) {
    if (!mqtt_is_connected()) {
        Serial.println("MQTT: Cannot publish status, not connected.");
        return false;
    }
    // Construct the specific status topic for this faculty member
    // mqtt_status_topic is already formatted with faculty_ble_id in mqtt_init
    Serial.printf("MQTT: Publishing to %s: %s\n", mqtt_status_topic, status_payload);
    if (mqttClient.publish(mqtt_status_topic, status_payload, true)) { // Retain status
        Serial.println("MQTT: Status published successfully.");
        return true;
    } else {
        Serial.println("MQTT: Status publish FAILED.");
        return false;
    }
} 