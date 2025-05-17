import paho.mqtt.client as mqtt
import logging
import json
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
MQTT_BROKER_HOST = "localhost" # Assuming Mosquitto is running on the same RPi
MQTT_BROKER_PORT = 1883
MQTT_KEEPALIVE = 60

# Topic for faculty status updates (ESP32s will publish here)
# Using a wildcard for faculty_id for subscription
FACULTY_STATUS_TOPIC_TEMPLATE = "consultease/faculty/{}/status"
FACULTY_STATUS_TOPIC_WILDCARD = "consultease/faculty/+/status"

# Topic for consultation requests (Central system will publish here)
CONSULTATION_REQUEST_TOPIC_TEMPLATE = "consultease/faculty/{}/requests"

class MQTTService(threading.Thread):
    def __init__(self, db_service, client_id="ConsultEase_CentralSystem"):
        super().__init__(daemon=True)
        self.client = mqtt.Client(client_id=client_id)
        self.db_service = db_service # To update faculty status in DB
        self._is_connected = False
        self._stop_event = threading.Event()

        # Assign callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish # Optional: for confirming publishes
        self.client.on_log = self._on_log # Optional: for detailed MQTT logging

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info(f"MQTTService: Connected successfully to broker {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            self._is_connected = True
            # Subscribe to topics upon successful connection
            client.subscribe(FACULTY_STATUS_TOPIC_WILDCARD)
            logging.info(f"MQTTService: Subscribed to {FACULTY_STATUS_TOPIC_WILDCARD}")
            # Add other subscriptions if needed
        else:
            logging.error(f"MQTTService: Connection failed with code {rc}. Check broker and network.")
            self._is_connected = False

    def _on_disconnect(self, client, userdata, rc):
        logging.warning(f"MQTTService: Disconnected from MQTT broker with result code {rc}. Will attempt to reconnect.")
        self._is_connected = False
        # Reconnection logic is handled by the loop method or an external monitor

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_str = msg.payload.decode('utf-8')
        logging.info(f"MQTTService: Message received on topic '{topic}': {payload_str}")

        if topic.startswith("consultease/faculty/") and topic.endswith("/status"):
            try:
                # Extract faculty BLE identifier or ID from topic if needed, or expect it in payload
                # For FACULTY_STATUS_TOPIC_WILDCARD = "consultease/faculty/+/status"
                # The part represented by "+" is the faculty's BLE identifier or a unique ID used in the topic
                topic_parts = topic.split('/')
                if len(topic_parts) == 4 and topic_parts[0] == "consultease" and topic_parts[1] == "faculty" and topic_parts[3] == "status":
                    ble_identifier = topic_parts[2]
                    # Payload could be simple string "Available"/"Unavailable" or JSON
                    # For MVP, let's assume simple string or simple JSON like {"status": "Available"}
                    status_data = payload_str
                    new_status = ""
                    try:
                        data = json.loads(payload_str)
                        new_status = data.get("status")
                    except json.JSONDecodeError:
                        # Assume plain text if JSON parsing fails
                        if payload_str.lower() in ["available", "present"]:
                            new_status = "Available"
                        elif payload_str.lower() in ["unavailable", "absent"]:
                            new_status = "Unavailable"
                        else:
                            logging.warning(f"MQTTService: Unknown status format/value '{payload_str}' from {ble_identifier}")
                            return

                    if new_status and self.db_service:
                        logging.info(f"MQTTService: Updating status for faculty (BLE: {ble_identifier}) to '{new_status}'")
                        updated_faculty = self.db_service.update_faculty_status_by_ble_id(ble_identifier, new_status)
                        if updated_faculty:
                            logging.info(f"MQTTService: DB status updated for {updated_faculty.get('name')}.")
                            # Here you could emit a signal if UI needs live update beyond DB polling
                        else:
                            logging.warning(f"MQTTService: Failed to update status in DB for BLE {ble_identifier}.")
                    elif not new_status:
                        logging.warning(f"MQTTService: Parsed empty status from payload: {payload_str}")
                else:
                    logging.warning(f"MQTTService: Received status message on unexpected topic structure: {topic}")

            except Exception as e:
                logging.error(f"MQTTService: Error processing faculty status message: {e}")
        else:
            logging.warning(f"MQTTService: Received message on unhandled topic: {topic}")

    def _on_publish(self, client, userdata, mid):
        logging.debug(f"MQTTService: Message Published (mid: {mid})")

    def _on_log(self, client, userdata, level, buf):
        # Be cautious with log level, MQTT can be very verbose
        if level <= mqtt.MQTT_LOG_WARNING: # Log warnings and errors from Paho client
            logging.log(logging.INFO if level == mqtt.MQTT_LOG_INFO else logging.WARNING if level == mqtt.MQTT_LOG_WARNING else logging.DEBUG, f"PAHO-MQTT: {buf}")

    def publish_message(self, topic, payload, qos=1, retain=False):
        if not self._is_connected:
            logging.error("MQTTService: Cannot publish, not connected to broker.")
            return False
        try:
            if not isinstance(payload, str):
                payload_str = json.dumps(payload) # Assume JSON if not string
            else:
                payload_str = payload
            
            result = self.client.publish(topic, payload_str, qos=qos, retain=retain)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"MQTTService: Message published to topic '{topic}': {payload_str}")
                return True
            else:
                logging.error(f"MQTTService: Failed to publish message to '{topic}'. RC: {result.rc}")
                return False
        except Exception as e:
            logging.error(f"MQTTService: Exception during publish: {e}")
            return False

    def publish_consultation_request(self, faculty_ble_identifier: str, request_payload: dict):
        if not faculty_ble_identifier:
            logging.error("MQTTService: Cannot publish consultation request, faculty BLE identifier is missing.")
            return False
            
        topic = CONSULTATION_REQUEST_TOPIC_TEMPLATE.format(faculty_ble_identifier)
        # request_payload should be a dict, will be converted to JSON string by publish_message
        # Ensure it contains student_name, course_code, subject, details, timestamp for the ESP32
        # e.g., {"student_name": "John Doe", "course": "CS101", "subject": "Help!", "details": "...", "timestamp": "2023-01-01T12:00:00"}
        return self.publish_message(topic, request_payload, qos=1) # QoS 1 for some reliability

    def run(self):
        logging.info("MQTTService: Starting connection attempts...")
        while not self._stop_event.is_set():
            if not self._is_connected:
                try:
                    self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
                    self.client.loop_start() # Starts a background thread for network traffic, callbacks
                    logging.info("MQTTService: loop_start() called. Waiting for connection...")
                    # Wait for on_connect to set self._is_connected or timeout
                    connect_timeout = 10 # seconds
                    wait_start = time.time()
                    while not self._is_connected and (time.time() - wait_start < connect_timeout) and not self._stop_event.is_set():
                        time.sleep(0.1)
                    
                    if not self._is_connected and not self._stop_event.is_set():
                        logging.warning(f"MQTTService: Connection attempt timed out after {connect_timeout}s. Retrying soon.")
                        self.client.loop_stop(force=True) # Stop if connect didn't establish fully

                except ConnectionRefusedError:
                    logging.error(f"MQTTService: Connection refused by broker {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}. Retrying in 5s.")
                except OSError as e: # Catches [Errno 113] No route to host etc.
                    logging.error(f"MQTTService: OS error connecting to broker: {e}. Retrying in 5s.")
                except Exception as e:
                    logging.error(f"MQTTService: Unexpected error during connection: {e}. Retrying in 5s.")
                
                if not self._is_connected: # If connection failed, wait before retry
                    self._stop_event.wait(5) # Wait 5 seconds or until stop_event is set
            else:
                # If connected, just sleep a bit to allow stop_event checking
                self._stop_event.wait(1)
        
        # Cleanup when thread is stopping
        if self._is_connected:
            self.client.loop_stop() # Stop the network loop
            self.client.disconnect()
            logging.info("MQTTService: Disconnected and loop stopped.")
        logging.info("MQTTService thread finished.")

    def stop(self):
        logging.info("MQTTService: Received stop signal.")
        self._stop_event.set()
        if self.is_alive():
            self.join(timeout=5) # Wait for the thread to finish
        if self.client and self._is_connected:
             self.client.loop_stop(force=True) # Ensure loop is stopped
             self.client.disconnect() # Ensure disconnected
        logging.info("MQTTService fully stopped.")

    def is_connected(self):
        return self._is_connected

