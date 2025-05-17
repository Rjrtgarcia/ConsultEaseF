# Main application entry point for Central System

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore import QTimer

# Assuming services, views, and controllers are in the same package structure
from services import DatabaseService, RFIDService, MQTTService
from views import AuthenticationScreen, MainDashboardScreen, AdminScreen
from controllers import AuthenticationController, DashboardController, AdminController

# Configure basic logging for the main application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - MainApp - %(message)s')

class ConsultEaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ConsultEase Central System")
        # Screen resolution for RPi Touchscreen is 1024x600
        # self.setGeometry(0, 0, 1024, 600) # Set initial size, or use .showFullScreen()
        # self.showFullScreen() # For Raspberry Pi display

        self.db_service = None
        self.rfid_service = None
        self.mqtt_service = None
        self.auth_controller = None
        self.dashboard_controller = None
        self.admin_controller = None
        
        self.current_student_data = None

        # Initialize services first
        try:
            self.db_service = DatabaseService()
            logging.info("DatabaseService initialized successfully.")
        except RuntimeError as e:
            logging.critical(f"CRITICAL: Failed to initialize DatabaseService: {e}")
            QMessageBox.critical(self, "Startup Error", f"Failed to connect to the database: {e}\nThe application cannot continue.")
            # In a real app, you might exit here or disable DB-dependent features
            # For now, allow it to continue to show UI structure, but DB ops will fail.
            sys.exit(1) # Critical error, exit
            
        # RFID Service (using simulation mode for now by default)
        # Change to simulation_mode=False when actual reader is integrated
        self.rfid_service = RFIDService(simulation_mode=True) 
        logging.info("RFIDService initialized.")

        # MQTT Service
        self.mqtt_service = MQTTService(db_service=self.db_service)
        self.mqtt_service.start() # Start the MQTT client thread
        logging.info("MQTTService started.")

        # Central widget to hold different screens
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize screens (views)
        self.auth_screen = AuthenticationScreen(parent_stacked_widget=self.stacked_widget)
        # Pass a lambda to get the db_service, as it might be re-initialized or changed
        self.dashboard_screen = MainDashboardScreen(db_service_getter=lambda: self.db_service, parent_stacked_widget=self.stacked_widget)
        self.admin_screen = AdminScreen(parent_stacked_widget=self.stacked_widget)

        # Add screens to the stacked widget
        self.stacked_widget.addWidget(self.auth_screen)
        self.stacked_widget.addWidget(self.dashboard_screen)
        self.stacked_widget.addWidget(self.admin_screen)

        # Initialize controllers
        if self.db_service: # Only init controller if DB is up
            self.auth_controller = AuthenticationController(
                rfid_service=self.rfid_service, 
                db_service=self.db_service, 
                auth_view=self.auth_screen
            )
            logging.info("AuthenticationController initialized.")

            # Initialize DashboardController - needs db_service, mqtt_service, and dashboard_view
            self.dashboard_controller = DashboardController(
                db_service=self.db_service,
                mqtt_service=self.mqtt_service,
                dashboard_view=self.dashboard_screen
            )
            logging.info("DashboardController initialized.")

            self.admin_controller = AdminController(
                db_service=self.db_service,
                admin_view=self.admin_screen
            )
            logging.info("AdminController initialized.")
        else:
            logging.error("AuthenticationController NOT initialized due to DB service failure.")
            logging.error("DashboardController NOT initialized due to DB service failure.")
            logging.error("AdminController NOT initialized due to DB service failure.")
            # Auth screen will still show, but RFID login won't work.

        # Connect signals for navigation
        self.auth_screen.login_successful.connect(self.handle_login_success)
        self.dashboard_screen.request_open_admin_panel.connect(self.show_admin_screen)
        self.admin_screen.request_admin_logout.connect(self.show_dashboard_screen)
        # self.dashboard_screen.request_logout.connect(self.handle_logout) # Logout for later

        # Start with the authentication screen
        self.show_authentication_screen()

    def show_authentication_screen(self):
        logging.info("Showing Authentication Screen.")
        if self.stacked_widget.currentWidget() == self.dashboard_screen:
            self.dashboard_screen.view_did_disappear()
        self.stacked_widget.setCurrentWidget(self.auth_screen)
        self.auth_screen.view_did_appear()
        self.current_student_data = None # Clear logged-in student

    def show_dashboard_screen(self):
        logging.info("Showing Dashboard Screen.")
        if self.stacked_widget.currentWidget() == self.auth_screen:
            self.auth_screen.view_did_disappear()
        self.dashboard_screen.set_student_info(self.current_student_data)
        self.stacked_widget.setCurrentWidget(self.dashboard_screen)
        self.dashboard_screen.view_did_appear()

    def show_admin_screen(self):
        logging.info("Showing Admin Screen.")
        if self.stacked_widget.currentWidget() == self.dashboard_screen:
            self.dashboard_screen.view_did_disappear()
        elif self.stacked_widget.currentWidget() == self.auth_screen:
            self.auth_screen.view_did_disappear()
        
        self.stacked_widget.setCurrentWidget(self.admin_screen)
        self.admin_screen.view_did_appear()

    def handle_login_success(self, student_data):
        logging.info(f"Login successful for student: {student_data.get('name')}")
        self.current_student_data = student_data
        # Add a small delay before switching to make success message visible
        QTimer.singleShot(1500, self.show_dashboard_screen)

    def closeEvent(self, event):
        logging.info("Close event received. Shutting down services...")
        if self.rfid_service:
            self.rfid_service.close()
        if self.mqtt_service:
            self.mqtt_service.stop()
        if self.auth_controller:
            self.auth_controller.cleanup()
        if self.dashboard_controller:
            self.dashboard_controller.cleanup()
        if self.admin_controller:
            self.admin_controller.cleanup()
        logging.info("Services shut down. Exiting.")
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = ConsultEaseApp()
    # For Raspberry Pi, uncomment the line below for true full screen
    # main_app.showFullScreen() 
    main_app.show() # Normal window for testing on desktop
    
    # Set initial geometry (optional, showFullScreen is better for RPi)
    # desired_width = 1024
    # desired_height = 600
    # main_app.resize(desired_width, desired_height)

    sys.exit(app.exec_()) 