from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QMessageBox
import logging
from datetime import datetime

class DashboardController(QObject):
    def __init__(self, db_service, mqtt_service, dashboard_view):
        super().__init__()
        self.db_service = db_service
        self.mqtt_service = mqtt_service
        self.dashboard_view = dashboard_view

        # Connect signals from the view
        self.dashboard_view.submit_consultation_request.connect(self.handle_submit_consultation_request)
        # self.dashboard_view.request_faculty_data_refresh.connect(self.refresh_faculty_data_on_view)
        # self.dashboard_view.request_logout.connect(...) # Main app will handle logout

        logging.info("DashboardController initialized.")

    @pyqtSlot(dict)
    def handle_submit_consultation_request(self, request_data: dict):
        logging.info(f"DashboardController: Received consultation request submission: {request_data}")
        
        student_id = request_data.get("student_id")
        faculty_id = request_data.get("faculty_id")
        faculty_ble_id = request_data.get("faculty_ble_identifier")
        course_code = request_data.get("course_code")
        subject = request_data.get("subject")
        details = request_data.get("details")
        student_name = request_data.get("student_name") # For MQTT payload

        if not all([student_id, faculty_id, faculty_ble_id, subject]):
            logging.error("DashboardController: Missing critical data for consultation request.")
            self.dashboard_view.set_request_status_message("Error: Missing required information.", is_error=True)
            return

        try:
            # 1. Save to database
            db_record = self.db_service.add_consultation_request(
                student_id=student_id,
                faculty_id=faculty_id,
                course_code=course_code,
                subject=subject,
                request_details=details
            )

            if not db_record:
                logging.error("DashboardController: Failed to save consultation request to DB.")
                self.dashboard_view.set_request_status_message("Error: Could not save request.", is_error=True)
                return

            logging.info(f"DashboardController: Consultation request saved to DB. ID: {db_record['consultation_id']}")

            # 2. Prepare payload for MQTT
            mqtt_payload = {
                "consultation_id": db_record['consultation_id'],
                "student_name": student_name,
                "student_id": student_id,
                "course_code": course_code,
                "subject": subject,
                "request_details": details,
                "requested_at": db_record['requested_at'].isoformat() # Use timestamp from DB
            }

            # 3. Publish via MQTT
            if self.mqtt_service.publish_consultation_request(faculty_ble_identifier=faculty_ble_id, request_payload=mqtt_payload):
                logging.info(f"DashboardController: Consultation request published via MQTT to faculty BLE ID {faculty_ble_id}.")
                self.dashboard_view.set_request_status_message("Request submitted successfully!", is_error=False, duration_ms=5000)
                self.dashboard_view.clear_request_form() # Clear form on success
            else:
                logging.error("DashboardController: Failed to publish consultation request via MQTT.")
                # Note: Request is in DB, but not sent. Might need a retry mechanism or admin alert later.
                self.dashboard_view.set_request_status_message("Error: Request saved but failed to send to faculty.", is_error=True, duration_ms=7000)

        except Exception as e:
            logging.error(f"DashboardController: Exception during consultation submission: {e}")
            self.dashboard_view.set_request_status_message(f"Error: {e}", is_error=True)

    # def refresh_faculty_data_on_view(self):
    #     # This could be a slot if the view emits a signal for explicit refresh
    #     # For now, the view's internal timer and refresh button handle it.
    #     self.dashboard_view.load_faculty_data()
    #     logging.info("DashboardController: Faculty data refresh triggered for view.")

    def cleanup(self):
        logging.info("DashboardController cleaned up.")

# Example of how this might be integrated (in main_app.py)
if __name__ == '__main__':
    # This is a simplified test setup
    # In a real app, services would be initialized once by the main application.
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication([]) # Dummy app for testing signals/slots if needed

    class MockDB:
        def add_consultation_request(self, **kwargs):
            print(f"MockDB: add_consultation_request called with {kwargs}")
            return {**kwargs, "consultation_id": 123, "requested_at": datetime.now(), "status": "Pending"}
    class MockMQTT:
        def publish_consultation_request(self, faculty_ble_identifier, request_payload):
            print(f"MockMQTT: publish_consultation_request to {faculty_ble_identifier} with {request_payload}")
            return True # Simulate success
    class MockDashboardView(QObject):
        submit_consultation_request = pyqtSignal(dict)
        def set_request_status_message(self, msg, is_error, duration_ms=0):
            print(f"MockView: Status: {msg} (Error: {is_error}, Duration: {duration_ms})")
        def clear_request_form(self):
            print("MockView: Cleared request form.")

    db_m = MockDB()
    mqtt_m = MockMQTT()
    view_m = MockDashboardView()

    controller = DashboardController(db_service=db_m, mqtt_service=mqtt_m, dashboard_view=view_m)
    
    print("\nSimulating consultation request submission...")
    test_data = {
        "student_id": 1,
        "faculty_id": 10,
        "faculty_ble_identifier": "BLE_PROF_XYZ", 
        "student_name": "Test Student",
        "course_code": "PY101",
        "subject": "Need help with loops",
        "details": "My for loop is not working as expected."
    }
    # In real app, this signal would be emitted by the view itself
    view_m.submit_consultation_request.emit(test_data)
    
    controller.cleanup()
    print("\nDashboardController test finished.") 