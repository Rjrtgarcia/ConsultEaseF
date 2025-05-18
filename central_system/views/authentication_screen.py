import sys
import os # For path joining
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QPalette # QPixmap could be used for an actual logo
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

# NU Color Palette (kept for dynamic styling if needed, e.g. status label)
NU_BLUE = "#003DA7"
NU_GOLD = "#FDB813"
# LIGHT_GRAY_BG = "#F8F9FA" # Now in QSS
# WHITE_BG = "#FFFFFF" # Now in QSS
DARK_GRAY_TEXT = "#34495E"
MEDIUM_GRAY_TEXT = "#566573"
# LIGHT_GRAY_TEXT = "#AAB7B8" # Now in QSS
STATUS_GREEN = "#2ECC71"
STATUS_RED = "#E74C3C"

class AuthenticationScreen(QWidget):
    # Signal to indicate successful authentication, carries student data (e.g., name or ID)
    login_successful = pyqtSignal(dict) # dict will contain student info
    # Signal to request RFID scan start/stop
    request_rfid_scan_start = pyqtSignal()
    request_rfid_scan_stop = pyqtSignal()
    request_open_admin_panel = pyqtSignal() # New signal for admin panel

    def __init__(self, parent=None): # Removed parent_stacked_widget as it's not used
        super().__init__(parent)
        self.setWindowTitle("ConsultEase - Student Authentication")
        self._init_ui()
        self._load_and_apply_styles() # Load QSS from file

    def _init_ui(self):
        # Main layout for the entire screen (centers the content panel)
        screen_layout = QHBoxLayout(self)
        screen_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Central Content Panel
        self.content_panel = QFrame(self)
        self.content_panel.setObjectName("contentPanel")
        self.content_panel.setFixedWidth(500) # Adjusted width
        self.content_panel.setFixedHeight(400) # Adjusted height
        
        panel_layout = QVBoxLayout(self.content_panel)
        panel_layout.setContentsMargins(30, 30, 30, 30) # Padding inside the panel
        panel_layout.setSpacing(15) # Spacing between elements in the panel
        panel_layout.setAlignment(Qt.AlignCenter)

        # 1. Application Title & University Name
        app_title_label = QLabel("ConsultEase")
        app_title_label.setObjectName("appTitleLabel")
        app_title_label.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(app_title_label)

        uni_name_label = QLabel("National University")
        uni_name_label.setObjectName("uniNameLabel")
        uni_name_label.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(uni_name_label)

        panel_layout.addSpacing(20) # Extra space

        # 2. Main Prompt Text
        prompt_label = QLabel("Welcome! Please scan your Student ID.")
        prompt_label.setObjectName("promptLabel")
        prompt_label.setAlignment(Qt.AlignCenter)
        prompt_label.setWordWrap(True)
        panel_layout.addWidget(prompt_label)

        # 3. RFID "Input" Area / Visualizer
        self.rfid_visualizer = QFrame()
        self.rfid_visualizer.setObjectName("rfidVisualizer")
        self.rfid_visualizer.setFixedSize(200, 100) # Adjusted size
        # Potentially add an icon or placeholder text inside visualizer using another layout
        rfid_visualizer_layout = QVBoxLayout(self.rfid_visualizer)
        rfid_visualizer_layout.setAlignment(Qt.AlignCenter)
        # For now, it's just a styled frame. An icon can be added here later.
        # Example: self.rfid_icon_label = QLabel(); self.rfid_icon_label.setPixmap(...)
        # rfid_visualizer_layout.addWidget(self.rfid_icon_label)
        self.rfid_placeholder_label = QLabel("Awaiting RFID Scan...")
        self.rfid_placeholder_label.setObjectName("rfidPlaceholderLabel")
        self.rfid_placeholder_label.setAlignment(Qt.AlignCenter)
        rfid_visualizer_layout.addWidget(self.rfid_placeholder_label)

        panel_layout.addWidget(self.rfid_visualizer, 0, Qt.AlignCenter)
        
        panel_layout.addSpacing(10)

        # 4. Status Message Label
        self.status_label = QLabel("Please scan your RFID card.") # Default message
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setFixedHeight(50) # Adjust height for 2 lines
        panel_layout.addWidget(self.status_label)

        panel_layout.addStretch(1) # Pushes admin button to bottom of panel

        # 5. Admin Panel Access Button
        self.admin_panel_button = QPushButton("Administrator Login")
        self.admin_panel_button.setObjectName("adminPanelButton")
        self.admin_panel_button.clicked.connect(self._handle_open_admin_panel)
        self.admin_panel_button.setMinimumHeight(40) # Make button taller
        panel_layout.addWidget(self.admin_panel_button)

        screen_layout.addWidget(self.content_panel)
        screen_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.setLayout(screen_layout)

    def _load_and_apply_styles(self):
        # Construct path to QSS file relative to this script
        # Assumes styles/auth_style.qss is in the same directory as this script's parent (views/)
        # For robustness, consider absolute paths or a resource system if structure changes
        style_file_path = os.path.join(os.path.dirname(__file__), "styles", "auth_style.qss")
        try:
            with open(style_file_path, "r") as f:
                style_sheet = f.read()
                self.setStyleSheet(style_sheet)
        except FileNotFoundError:
            print(f"ERROR: Stylesheet not found at {style_file_path}")
        except Exception as e:
            print(f"ERROR: Could not load stylesheet: {e}")

    def set_status_message(self, message, is_error=False, is_success=False, duration_ms=0):
        self.status_label.setText(message)
        # Dynamic styling for status label text color (QSS can set font size/weight)
        if is_error:
            self.status_label.setStyleSheet(f"color: {STATUS_RED}; font-size: 11pt; font-weight: bold;")
        elif is_success:
            self.status_label.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 11pt; font-weight: bold;")
        else: # Default / prompt
            # Re-apply base style from QSS if specific style was set, or set default color
            # For simplicity, just setting color here. More complex scenarios might re-apply objectName specific QSS.
            self.status_label.setStyleSheet(f"color: {MEDIUM_GRAY_TEXT}; font-size: 11pt;")

        if duration_ms > 0:
            QTimer.singleShot(duration_ms, self.reset_status_message)
            
    def reset_status_message(self):
        self.set_status_message("Please scan your RFID card.")

    # This method will be called by the controller upon successful login
    def _on_login_success(self, student_data):
        self.set_status_message(f"Authenticated as {student_data.get('name', 'Student')}. Redirecting...", is_success=True, duration_ms=2000)
        # Emit signal for main app/controller to handle view switching
        # Adding a slight delay before emitting to allow user to see success message.
        QTimer.singleShot(1000, lambda: self.login_successful.emit(student_data))

    # This method will be called by the controller upon failed login
    def _on_login_failed(self, reason="Unknown RFID or system error."):
        self.set_status_message(f"Authentication Failed: {reason}", is_error=True, duration_ms=3000)

    # Call this method when the view is shown to start scanning
    def view_did_appear(self):
        self.reset_status_message()
        self.request_rfid_scan_start.emit()

    # Call this method when the view is hidden to stop scanning
    def view_did_disappear(self):
        self.request_rfid_scan_stop.emit()

    def _handle_open_admin_panel(self):
        self.request_open_admin_panel.emit()

    def closeEvent(self, event):
        self.request_rfid_scan_stop.emit() # Ensure scanning stops if window is closed
        super().closeEvent(event)

# Example of how to run this screen standalone (for testing)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # It's good practice to ensure a QCoreApplication instance exists before QFont
    # if not QApplication.instance():
    #     app = QApplication(sys.argv)
    # else:
    #     app = QApplication.instance()

    auth_screen = AuthenticationScreen()
    auth_screen.setMinimumSize(800, 600) # Simulate a decent window size
    auth_screen.show()
    auth_screen.view_did_appear() # Manually call for standalone testing

    # --- Mocking controller interactions for testing UI states ---
    def test_ui_states():
        # Test success state
        QTimer.singleShot(3000, lambda: auth_screen._on_login_success({"name": "Juan dela Cruz"}))
        # Test failure state after reset
        QTimer.singleShot(7000, lambda: auth_screen._on_login_failed("Invalid RFID Tag."))
        # Test another prompt
        QTimer.singleShot(11000, lambda: auth_screen.reset_status_message())

    test_ui_states()
    # --- End Mocking ---

    sys.exit(app.exec_()) 