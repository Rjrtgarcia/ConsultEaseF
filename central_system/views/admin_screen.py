import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem, 
    QHeaderView, QDialog, QInputDialog, QFormLayout, QGroupBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
import logging

class AdminScreen(QWidget):
    request_admin_logout = pyqtSignal() # Or navigate back to dashboard
    request_add_student = pyqtSignal(dict)
    request_add_faculty = pyqtSignal(dict)
    request_load_students = pyqtSignal()
    request_load_faculty = pyqtSignal()

    def __init__(self, parent_stacked_widget: QStackedWidget = None):
        super().__init__()
        self.parent_stacked_widget = parent_stacked_widget
        self.setWindowTitle("ConsultEase - Admin Panel")
        self._is_authenticated = False # Basic auth flag
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20,20,20,20)

        # Placeholder for content - will be replaced by tabs after auth
        self.placeholder_label = QLabel("Admin area locked. Please authenticate.")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setFont(QFont("Arial", 16))
        self.main_layout.addWidget(self.placeholder_label)
        
        # Back button (always visible or only after auth? For now, always)
        # back_button = QPushButton("Back to Dashboard/Login")
        # back_button.clicked.connect(self._handle_admin_logout)
        # self.main_layout.addWidget(back_button, alignment=Qt.AlignBottom | Qt.AlignRight)
        
        self.setLayout(self.main_layout)

    def _setup_admin_interface(self):
        # Remove placeholder if it exists
        if self.placeholder_label:
            self.main_layout.removeWidget(self.placeholder_label)
            self.placeholder_label.deleteLater()
            self.placeholder_label = None

        # Tab Widget for different admin sections
        tab_widget = QTabWidget()
        self.main_layout.insertWidget(0, tab_widget) # Insert tabs at the top

        # Student Management Tab
        student_tab = QWidget()
        student_layout = QVBoxLayout(student_tab)
        self._create_student_management_ui(student_layout)
        tab_widget.addTab(student_tab, "Student Management")

        # Faculty Management Tab
        faculty_tab = QWidget()
        faculty_layout = QVBoxLayout(faculty_tab)
        self._create_faculty_management_ui(faculty_layout)
        tab_widget.addTab(faculty_tab, "Faculty Management")

        # System Settings / Logs (Placeholder for future)
        # settings_tab = QWidget()
        # settings_layout = QVBoxLayout(settings_tab)
        # settings_layout.addWidget(QLabel("System Settings & Logs (Future Implementation)"))
        # tab_widget.addTab(settings_tab, "System Settings")

    def _create_student_management_ui(self, layout: QVBoxLayout):
        # View Students
        view_students_group = QGroupBox("View Students")
        view_students_layout = QVBoxLayout()
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(4) # ID, Name, RFID, Department
        self.students_table.setHorizontalHeaderLabels(["ID", "Name", "RFID Tag", "Department"])
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.students_table.setEditTriggers(QTableWidget.NoEditTriggers)
        refresh_students_button = QPushButton("Refresh Student List")
        refresh_students_button.clicked.connect(lambda: self.request_load_students.emit())
        view_students_layout.addWidget(refresh_students_button)
        view_students_layout.addWidget(self.students_table)
        view_students_group.setLayout(view_students_layout)
        layout.addWidget(view_students_group)

        # Add Student
        add_student_group = QGroupBox("Add New Student")
        add_student_form = QFormLayout()
        self.student_name_input = QLineEdit()
        self.student_rfid_input = QLineEdit()
        self.student_dept_input = QLineEdit()
        add_student_form.addRow("Full Name:", self.student_name_input)
        add_student_form.addRow("RFID Tag ID:", self.student_rfid_input)
        add_student_form.addRow("Department (Optional):", self.student_dept_input)
        add_student_button = QPushButton("Add Student")
        add_student_button.clicked.connect(self._handle_add_student)
        add_student_form.addRow(add_student_button)
        add_student_group.setLayout(add_student_form)
        layout.addWidget(add_student_group)
        layout.addStretch(1)

    def _create_faculty_management_ui(self, layout: QVBoxLayout):
        # View Faculty
        view_faculty_group = QGroupBox("View Faculty")
        view_faculty_layout = QVBoxLayout()
        self.faculty_table = QTableWidget()
        self.faculty_table.setColumnCount(5) # ID, Name, Department, BLE ID, Status
        self.faculty_table.setHorizontalHeaderLabels(["ID", "Name", "Department", "BLE Identifier", "Office", "Status"])
        self.faculty_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) # Adjust as needed
        self.faculty_table.horizontalHeader().setStretchLastSection(True)
        self.faculty_table.setEditTriggers(QTableWidget.NoEditTriggers)
        refresh_faculty_button = QPushButton("Refresh Faculty List")
        refresh_faculty_button.clicked.connect(lambda: self.request_load_faculty.emit())
        view_faculty_layout.addWidget(refresh_faculty_button)
        view_faculty_layout.addWidget(self.faculty_table)
        view_faculty_group.setLayout(view_faculty_layout)
        layout.addWidget(view_faculty_group)

        # Add Faculty
        add_faculty_group = QGroupBox("Add New Faculty")
        add_faculty_form = QFormLayout()
        self.faculty_name_input = QLineEdit()
        self.faculty_dept_input = QLineEdit()
        self.faculty_ble_input = QLineEdit()
        self.faculty_office_input = QLineEdit()
        add_faculty_form.addRow("Full Name:", self.faculty_name_input)
        add_faculty_form.addRow("Department:", self.faculty_dept_input)
        add_faculty_form.addRow("BLE Identifier (MAC Address):", self.faculty_ble_input)
        add_faculty_form.addRow("Office Location (Optional):", self.faculty_office_input)
        add_faculty_button = QPushButton("Add Faculty")
        add_faculty_button.clicked.connect(self._handle_add_faculty)
        add_faculty_form.addRow(add_faculty_button)
        add_faculty_group.setLayout(add_faculty_form)
        layout.addWidget(add_faculty_group)
        layout.addStretch(1)

    def _handle_add_student(self):
        name = self.student_name_input.text().strip()
        rfid = self.student_rfid_input.text().strip()
        dept = self.student_dept_input.text().strip()
        if name and rfid:
            self.request_add_student.emit({"name": name, "rfid_tag": rfid, "department": dept if dept else None})
        else:
            QMessageBox.warning(self, "Input Error", "Student Name and RFID Tag are required.")

    def _handle_add_faculty(self):
        name = self.faculty_name_input.text().strip()
        dept = self.faculty_dept_input.text().strip()
        ble = self.faculty_ble_input.text().strip()
        office = self.faculty_office_input.text().strip()
        if name and dept and ble:
            self.request_add_faculty.emit({"name": name, "department": dept, "ble_identifier": ble, "office_location": office if office else None})
        else:
            QMessageBox.warning(self, "Input Error", "Faculty Name, Department, and BLE Identifier are required.")

    def populate_students_table(self, students_data):
        self.students_table.setRowCount(0)
        if not students_data: return
        self.students_table.setRowCount(len(students_data))
        for row, student in enumerate(students_data):
            self.students_table.setItem(row, 0, QTableWidgetItem(str(student.get('student_id', ''))))
            self.students_table.setItem(row, 1, QTableWidgetItem(student.get('name', '')))
            self.students_table.setItem(row, 2, QTableWidgetItem(student.get('rfid_tag', '')))
            self.students_table.setItem(row, 3, QTableWidgetItem(student.get('department', '')))

    def populate_faculty_table(self, faculty_data):
        self.faculty_table.setRowCount(0)
        if not faculty_data: return
        self.faculty_table.setRowCount(len(faculty_data))
        for row, faculty in enumerate(faculty_data):
            self.faculty_table.setItem(row, 0, QTableWidgetItem(str(faculty.get('faculty_id', ''))))
            self.faculty_table.setItem(row, 1, QTableWidgetItem(faculty.get('name', '')))
            self.faculty_table.setItem(row, 2, QTableWidgetItem(faculty.get('department', '')))
            self.faculty_table.setItem(row, 3, QTableWidgetItem(faculty.get('ble_identifier', '')))
            self.faculty_table.setItem(row, 4, QTableWidgetItem(faculty.get('office_location', '')))
            self.faculty_table.setItem(row, 5, QTableWidgetItem(faculty.get('current_status', '')))

    def prompt_for_password(self):
        if self._is_authenticated: return True
        
        password, ok = QInputDialog.getText(self, "Admin Authentication", "Enter Admin Password:", QLineEdit.Password)
        if ok:
            # In a real app, use a hashed password and proper comparison
            if password == "admin123": # Placeholder password
                self._is_authenticated = True
                self._setup_admin_interface() # Setup UI after successful auth
                self.request_load_students.emit() # Initial load
                self.request_load_faculty.emit()  # Initial load
                return True
            else:
                QMessageBox.critical(self, "Authentication Failed", "Incorrect password.")
                self._handle_admin_logout() # Go back or stay locked
                return False
        else:
            # User cancelled password dialog
            self._handle_admin_logout() # Go back
            return False

    def _handle_admin_logout(self):
        self._is_authenticated = False 
        # Clear admin UI if it was built, then emit signal to navigate away
        # For now, just emit signal. Main app should handle UI reset of admin panel if needed.
        self.request_admin_logout.emit()

    def view_did_appear(self):
        logging.info("AdminScreen appeared.")
        if not self._is_authenticated:
            # Lock out the view if not authenticated and re-prompt or handle it
            # Clear previous UI if any (e.g. if user navigates back and forth)
            while self.main_layout.count() > 1: # Keep only the first (placeholder or button)
                 item = self.main_layout.takeAt(0)
                 if item.widget(): item.widget().deleteLater()
            if not self.placeholder_label: # Re-add placeholder if it was removed
                self.placeholder_label = QLabel("Admin area locked. Please authenticate.")
                self.placeholder_label.setAlignment(Qt.AlignCenter)
                self.placeholder_label.setFont(QFont("Arial", 16))
                self.main_layout.insertWidget(0, self.placeholder_label)
            
            self.prompt_for_password()
        else:
            # Already authenticated, ensure data is fresh
            self.request_load_students.emit()
            self.request_load_faculty.emit()

    def view_did_disappear(self):
        logging.info("AdminScreen disappeared.")
        # self._is_authenticated = False # Optional: force re-auth every time view appears
        # If not forcing re-auth, the admin interface remains built.

