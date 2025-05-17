from PyQt5.QtCore import QObject, pyqtSlot
import logging

# Assuming services and views are accessible via package structure
# from ..services import RFIDService, DatabaseService # Adjust if run standalone
# from ..views import AuthenticationScreen # Adjust if run standalone

class AuthenticationController(QObject):
    def __init__(self, rfid_service, db_service, auth_view):
        super().__init__()
        self.rfid_service = rfid_service
        self.db_service = db_service
        self.auth_view = auth_view

        # Connect signals from the view to controller slots
        self.auth_view.request_rfid_scan_start.connect(self.start_rfid_scanning)
        self.auth_view.request_rfid_scan_stop.connect(self.stop_rfid_scanning)

        # Register a callback with the RFIDService
        self.rfid_service.register_rfid_callback(self.handle_rfid_scan)

        logging.info("AuthenticationController initialized.")

    @pyqtSlot()
    def start_rfid_scanning(self):
        logging.info("AuthenticationController: Received request to start RFID scanning.")
        self.rfid_service.start_scanning()
        self.auth_view.set_status_message("Scanning for RFID card...")

    @pyqtSlot()
    def stop_rfid_scanning(self):
        logging.info("AuthenticationController: Received request to stop RFID scanning.")
        self.rfid_service.stop_scanning()

    @pyqtSlot(str)
    def handle_rfid_scan(self, rfid_tag_id: str):
        logging.info(f"AuthenticationController: RFID Tag Scanned: {rfid_tag_id}")
        self.auth_view.set_status_message(f"Processing tag: {rfid_tag_id}...", duration_ms=0) # Display processing message

        try:
            student_data = self.db_service.get_student_by_rfid(rfid_tag_id)
            if student_data:
                logging.info(f"Student found: {student_data['name']}")
                # The view will emit login_successful, which the main app will handle
                self.auth_view._on_login_success(dict(student_data)) 
            else:
                logging.warning(f"No student found for RFID tag: {rfid_tag_id}")
                self.auth_view._on_login_failed("RFID tag not recognized.")
        except Exception as e:
            logging.error(f"Error during RFID validation: {e}")
            self.auth_view._on_login_failed("System error during validation.")

    def cleanup(self):
        """Called when the controller is no longer needed, e.g., before app shutdown."""
        self.stop_rfid_scanning()
        logging.info("AuthenticationController cleaned up.")

# Example of how to connect this (would typically be in your main application setup)
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # For direct testing, we need to import services and views differently
    # This requires central_system to be in PYTHONPATH or running from parent directory
    try:
        from services import RFIDService, DatabaseService
        from views import AuthenticationScreen
    except ImportError:
        # If running directly from controllers directory, adjust path for sibling packages
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Add parent dir (central_system)
        from services import RFIDService, DatabaseService
        from views import AuthenticationScreen

    app = QApplication(sys.argv)

    # Initialize services (ensure DB is running for DatabaseService)
    # For this test, ensure your PostgreSQL is running and configured as per database_service.py
    try:
        db_service_instance = DatabaseService() # This will try to connect & create tables
    except Exception as e:
        print(f"Failed to initialize DatabaseService: {e}")
        print("Ensure PostgreSQL is running and configured correctly.")
        sys.exit(1)
        
    rfid_service_instance = RFIDService(simulation_mode=True)
    
    # Initialize view
    auth_screen_view = AuthenticationScreen()
    
    # Initialize controller
    auth_controller = AuthenticationController(
        rfid_service=rfid_service_instance, 
        db_service=db_service_instance,
        auth_view=auth_screen_view
    )

    auth_screen_view.show() 
    auth_screen_view.view_did_appear() # Manually trigger this as it's normally called by main app logic

    exit_code = app.exec_()
    auth_controller.cleanup() # Clean up controller resources before exiting
    rfid_service_instance.close()
    sys.exit(exit_code) 