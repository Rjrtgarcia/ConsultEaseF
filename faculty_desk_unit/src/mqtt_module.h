#ifndef MQTT_MODULE_H
#define MQTT_MODULE_H

#include <WiFi.h>
#include <PubSubClient.h>

// Callback function type for incoming messages
typedef void (*mqtt_message_callback_t)(const char* topic, const char* payload);

void mqtt_init(const char* unique_client_id_suffix, const char* faculty_ble_id);
void mqtt_set_callback(mqtt_message_callback_t callback);
void mqtt_loop(); // Needs to be called regularly to maintain connection and process messages
bool mqtt_is_connected();
bool mqtt_publish_status(const char* faculty_ble_id, const char* status_payload); // payload: "Available" or "Unavailable" or JSON

#endif // MQTT_MODULE_H 