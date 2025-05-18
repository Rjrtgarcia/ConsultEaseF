import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox, QDialog, QScrollArea, QFrame,
    QSizePolicy, QGridLayout, QTextEdit, QSpacerItem, QMessageBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

# NU Color Palette (for dynamic parts if needed)
NU_BLUE = "#003DA7"
NU_GOLD = "#FDB813"
STATUS_GREEN = "#2ECC71"
STATUS_RED = "#E74C3C"
STATUS_ORANGE = "#F39C12"
STATUS_GRAY = "#95A5A6"
DARK_GRAY_TEXT = "#34495E"
MEDIUM_GRAY_TEXT = "#566573"

# Placeholder for where faculty data will come from (controller/service)
# from ..services import DatabaseService # For direct testing or if controller passes it

# --- Consultation Request Dialog --- 
class ConsultationRequestDialog(QDialog):
    submit_consultation_request_data = pyqtSignal(dict)

    def __init__(self, faculty_data, student_id, student_name, parent=None):
        super().__init__(parent)
        self.faculty_data = faculty_data
        self.student_id = student_id
        self.student_name = student_name
        
        self.setWindowTitle("Request Consultation")
        self.setObjectName("consultationRequestDialog") # For QSS
        self.setModal(True)
        self.setMinimumWidth(450)
        self._init_dialog_ui()

    def _init_dialog_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        group_box = QGroupBox(f"Requesting with: {self.faculty_data.get('name', 'N/A')}")
        group_box_layout = QVBoxLayout(group_box)

        form_layout = QGridLayout()
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Course Code (Optional):"), 0, 0)
        self.course_code_input = QLineEdit()
        self.course_code_input.setPlaceholderText("e.g., CS101")
        form_layout.addWidget(self.course_code_input, 0, 1)

        form_layout.addWidget(QLabel("Subject/Brief Reason:"), 1, 0)
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("e.g., Help with Assignment 2")
        form_layout.addWidget(self.subject_input, 1, 1)

        form_layout.addWidget(QLabel("Details (Optional):"), 2, 0, Qt.AlignTop)
        self.details_input = QTextEdit()
        self.details_input.setPlaceholderText("More details about your query...")
        self.details_input.setFixedHeight(80)
        form_layout.addWidget(self.details_input, 2, 1)
        
        group_box_layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelModalButton")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.submit_button = QPushButton("Submit Request")
        self.submit_button.setObjectName("submitModalButton")
        self.submit_button.clicked.connect(self._handle_submit)
        button_layout.addWidget(self.submit_button)
        group_box_layout.addLayout(button_layout)
        
        main_layout.addWidget(group_box)
        self.setLayout(main_layout)

    def _handle_submit(self):
        if not self.student_id:
            QMessageBox.warning(self, "Login Error", "Cannot submit request. Student not logged in properly.")
            return
        if not self.faculty_data or 'faculty_id' not in self.faculty_data:
            QMessageBox.warning(self, "Faculty Error", "Faculty data is missing.")
            return

        course_code = self.course_code_input.text().strip()
        subject = self.subject_input.text().strip()
        details = self.details_input.toPlainText().strip()

        if not subject:
            QMessageBox.warning(self, "Input Error", "Please enter a subject for your consultation request.")
            self.subject_input.setFocus()
            return

        request_data = {
            "student_id": self.student_id,
            "faculty_id": self.faculty_data['faculty_id'],
            "faculty_ble_identifier": self.faculty_data.get('ble_identifier', ''),
            "student_name": self.student_name,
            "course_code": course_code,
            "subject": subject,
            "details": details
        }
        self.submit_consultation_request_data.emit(request_data)
        self.accept() # Close dialog

