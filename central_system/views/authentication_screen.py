import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QStackedWidget
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer

class AuthenticationScreen(QWidget):
    # Signal to indicate successful authentication, carries student data (e.g., name or ID)
    login_successful = pyqtSignal(dict) # dict will contain student info
    # Signal to request RFID scan start/stop
    request_rfid_scan_start = pyqtSignal()
    request_rfid_scan_stop = pyqtSignal()

    def __init__(self, parent_stacked_widget: QStackedWidget = None):
        super().__init__()
        self.parent_stacked_widget = parent_stacked_widget # To switch to main dashboard
        self.setWindowTitle("ConsultEase - Student Authentication")        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        title_label = QLabel("Student RFID Authentication")
        title_font = QFont("Arial", 28, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.status_label = QLabel("Please scan your RFID card.")
        status_font = QFont("Arial", 18)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setFixedHeight(100) # Give it some space for messages
        layout.addWidget(self.status_label)

        # RFID Simulation Input (for testing without a real reader)
        # This part will be primarily controlled by the RFIDService in simulation mode
        self.rfid_simulation_label = QLabel("RFID Simulation (for testing):")
        self.rfid_simulation_label.setFont(QFont("Arial", 10))
        # Initially hidden, controller can show if needed
        # self.rfid_simulation_label.hide()
        # layout.addWidget(self.rfid_simulation_label)

        # self.rfid_input_field = QLineEdit()
        # self.rfid_input_field.setPlaceholderText("Enter simulated RFID tag ID")
        # self.rfid_input_field.setFont(QFont("Arial", 12))
        # self.rfid_input_field.returnPressed.connect(self._handle_simulated_rfid_submit) # For manual entry
        # self.rfid_input_field.hide()
        # layout.addWidget(self.rfid_input_field)

        # self.submit_rfid_button = QPushButton("Simulate Scan")
        # self.submit_rfid_button.setFont(QFont("Arial", 12))
        # self.submit_rfid_button.clicked.connect(self._handle_simulated_rfid_submit)
        # self.submit_rfid_button.hide()
        # layout.addWidget(self.submit_rfid_button)
        
        layout.addStretch(1) # Pushes elements to the top and middle

        self.setLayout(layout)
        self.set_default_status_appearance()

    def set_status_message(self, message, is_error=False, is_success=False, duration_ms=0):
        self.status_label.setText(message)
        palette = self.status_label.palette()
        if is_error:
            palette.setColor(QPalette.WindowText, QColor("red"))
        elif is_success:
            palette.setColor(QPalette.WindowText, QColor("green"))
        else:
            palette.setColor(QPalette.WindowText, QColor("black")) # Default color
        self.status_label.setPalette(palette)

        if duration_ms > 0:
            QTimer.singleShot(duration_ms, self.reset_status_message)
            
    def reset_status_message(self):
        self.set_status_message("Please scan your RFID card.")
        self.set_default_status_appearance()

    def set_default_status_appearance(self):
        palette = self.status_label.palette()
        palette.setColor(QPalette.WindowText, QColor("black"))
        self.status_label.setPalette(palette)

    # This method will be called by the controller upon successful login
    def _on_login_success(self, student_data):
        self.set_status_message(f"Welcome, {student_data.get('name', 'Student')}!", is_success=True)
        # The main app or controller will handle switching to the dashboard.
        # If this screen directly handles it with a parent_stacked_widget:
        # if self.parent_stacked_widget and self.parent_stacked_widget.count() > 1:
        #     QTimer.singleShot(1500, lambda: self.parent_stacked_widget.setCurrentIndex(1)) # Assuming dashboard is at index 1
        # else:
        #     logging.warning("Login successful but no parent_stacked_widget or dashboard to switch to.")
        self.login_successful.emit(student_data) # Emit signal for main app to handle view switching

    # This method will be called by the controller upon failed login
    def _on_login_failed(self, reason="Invalid RFID or system error."):
        self.set_status_message(f"Login Failed: {reason}", is_error=True, duration_ms=3000)

    # def _handle_simulated_rfid_submit(self):
    #     # This would be used if we allowed manual RFID entry for simulation
    #     # For MVP, RFIDService simulation will trigger the scan event directly
    #     rfid_tag = self.rfid_input_field.text().strip()
    #     if rfid_tag and self._rfid_callback_from_controller: # Requires controller to set this callback
    #         self._rfid_callback_from_controller(rfid_tag)
    #     self.rfid_input_field.clear()

    # Call this method when the view is shown to start scanning
    def view_did_appear(self):
        self.reset_status_message()
        self.request_rfid_scan_start.emit()

    # Call this method when the view is hidden to stop scanning
    def view_did_disappear(self):
        self.request_rfid_scan_stop.emit()

    def closeEvent(self, event):
        self.request_rfid_scan_stop.emit() # Ensure scanning stops if window is closed
        super().closeEvent(event)

# Example of how to run this screen standalone (for testing)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    auth_screen = AuthenticationScreen()
    
    # Simulate receiving a scan event after a delay (controller would do this)
    # def mock_scan_handler(tag_id):
    #     print(f"AuthScreen received mock scan: {tag_id}")
    #     if tag_id == "STUDENT_RFID_001":
    #         auth_screen._on_login_success({"name": "Test Student", "id": 1})
    #     else:
    #         auth_screen._on_login_failed("Unknown RFID tag.")
    
    # This is a simplification. In reality, the RFIDService would call the controller,
    # and the controller would call _on_login_success or _on_login_failed.
    # For direct testing, you might temporarily connect a timer to these methods.
    # QTimer.singleShot(3000, lambda: mock_scan_handler("STUDENT_RFID_001"))
    # QTimer.singleShot(6000, lambda: mock_scan_handler("BAD_RFID"))

    auth_screen.show() # For RPi, you might want .showFullScreen()
    auth_screen.view_did_appear() # Manually call for standalone testing
    sys.exit(app.exec_()) 