# Example usage:
if __name__ == '__main__':
    app = QApplication(sys.argv)
    admin_screen = AdminScreen()
    
    def handle_load_students():
        print("ADMIN_SCREEN_TEST: Load students requested")
        admin_screen.populate_students_table([
            {'student_id': 1, 'name': 'Test Stu 1', 'rfid_tag': 'S001', 'department': 'CS'},
            {'student_id': 2, 'name': 'Test Stu 2', 'rfid_tag': 'S002', 'department': 'EE'}
        ])
    def handle_load_faculty():
        print("ADMIN_SCREEN_TEST: Load faculty requested")
        admin_screen.populate_faculty_table([
            {'faculty_id': 1, 'name': 'Prof. Alpha', 'department': 'CS', 'ble_identifier': 'BLE01', 'office_location': 'A1', 'current_status': 'Available'},
            {'faculty_id': 2, 'name': 'Dr. Beta', 'department': 'EE', 'ble_identifier': 'BLE02', 'office_location': 'B2', 'current_status': 'Unavailable'}
        ])

    admin_screen.request_load_students.connect(handle_load_students)
    admin_screen.request_load_faculty.connect(handle_load_faculty)
    admin_screen.request_add_student.connect(lambda d: print(f"ADMIN_SCREEN_TEST: Add student: {d}"))
    admin_screen.request_add_faculty.connect(lambda d: print(f"ADMIN_SCREEN_TEST: Add faculty: {d}"))
    admin_screen.request_admin_logout.connect(lambda: print("ADMIN_SCREEN_TEST: Logout requested"))

    admin_screen.show()
    admin_screen.view_did_appear() # Trigger auth prompt for standalone test
    sys.exit(app.exec_()) 