# --- Main Dashboard Screen --- 
class MainDashboardScreen(QWidget):
    # Signals for UI interactions that need controller logic
    request_logout = pyqtSignal()
    request_faculty_data_refresh = pyqtSignal()
    request_open_admin_panel = pyqtSignal()

    def __init__(self, db_service_getter, parent_stacked_widget: QStackedWidget = None):
        super().__init__()
        self.parent_stacked_widget = parent_stacked_widget
        self.db_service_getter = db_service_getter # Function to get current DB service instance
        self.current_student_data = None # To store logged-in student info
        self.faculty_cards = [] # To keep references if needed

        self.setWindowTitle("ConsultEase - Main Dashboard")
        self.init_ui()
        
        # Timer for periodic refresh of faculty availability
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_faculty_data) # Or connect to a controller method
        self.refresh_interval_ms = 10000 # Refresh every 10 seconds, adjust as needed

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header Area
        header_layout = QHBoxLayout()
        self.welcome_label = QLabel("Welcome, Student!") # Will be updated
        self.welcome_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(self.welcome_label)
        header_layout.addStretch(1)

        admin_button = QPushButton("Admin Panel")
        admin_button.setFont(QFont("Arial", 10))
        admin_button.setFixedWidth(120)
        admin_button.clicked.connect(lambda: self.request_open_admin_panel.emit())
        header_layout.addWidget(admin_button)

        # logout_button = QPushButton("Logout")
        # logout_button.setFont(QFont("Arial", 10))
        # logout_button.setFixedWidth(100)
        # logout_button.clicked.connect(self._handle_logout)
        # header_layout.addWidget(logout_button)
        # main_layout.addLayout(header_layout)

        # --- Faculty Availability Panel ---
        faculty_group = QGroupBox("Faculty Availability")
        faculty_group.setFont(QFont("Arial", 14, QFont.Bold))
        faculty_layout = QVBoxLayout()

        # Filters (Basic for MVP)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search Name:"))
        self.faculty_name_search_input = QLineEdit()
        self.faculty_name_search_input.setPlaceholderText("Enter faculty name...")
        self.faculty_name_search_input.setFont(QFont("Arial", 10))
        self.faculty_name_search_input.textChanged.connect(self.load_faculty_data) # Trigger refresh on text change
        filter_layout.addWidget(self.faculty_name_search_input)

        filter_layout.addWidget(QLabel("  Department:"))
        self.dept_filter_combo = QComboBox()
        self.dept_filter_combo.setFont(QFont("Arial", 10))
        self.dept_filter_combo.addItem("All Departments") # Populate with actual departments later
        self.dept_filter_combo.currentTextChanged.connect(self.load_faculty_data)
        filter_layout.addWidget(self.dept_filter_combo)
        
        filter_layout.addWidget(QLabel("  Status:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.setFont(QFont("Arial", 10))
        self.status_filter_combo.addItems(["All Statuses", "Available", "Unavailable"])
        self.status_filter_combo.currentTextChanged.connect(self.load_faculty_data)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addStretch(1)
        refresh_button = QPushButton("Refresh List")
        refresh_button.setFont(QFont("Arial", 10))
        refresh_button.clicked.connect(self.load_faculty_data)
        filter_layout.addWidget(refresh_button)
        faculty_layout.addLayout(filter_layout)

        self.faculty_table = QTableWidget()
        self.faculty_table.setFont(QFont("Arial", 11))
        self.faculty_table.setColumnCount(4) # Name, Department, Office, Status
        self.faculty_table.setHorizontalHeaderLabels(["Name", "Department", "Office", "Status"])
        self.faculty_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.faculty_table.horizontalHeader().setFont(QFont("Arial", 12, QFont.Bold))
        self.faculty_table.setEditTriggers(QTableWidget.NoEditTriggers) # Read-only
        self.faculty_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.faculty_table.setAlternatingRowColors(True)
        self.faculty_table.itemDoubleClicked.connect(self._handle_faculty_selection_for_request)
        faculty_layout.addWidget(self.faculty_table)
        faculty_group.setLayout(faculty_layout)
        main_layout.addWidget(faculty_group)

        # --- Consultation Request Interface ---
        consultation_group = QGroupBox("Request Consultation")
        consultation_group.setFont(QFont("Arial", 14, QFont.Bold))
        consult_form_layout = QVBoxLayout()

        self.selected_faculty_label = QLabel("Selected Faculty: None (Double-click a faculty member from the list above)")
        self.selected_faculty_label.setFont(QFont("Arial", 11, QFont.StyleItalic))
        self.selected_faculty_label.setWordWrap(True)
        consult_form_layout.addWidget(self.selected_faculty_label)

        form_fields_layout = QHBoxLayout()
        course_code_layout = QVBoxLayout()
        course_code_layout.addWidget(QLabel("Course Code (Optional):"))
        self.course_code_input = QLineEdit()
        self.course_code_input.setFont(QFont("Arial", 11))
        self.course_code_input.setPlaceholderText("e.g., CS101")
        course_code_layout.addWidget(self.course_code_input)
        form_fields_layout.addLayout(course_code_layout)

        subject_layout = QVBoxLayout()
        subject_layout.addWidget(QLabel("Subject/Brief Reason:"))
        self.subject_input = QLineEdit()
        self.subject_input.setFont(QFont("Arial", 11))
        self.subject_input.setPlaceholderText("e.g., Help with Assignment 2")
        subject_layout.addWidget(self.subject_input)
        form_fields_layout.addLayout(subject_layout)
        consult_form_layout.addLayout(form_fields_layout)

        consult_form_layout.addWidget(QLabel("Details (Optional):"))
        self.details_input = QLineEdit() # Changed to QLineEdit for simplicity, use QTextEdit for multi-line
        self.details_input.setFont(QFont("Arial", 11))
        self.details_input.setPlaceholderText("More details about your query...")
        # self.details_input.setFixedHeight(80) # For QTextEdit
        consult_form_layout.addWidget(self.details_input)

        self.submit_request_button = QPushButton("Submit Consultation Request")
        self.submit_request_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.submit_request_button.clicked.connect(self._handle_submit_request_button)
        self.submit_request_button.setEnabled(False) # Disabled until faculty is selected
        consult_form_layout.addWidget(self.submit_request_button)
        
        self.request_status_label = QLabel("") # For showing submission status
        self.request_status_label.setFont(QFont("Arial", 10))
        consult_form_layout.addWidget(self.request_status_label)

        consultation_group.setLayout(consult_form_layout)
        main_layout.addWidget(consultation_group)

        main_layout.addStretch(1)
        self.setLayout(main_layout)
        self._selected_faculty_for_request = None # Store full faculty data dictionary

    def set_student_info(self, student_data):
        self.current_student_data = student_data
        if student_data and 'name' in student_data:
            self.welcome_label.setText(f"Welcome, {student_data['name']}!")
        else:
            self.welcome_label.setText("Welcome, Student!")

    def load_faculty_data(self):
        logging.info("MainDashboard: Attempting to load/refresh faculty data.")
        self._clear_faculty_cards()
        db_service = self.db_service_getter()
        if not db_service:
            logging.error("MainDashboard: DatabaseService not available to load faculty data.")
            self.faculty_table.setRowCount(0) # Clear table
            QMessageBox.warning(self, "Error", "Could not connect to database to load faculty.")
            return

        try:
            # Get filter values
            name_filter = self.faculty_name_search_input.text().strip()
            dept_filter_val = self.dept_filter_combo.currentText()
            if dept_filter_val == "All Departments": dept_filter_val = None
            
            status_filter_val = self.status_filter_combo.currentText()
            if status_filter_val == "All Statuses": status_filter_val = None

            faculty_list = db_service.get_all_faculty(name_filter=name_filter if name_filter else None,
                                                      department_filter=dept_filter_val,
                                                      status_filter=status_filter_val)

            self.faculty_table.setRowCount(0) # Clear existing rows
            if faculty_list:
                self.faculty_table.setRowCount(len(faculty_list))
                for row_idx, faculty_member in enumerate(faculty_list):
                    self._populate_faculty_row(row_idx, faculty_member)
            else:
                logging.info("MainDashboard: No faculty data found.")
        except Exception as e:
            logging.error(f"MainDashboard: Error loading faculty data: {e}")
            self.faculty_table.setRowCount(0)
            QMessageBox.critical(self, "Load Error", f"Failed to load faculty data: {e}")

    def _populate_faculty_row(self, row_idx, faculty_member):
        name_item = QTableWidgetItem(str(faculty_member.get('name', 'N/A')))
        dept_item = QTableWidgetItem(str(faculty_member.get('department', 'N/A')))
        office_item = QTableWidgetItem(str(faculty_member.get('office_location', 'N/A')))
        status_item = QTableWidgetItem(str(faculty_member.get('current_status', 'Unknown')))

        status_text = faculty_member.get('current_status', 'Unknown').lower()
        if status_text == 'available':
            status_item.setBackground(QColor("#ccffcc")) # Light green
            status_item.setForeground(QColor("darkGreen"))
        elif status_text == 'unavailable':
            status_item.setBackground(QColor("#ffcccc")) # Light red
            status_item.setForeground(QColor("darkRed"))
        else:
            status_item.setBackground(QColor("#f0f0f0")) # Light grey

        # Center align status for better visuals
        status_item.setTextAlignment(Qt.AlignCenter)

        self.faculty_table.setItem(row_idx, 0, name_item)
        self.faculty_table.setItem(row_idx, 1, dept_item)
        self.faculty_table.setItem(row_idx, 2, office_item)
        self.faculty_table.setItem(row_idx, 3, status_item)

        # Store faculty_id and ble_identifier in the name item for later retrieval
        name_item.setData(Qt.UserRole, faculty_member) # Store the whole dict

    def _handle_logout(self):
        self.request_logout.emit()
        # The main application will handle switching back to the auth screen.

    def _handle_faculty_selection_for_request(self, item: QTableWidgetItem):
        # item is the cell item that was double-clicked, usually the name item
        # We want the data stored in the first column (name_item) of that row
        name_cell_item = self.faculty_table.item(item.row(), 0)
        if name_cell_item:
            faculty_data = name_cell_item.data(Qt.UserRole)
            if faculty_data and isinstance(faculty_data, dict):
                self._selected_faculty_for_request = faculty_data
                self.selected_faculty_label.setText(f"Selected Faculty: {faculty_data.get('name', 'N/A')} (Dept: {faculty_data.get('department', 'N/A')})")
                self.submit_request_button.setEnabled(True)
                self.request_status_label.setText("") # Clear previous status
                logging.info(f"Faculty selected for consultation: {faculty_data.get('name')}")
            else:
                logging.warning("_handle_faculty_selection_for_request: No data or wrong data type in UserRole.")
                self._selected_faculty_for_request = None
                self.selected_faculty_label.setText("Selected Faculty: None (Error reading data)")
                self.submit_request_button.setEnabled(False)

    def _handle_submit_request_button(self):
        if not self.current_student_data or 'student_id' not in self.current_student_data:
            QMessageBox.warning(self, "Login Error", "Cannot submit request. Student not logged in properly.")
            return
        if not self._selected_faculty_for_request or 'faculty_id' not in self._selected_faculty_for_request:
            QMessageBox.warning(self, "Selection Error", "Please select a faculty member first by double-clicking their name.")
            return

        course_code = self.course_code_input.text().strip()
        subject = self.subject_input.text().strip()
        details = self.details_input.text().strip()

        if not subject: # Subject is mandatory for this MVP example
            QMessageBox.warning(self, "Input Error", "Please enter a subject for your consultation request.")
            self.subject_input.setFocus()
            return

        request_data = {
            "student_id": self.current_student_data['student_id'],
            "faculty_id": self._selected_faculty_for_request['faculty_id'],
            "faculty_ble_identifier": self._selected_faculty_for_request['ble_identifier'], # For MQTT topic
            "student_name": self.current_student_data.get('name', 'Unknown Student'), # For MQTT payload
            "course_code": course_code,
            "subject": subject,
            "details": details
        }
        self.submit_consultation_request.emit(request_data)
        self.set_request_status_message("Submitting request...", is_error=False)
    
    def set_request_status_message(self, message, is_error=False, duration_ms=3000):
        self.request_status_label.setText(message)
        palette = self.request_status_label.palette()
        if is_error:
            palette.setColor(QPalette.WindowText, QColor("red"))
        else:
            palette.setColor(QPalette.WindowText, QColor("blue")) 
        self.request_status_label.setPalette(palette)
        if duration_ms > 0:
             QTimer.singleShot(duration_ms, lambda: self.request_status_label.setText(""))

    def clear_request_form(self):
        self.course_code_input.clear()
        self.subject_input.clear()
        self.details_input.clear()
        self._selected_faculty_for_request = None
        self.selected_faculty_label.setText("Selected Faculty: None (Double-click a faculty member from the list above)")
        self.submit_request_button.setEnabled(False)
        # self.request_status_label.setText("") # Cleared by timer or next status

    def view_did_appear(self):
        """Called when this view becomes active."""
        logging.info("MainDashboardScreen appeared.")
        self._populate_department_filter() # Populate departments before loading data
        self.load_faculty_data() # Load data when view is shown
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(self.refresh_interval_ms)

    def view_did_disappear(self):
        """Called when this view is no longer active."""
        logging.info("MainDashboardScreen disappeared.")
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()

    def _populate_department_filter(self):
        logging.debug("Populating department filter...")
        db_service = self.db_service_getter()
        if not db_service:
            logging.warning("Cannot populate department filter, DB service not available.")
            return
        try:
            current_selection = self.dept_filter_combo.currentText()
            self.dept_filter_combo.blockSignals(True)
            self.dept_filter_combo.clear()
            self.dept_filter_combo.addItem("All Departments")
            # This could be optimized by getting distinct departments from DB
            all_faculty = db_service.get_all_faculty() 
            if all_faculty:
                departments = sorted(list(set(f['department'] for f in all_faculty if f.get('department'))))
                for dept in departments:
                    self.dept_filter_combo.addItem(dept)
            
            idx = self.dept_filter_combo.findText(current_selection)
            if idx != -1: self.dept_filter_combo.setCurrentIndex(idx)
            else: self.dept_filter_combo.setCurrentIndex(0)
            
        except Exception as e:
            logging.error(f"Error populating department filter: {e}")
        finally:
            self.dept_filter_combo.blockSignals(False)

    def _clear_faculty_cards(self):
        for i in reversed(range(self.faculty_grid_layout.count())):
            widget_to_remove = self.faculty_grid_layout.itemAt(i).widget()
            if widget_to_remove:
                self.faculty_grid_layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)
                widget_to_remove.deleteLater()
        self.faculty_cards = []

# Example of how to run this screen standalone (for testing)
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- Mock DatabaseService for testing UI standalone ---
    class MockDBServiceForDashboard:
        def get_all_faculty(self, department_filter=None, status_filter=None):
            print(f"MockDB: get_all_faculty called (dept: {department_filter}, status: {status_filter})")
            # Simulate some data
            return [
                {'faculty_id': 1, 'name': 'Dr. Alpha', 'department': 'CompSci', 'office_location': 'A101', 'current_status': 'Available', 'ble_identifier': 'BLE_A'},
                {'faculty_id': 2, 'name': 'Prof. Beta', 'department': 'Physics', 'office_location': 'B203', 'current_status': 'Unavailable', 'ble_identifier': 'BLE_B'},
                {'faculty_id': 3, 'name': 'Dr. Gamma', 'department': 'CompSci', 'office_location': 'A102', 'current_status': 'Available', 'ble_identifier': 'BLE_G'},
            ]
    mock_db_dash = MockDBServiceForDashboard()
    
    # The dashboard needs a way to get the db_service, so we provide a simple lambda
    dashboard_screen = MainDashboardScreen(db_service_getter=lambda: mock_db_dash)
    dashboard_screen.set_student_info({"name": "Test Student User"})
    dashboard_screen.show() # For RPi, .showFullScreen()
    dashboard_screen.view_did_appear() # Manually trigger
    sys.exit(app.exec_()) 