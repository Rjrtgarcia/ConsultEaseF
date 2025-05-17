# Main application entry point for Central System

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore import QTimer

# Assuming services, views, and controllers are in the same package structure
from services import DatabaseService, RFIDService, MQTTService
from views import AuthenticationScreen, MainDashboardScreen, AdminDashboardScreen
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
        self.admin_controller = None # Controller for AdminDashboardScreen
        
        self.current_student_data = None

        # Initialize services first
        try:
            self.db_service = DatabaseService()
            logging.info("DatabaseService initialized successfully.")
        except RuntimeError as e:
            logging.critical(f"CRITICAL: Failed to initialize DatabaseService: {e}")
            QMessageBox.critical(self, "Startup Error", f"Failed to connect to the database: {e}\nThe application cannot continue.")
            sys.exit(1) # Critical error, exit
            
        self.rfid_service = RFIDService(simulation_mode=True) 
        logging.info("RFIDService initialized.")

        self.mqtt_service = MQTTService(db_service=self.db_service)
        self.mqtt_service.start()
        logging.info("MQTTService started.")

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize Controllers first that don't take views
        if self.db_service:
            self.admin_controller = AdminController(db_service=self.db_service)
            logging.info("AdminController initialized.")
        else:
            logging.error("AdminController NOT initialized due to DB service failure.")

        # Initialize screens (views)
        self.auth_screen = AuthenticationScreen(parent_stacked_widget=self.stacked_widget)
        self.dashboard_screen = MainDashboardScreen(db_service_getter=lambda: self.db_service, parent_stacked_widget=self.stacked_widget)
        
        # AdminDashboardScreen needs the admin_controller
        if self.admin_controller:
            self.admin_dashboard_screen = AdminDashboardScreen(admin_controller=self.admin_controller)
        else: # Fallback if admin_controller failed (though app would likely exit earlier if DB fails)
            logging.warning("AdminDashboardScreen cannot be fully initialized as AdminController is missing.")
            # Create a placeholder or error-displaying widget if needed
            self.admin_dashboard_screen = QMessageBox(QMessageBox.Critical, "Error", "Admin Panel could not be loaded.")

        # Add screens to the stacked widget
        self.stacked_widget.addWidget(self.auth_screen)
        self.stacked_widget.addWidget(self.dashboard_screen)
        if isinstance(self.admin_dashboard_screen, AdminDashboardScreen): # Only add if initialized correctly
            self.stacked_widget.addWidget(self.admin_dashboard_screen)
        else: # If it's a QMessageBox or placeholder, maybe don't add or handle differently
            pass 

        # Initialize other controllers that take views
        if self.db_service: 
            self.auth_controller = AuthenticationController(
                rfid_service=self.rfid_service, 
                db_service=self.db_service, 
                auth_view=self.auth_screen
            )
            logging.info("AuthenticationController initialized.")

            self.dashboard_controller = DashboardController(
                db_service=self.db_service,
                mqtt_service=self.mqtt_service,
                dashboard_view=self.dashboard_screen
            )
            logging.info("DashboardController initialized.")
        else:
            logging.error("AuthenticationController NOT initialized due to DB service failure.")
            logging.error("DashboardController NOT initialized due to DB service failure.")

        # Connect signals for navigation
        self.auth_screen.login_successful.connect(self.handle_login_success)
        self.dashboard_screen.request_open_admin_panel.connect(self.show_admin_dashboard_screen) # Connect to new method
        # No back signal from admin_dashboard_screen currently defined in its UI

        self.show_authentication_screen()

    def show_authentication_screen(self):
        logging.info("Showing Authentication Screen.")
        current_shown_widget = self.stacked_widget.currentWidget()
        if current_shown_widget == self.dashboard_screen: self.dashboard_screen.view_did_disappear()
        elif hasattr(current_shown_widget, 'view_did_disappear'): # For AdminDashboardScreen or others
             if callable(getattr(current_shown_widget, 'view_did_disappear')):
                current_shown_widget.view_did_disappear()

        self.stacked_widget.setCurrentWidget(self.auth_screen)
        self.auth_screen.view_did_appear()
        self.current_student_data = None

    def show_dashboard_screen(self):
        logging.info("Showing Dashboard Screen.")
        current_shown_widget = self.stacked_widget.currentWidget()
        if current_shown_widget == self.auth_screen: self.auth_screen.view_did_disappear()
        elif hasattr(current_shown_widget, 'view_did_disappear'):
             if callable(getattr(current_shown_widget, 'view_did_disappear')):
                current_shown_widget.view_did_disappear()
        
        self.dashboard_screen.set_student_info(self.current_student_data)
        self.stacked_widget.setCurrentWidget(self.dashboard_screen)
        self.dashboard_screen.view_did_appear()

    def show_admin_dashboard_screen(self):
        if not isinstance(self.admin_dashboard_screen, AdminDashboardScreen):
            QMessageBox.critical(self, "Error", "Admin Panel is not available.")
            return
            
        logging.info("Showing Admin Dashboard Screen.")
        current_shown_widget = self.stacked_widget.currentWidget()
        if current_shown_widget == self.dashboard_screen: self.dashboard_screen.view_did_disappear()
        elif current_shown_widget == self.auth_screen: self.auth_screen.view_did_disappear()
        
        self.stacked_widget.setCurrentWidget(self.admin_dashboard_screen)
        # Assuming AdminDashboardScreen might have a method like view_did_appear to refresh data
        if hasattr(self.admin_dashboard_screen, 'load_all_data') and callable(getattr(self.admin_dashboard_screen, 'load_all_data')):
            self.admin_dashboard_screen.load_all_data() # Refresh data when shown
        if hasattr(self.admin_dashboard_screen, 'view_did_appear') and callable(getattr(self.admin_dashboard_screen, 'view_did_appear')):
            self.admin_dashboard_screen.view_did_appear()

    def handle_login_success(self, student_data):
        logging.info(f"Login successful for student: {student_data.get('name')}")
        self.current_student_data = student_data
        QTimer.singleShot(1500, self.show_dashboard_screen)

    def closeEvent(self, event):
        logging.info("Close event received. Shutting down services...")
        if self.rfid_service: self.rfid_service.close()
        if self.mqtt_service: self.mqtt_service.stop()
        # Controllers might have cleanup, e.g., if they manage threads or external resources
        # if self.auth_controller and hasattr(self.auth_controller, 'cleanup'): self.auth_controller.cleanup()
        # if self.dashboard_controller and hasattr(self.dashboard_controller, 'cleanup'): self.dashboard_controller.cleanup()
        # if self.admin_controller and hasattr(self.admin_controller, 'cleanup'): self.admin_controller.cleanup()
        logging.info("Services shut down. Exiting.")
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = ConsultEaseApp()
    main_app.show() 
    # main_app.resize(1024, 600) # Optional resize for desktop
    sys.exit(app.exec_()) 