# Example Usage
if __name__ == '__main__':
    print("Testing MQTTService...")
    # For this test, you need an MQTT broker (like Mosquitto) running on localhost.
    # You also need a DatabaseService instance for the MQTTService to use.

    # --- Mock DatabaseService for testing MQTTService standalone ---
    class MockDBService:
        def update_faculty_status_by_ble_id(self, ble_identifier, new_status):
            print(f"[MockDBService] Updating status for BLE ID {ble_identifier} to {new_status}")
            if ble_identifier == "KNOWN_BLE_ID":
                return {"name": "Dr. Mock Prof", "ble_identifier": ble_identifier, "current_status": new_status}
            return None
    
    mock_db = MockDBService()
    mqtt_service = MQTTService(db_service=mock_db)
    mqtt_service.start() # Starts the connection loop in a new thread

    try:
        print("MQTTService started. Waiting for connection and messages...")
        print(f"Publish to '{FACULTY_STATUS_TOPIC_TEMPLATE.format("YOUR_FACULTY_BLE_ID")}' with payload 'Available' or '{{\"status\": \"Unavailable\"}}'")
        print(f"Example: mosquitto_pub -h {MQTT_BROKER_HOST} -t consultease/faculty/TEST_BLE_001/status -m \"{{\\\"status\\\": \\\"Available\\\"}}\"")
        
        # Keep main thread alive to observe logs and allow MQTT thread to run
        while not mqtt_service.is_connected():
            print("Waiting for MQTT connection...")
            time.sleep(1)
            if not mqtt_service.is_alive():
                print("MQTT service thread unexpectedly died.")
                break
        
        if mqtt_service.is_connected():
            print("MQTT Service connected. Ready to receive messages.")
            # Example publish from the service itself (usually done by other parts of app)
            # mqtt_service.publish_message("consultease/system/test", "Hello from MQTTService test!")
        
        count = 0
        while count < 30 and mqtt_service.is_alive(): # Run for 30 seconds or until thread dies
            time.sleep(1)
            count += 1
            if count % 10 == 0 and mqtt_service.is_connected():
                 mqtt_service.publish_message("consultease/system/heartbeat", f"Test heartbeat {count//10}")

    except KeyboardInterrupt:
        print("Test interrupted by user.")
    finally:
        print("Stopping MQTTService...")
        mqtt_service.stop()
        print("MQTTService test finished.") 