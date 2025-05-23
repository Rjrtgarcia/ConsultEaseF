import logging
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QAbstractItemView,
                             QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QColor

logger_admin_dash = logging.getLogger(__name__)

# Color constants (some might be used for dynamic styling if QSS doesn't cover all cases)
NU_BLUE = "#003DA7"
NU_GOLD = "#FDB813"
STATUS_GREEN = "#2ECC71"
STATUS_RED = "#E74C3C"
STATUS_ORANGE = "#F39C12"

class AdminDashboardScreen(QWidget):
    # Signals for controller interaction if needed later, for now direct calls
    # e.g., request_load_students = pyqtSignal()
    request_logout_from_admin_panel = pyqtSignal() # Signal to logout

    def __init__(self, admin_controller, main_dashboard_ref, parent=None):
        super().__init__(parent)
        self.setObjectName("adminDashboardScreen") # For root QSS styling
        logger_admin_dash.info("AdminDashboardScreen: __init__ started.")
        self.admin_controller = admin_controller
        self.main_dashboard_ref = main_dashboard_ref # To refresh if needed
        self.setWindowTitle("Admin Dashboard - ConsultEase")
        self.setMinimumSize(900, 600)
        
        logger_admin_dash.info("AdminDashboardScreen: Calling _init_ui().")
        self._init_ui()
        logger_admin_dash.info("AdminDashboardScreen: _init_ui() completed.")
        
        self._load_and_apply_styles()
        self._connect_signals()
        logger_admin_dash.info("AdminDashboardScreen: _connect_signals() completed.")

        logger_admin_dash.info("AdminDashboardScreen: Calling load_all_data().")
        self.load_all_data()
        logger_admin_dash.info("AdminDashboardScreen: load_all_data() completed.")
        logger_admin_dash.info("AdminDashboardScreen: __init__ finished.")

    def _init_ui(self):
        logger_admin_dash.info("AdminDashboardScreen: _init_ui() started.")
        # Overall screen layout (Header + Content)
        screen_layout = QVBoxLayout(self)
        screen_layout.setContentsMargins(0, 0, 0, 0) # No margin for the main screen layout
        screen_layout.setSpacing(0)

        # 1. Header Bar
        admin_header_bar = QWidget()
        admin_header_bar.setObjectName("adminHeaderBar")
        admin_header_layout = QHBoxLayout(admin_header_bar)
        admin_header_layout.setContentsMargins(15,0,15,0)

        header_title = QLabel("ConsultEase - Admin Panel")
        header_title.setObjectName("adminHeaderTitleLabel")
        admin_header_layout.addWidget(header_title)
        admin_header_layout.addStretch(1)

        self.logout_button = QPushButton("Logout") # Re-styled and moved here
        self.logout_button.setObjectName("adminLogoutButton")
        self.logout_button.clicked.connect(self.request_logout_from_admin_panel.emit)
        admin_header_layout.addWidget(self.logout_button)
        screen_layout.addWidget(admin_header_bar)

        # 2. Main Content Area for Tabs
        admin_main_content_area = QWidget()
        admin_main_content_area.setObjectName("adminMainContentArea")
        content_area_layout = QVBoxLayout(admin_main_content_area)
        content_area_layout.setContentsMargins(15, 15, 15, 15) # Padding around the tab widget
        content_area_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("adminTabWidget")
        
        logger_admin_dash.info("AdminDashboardScreen: Adding Manage Students tab.")
        self.tabs.addTab(self._create_students_tab(), "Manage Students")
        logger_admin_dash.info("AdminDashboardScreen: Manage Students tab added.")

        logger_admin_dash.info("AdminDashboardScreen: Adding Manage Faculty tab.")
        self.tabs.addTab(self._create_faculty_tab(), "Manage Faculty")
        logger_admin_dash.info("AdminDashboardScreen: Manage Faculty tab added.")

        logger_admin_dash.info("AdminDashboardScreen: Adding View Consultations tab.")
        self.tabs.addTab(self._create_consultations_tab(), "View Consultations")
        logger_admin_dash.info("AdminDashboardScreen: View Consultations tab added.")
        
        content_area_layout.addWidget(self.tabs)
        screen_layout.addWidget(admin_main_content_area)
        self.setLayout(screen_layout)
        logger_admin_dash.info("AdminDashboardScreen: _init_ui() finished.")

    def _load_and_apply_styles(self):
        style_file_path = os.path.join(os.path.dirname(__file__), "styles", "admin_dashboard_style.qss")
        try:
            with open(style_file_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            logger_admin_dash.error(f"Admin Stylesheet not found: {style_file_path}")
        except Exception as e:
            logger_admin_dash.error(f"Error loading admin stylesheet: {e}")

    def _connect_signals(self):
        # Connect signals from controller to update tables
        self.admin_controller.students_data_changed.connect(self.load_students_data)
        self.admin_controller.faculty_data_changed.connect(self.load_faculty_data)
        self.admin_controller.consultations_data_changed.connect(self.load_consultations_data)
        # Connect signal from controller for RFID tag scanned for new student
        self.admin_controller.rfid_tag_scanned_for_student.connect(self.update_rfid_tag_entry_for_new_student)

    def _create_general_table(self, headers): # Renamed from _create_table to avoid conflict if any base class has it
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive) # Allow column resize
        table.setAlternatingRowColors(True) # QSS might override this, but good fallback
        return table

    # -------------------- Student Tab --------------------
    def _create_students_tab(self):
        student_tab_content = QWidget()
        student_tab_content.setObjectName("tabContentWidget") # For common tab content styling
        main_layout = QHBoxLayout(student_tab_content)
        main_layout.setSpacing(15)

        form_group = QGroupBox("Student Details")
        form_container_layout = QVBoxLayout() # Use QVBoxLayout for vertical arrangement of form and buttons
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        self.student_id_entry = QLineEdit() 
        self.student_id_entry.setReadOnly(True)
        self.student_id_entry.setPlaceholderText("Auto-generated or N/A")
        self.student_name_entry = QLineEdit()
        self.student_number_entry = QLineEdit()
        self.course_entry = QLineEdit()
        self.department_entry = QLineEdit()
        self.rfid_tag_entry = QLineEdit()

        form_layout.addRow("Student ID:", self.student_id_entry)
        form_layout.addRow("Full Name:", self.student_name_entry)
        form_layout.addRow("Student Number:", self.student_number_entry)
        form_layout.addRow("Course:", self.course_entry)
        form_layout.addRow("Department:", self.department_entry)
        
        rfid_layout = QHBoxLayout()
        rfid_layout.addWidget(self.rfid_tag_entry)
        self.scan_rfid_button_student = QPushButton("Scan RFID")
        self.scan_rfid_button_student.setObjectName("secondaryAdminButton") # Or a more specific ID
        # self.scan_rfid_button_student.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon)) # Example Icon
        rfid_layout.addWidget(self.scan_rfid_button_student)
        form_layout.addRow("RFID Tag:", rfid_layout)
        form_container_layout.addLayout(form_layout)
        form_container_layout.addSpacing(10)

        student_buttons_layout = QHBoxLayout()
        self.add_student_button = QPushButton("Add Student")
        self.add_student_button.setObjectName("primaryAdminButton")
        self.update_student_button = QPushButton("Update Student")
        self.update_student_button.setObjectName("primaryAdminButton")
        self.clear_student_form_button = QPushButton("Clear Form")
        self.clear_student_form_button.setObjectName("secondaryAdminButton")
        student_buttons_layout.addStretch(1)
        student_buttons_layout.addWidget(self.add_student_button)
        student_buttons_layout.addWidget(self.update_student_button)
        student_buttons_layout.addStretch(1)
        student_buttons_layout.addWidget(self.clear_student_form_button)
        form_container_layout.addLayout(student_buttons_layout)
        form_group.setLayout(form_container_layout)

        table_group = QGroupBox("Registered Students")
        table_layout = QVBoxLayout()
        headers = ["ID", "Name", "Student No.", "Course", "Department", "RFID Tag", "Created At"]
        self.students_table = self._create_general_table(headers)
        table_layout.addWidget(self.students_table)
        table_group.setLayout(table_layout)

        main_layout.addWidget(form_group, 1)
        main_layout.addWidget(table_group, 2)

        self.add_student_button.clicked.connect(self._add_student)
        self.update_student_button.clicked.connect(self._update_student)
        self.clear_student_form_button.clicked.connect(self._clear_student_form)
        self.students_table.itemDoubleClicked.connect(self._load_student_data_to_form) # Keep double click to load
        self.scan_rfid_button_student.clicked.connect(self._on_scan_rfid_for_student_clicked)
        self._clear_student_form() # Initialize form state
        return student_tab_content

    @pyqtSlot(str)
    def update_rfid_tag_entry_for_new_student(self, tag_id):
        logger_admin_dash.info(f"AdminDashboardScreen: Received tag to update UI: {tag_id}")
        self.rfid_tag_entry.setText(tag_id)
        if not tag_id:
            QMessageBox.warning(self, "RFID Scan", "Failed to scan RFID tag or scan was cancelled.")

    def _on_scan_rfid_for_student_clicked(self):
        logger_admin_dash.info("AdminDashboardScreen: 'Scan RFID for Student' button clicked.")
        self.rfid_tag_entry.clear()
        # QMessageBox.information(self, "RFID Scan", "Please scan the student's RFID tag now.") # Can be intrusive
        self.admin_controller.handle_scan_tag_for_new_student_button()

    def _clear_student_form(self):
        self.student_id_entry.setText("N/A")
        self.student_name_entry.clear()
        self.student_number_entry.clear()
        self.course_entry.clear()
        self.department_entry.clear()
        self.rfid_tag_entry.clear()
        self.students_table.clearSelection()
        self.update_student_button.setEnabled(False)
        self.add_student_button.setEnabled(True)

    def _load_student_data_to_form(self, item=None): # Item can be None if called after add/update
        selected_rows = self.students_table.selectedItems()
        if not selected_rows and item is None:
            self._clear_student_form()
            return
        
        row = item.row() if item else selected_rows[0].row()
        self.student_id_entry.setText(self.students_table.item(row, 0).text())
        self.student_name_entry.setText(self.students_table.item(row, 1).text())
        self.student_number_entry.setText(self.students_table.item(row, 2).text() if self.students_table.item(row, 2) else "")
        self.course_entry.setText(self.students_table.item(row, 3).text() if self.students_table.item(row, 3) else "")
        self.department_entry.setText(self.students_table.item(row, 4).text() if self.students_table.item(row, 4) else "")
        self.rfid_tag_entry.setText(self.students_table.item(row, 5).text() if self.students_table.item(row, 5) else "")
        self.update_student_button.setEnabled(True)
        self.add_student_button.setEnabled(False)

    def _add_student(self):
        rfid = self.rfid_tag_entry.text().strip()
        name = self.student_name_entry.text().strip()
        student_number = self.student_number_entry.text().strip()
        course = self.course_entry.text().strip()
        department = self.department_entry.text().strip()

        if not rfid or not name:
            QMessageBox.warning(self, "Input Error", "RFID Tag and Name are required.")
            return
        
        if self.admin_controller.add_student(rfid_tag=rfid, name=name, student_number=student_number, course=course, department=department):
            QMessageBox.information(self, "Success", "Student added successfully.")
            self._clear_student_form()
            # self.admin_controller.load_students() # Signal students_data_changed will trigger this
        else:
            QMessageBox.critical(self, "Error", "Failed to add student. Check logs or ensure RFID is unique.")

    def _update_student(self):
        student_id_text = self.student_id_entry.text()
        if not student_id_text or student_id_text == "N/A":
            QMessageBox.warning(self, "Selection Error", "Please select a student to update.")
            return
        try:
            student_id = int(student_id_text)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid Student ID.")
            return

        rfid = self.rfid_tag_entry.text().strip()
        name = self.student_name_entry.text().strip()
        student_number = self.student_number_entry.text().strip()
        course = self.course_entry.text().strip()
        department = self.department_entry.text().strip()

        if not rfid or not name:
            QMessageBox.warning(self, "Input Error", "RFID Tag and Name are required.")
            return

        if self.admin_controller.update_student(student_id=student_id, rfid_tag=rfid, name=name, student_number=student_number, course=course, department=department):
            QMessageBox.information(self, "Success", "Student updated successfully.")
            self._clear_student_form()
            # self.admin_controller.load_students() # Signal students_data_changed will trigger this
        else:
            QMessageBox.critical(self, "Error", "Failed to update student. Check logs or ensure RFID uniqueness.")

    def _delete_student(self):
        student_id_text = self.student_id_entry.text()
        if not student_id_text or student_id_text == "N/A":
            QMessageBox.warning(self, "Selection Error", "Please select a student from the table to delete.")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete student ID {student_id_text} ({self.student_name_entry.text()})?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.admin_controller.delete_student(int(student_id_text)):
                QMessageBox.information(self, "Success", "Student deleted successfully.")
                self._clear_student_form()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete student. Check logs or related consultations.")

    # -------------------- Faculty Tab --------------------
    def _create_faculty_tab(self):
        faculty_tab_content = QWidget()
        faculty_tab_content.setObjectName("tabContentWidget")
        main_layout = QHBoxLayout(faculty_tab_content)
        main_layout.setSpacing(15)

        form_group = QGroupBox("Faculty Details")
        form_container_layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        self.faculty_id_label = QLineEdit() # Changed to QLineEdit for consistency, readonly
        self.faculty_id_label.setReadOnly(True)
        self.faculty_id_label.setPlaceholderText("Auto-generated or N/A")
        self.faculty_name_edit = QLineEdit()
        self.faculty_dept_edit = QLineEdit()
        self.faculty_ble_edit = QLineEdit()
        self.faculty_office_edit = QLineEdit()
        self.faculty_contact_edit = QLineEdit()

        form_layout.addRow("Faculty ID:", self.faculty_id_label)
        form_layout.addRow("Full Name:", self.faculty_name_edit)
        form_layout.addRow("Department:", self.faculty_dept_edit)
        form_layout.addRow("BLE Identifier:", self.faculty_ble_edit)
        form_layout.addRow("Office Location:", self.faculty_office_edit)
        form_layout.addRow("Contact Details:", self.faculty_contact_edit)
        form_container_layout.addLayout(form_layout)
        form_container_layout.addSpacing(10)

        faculty_buttons_layout = QHBoxLayout()
        self.faculty_add_button = QPushButton("Add Faculty")
        self.faculty_add_button.setObjectName("primaryAdminButton")
        self.faculty_update_button = QPushButton("Update Faculty")
        self.faculty_update_button.setObjectName("primaryAdminButton")
        self.faculty_clear_button = QPushButton("Clear Form") # Renamed from "Clear Fields"
        self.faculty_clear_button.setObjectName("secondaryAdminButton")
        # Delete button could be added here if form-based deletion is preferred
        # self.faculty_delete_button = QPushButton("Delete Faculty") 
        # self.faculty_delete_button.setObjectName("dangerAdminButton")

        faculty_buttons_layout.addStretch(1)
        faculty_buttons_layout.addWidget(self.faculty_add_button)
        faculty_buttons_layout.addWidget(self.faculty_update_button)
        faculty_buttons_layout.addStretch(1)
        faculty_buttons_layout.addWidget(self.faculty_clear_button)
        # faculty_buttons_layout.addWidget(self.faculty_delete_button)
        form_container_layout.addLayout(faculty_buttons_layout)
        form_group.setLayout(form_container_layout)

        table_group = QGroupBox("Registered Faculty")
        table_layout = QVBoxLayout()
        headers = ["ID", "Name", "Department", "BLE ID", "Office", "Contact", "Status", "Status Updated"]
        self.faculty_table = self._create_general_table(headers)
        self.faculty_table.itemSelectionChanged.connect(self._load_faculty_to_form) # Changed from itemDoubleClicked
        
        # Refresh button might not be needed if data is auto-refreshed via signals
        # self.faculty_refresh_button = QPushButton("Refresh List")
        # table_layout.addWidget(self.faculty_refresh_button)
        table_layout.addWidget(self.faculty_table)
        table_group.setLayout(table_layout)

        main_layout.addWidget(form_group, 1)
        main_layout.addWidget(table_group, 2)

        self.faculty_add_button.clicked.connect(self._handle_add_faculty)
        self.faculty_update_button.clicked.connect(self._handle_update_faculty)
        self.faculty_clear_button.clicked.connect(self._clear_faculty_fields)
        # if self.faculty_delete_button: self.faculty_delete_button.clicked.connect(self._handle_delete_faculty)
        self._clear_faculty_fields()
        return faculty_tab_content

    def _clear_faculty_fields(self):
        self.faculty_id_label.setText("N/A")
        self.faculty_name_edit.clear()
        self.faculty_dept_edit.clear()
        self.faculty_ble_edit.clear()
        self.faculty_office_edit.clear()
        self.faculty_contact_edit.clear()
        self.faculty_table.clearSelection()
        self.faculty_update_button.setEnabled(False)
        self.faculty_add_button.setEnabled(True)

    def _load_faculty_to_form(self):
        selected_rows = self.faculty_table.selectedItems()
        if not selected_rows:
            self._clear_faculty_fields()
            return
        
        row = selected_rows[0].row()
        self.faculty_id_label.setText(self.faculty_table.item(row, 0).text())
        self.faculty_name_edit.setText(self.faculty_table.item(row, 1).text())
        self.faculty_dept_edit.setText(self.faculty_table.item(row, 2).text())
        self.faculty_ble_edit.setText(self.faculty_table.item(row, 3).text())
        self.faculty_office_edit.setText(self.faculty_table.item(row, 4).text() if self.faculty_table.item(row, 4) else "")
        self.faculty_contact_edit.setText(self.faculty_table.item(row, 5).text() if self.faculty_table.item(row, 5) else "")
        self.faculty_update_button.setEnabled(True)
        self.faculty_add_button.setEnabled(False)

    def _handle_add_faculty(self):
        name = self.faculty_name_edit.text().strip()
        dept = self.faculty_dept_edit.text().strip()
        ble_id = self.faculty_ble_edit.text().strip()
        office = self.faculty_office_edit.text().strip()
        contact = self.faculty_contact_edit.text().strip()

        if not name or not dept or not ble_id:
            QMessageBox.warning(self, "Input Error", "Name, Department, and BLE Identifier are required.")
            return
        if self.admin_controller.add_faculty(name, dept, ble_id, office, contact):
            QMessageBox.information(self, "Success", "Faculty added successfully.")
            self._clear_faculty_fields()
        else:
            QMessageBox.critical(self, "Error", "Failed to add faculty. Check logs or ensure BLE ID is unique.")

    def _handle_update_faculty(self):
        faculty_id_text = self.faculty_id_label.text()
        if faculty_id_text == "N/A" or not faculty_id_text:
            QMessageBox.warning(self, "Selection Error", "Please select a faculty member to update.")
            return
        faculty_id = int(faculty_id_text)
        name = self.faculty_name_edit.text().strip()
        dept = self.faculty_dept_edit.text().strip()
        ble_id = self.faculty_ble_edit.text().strip()
        office = self.faculty_office_edit.text().strip()
        contact = self.faculty_contact_edit.text().strip()

        if not name or not dept or not ble_id:
            QMessageBox.warning(self, "Input Error", "Name, Department, and BLE Identifier are required.")
            return
        if self.admin_controller.update_faculty(faculty_id, name, dept, ble_id, office, contact):
            QMessageBox.information(self, "Success", "Faculty updated successfully.")
            self._clear_faculty_fields()
        else:
            QMessageBox.critical(self, "Error", "Failed to update faculty. Check logs.")

    def _handle_delete_faculty(self): # Needs connection if button added
        faculty_id_text = self.faculty_id_label.text()
        if faculty_id_text == "N/A" or not faculty_id_text:
            QMessageBox.warning(self, "Selection Error", "Please select a faculty member to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete faculty ID {faculty_id_text} ({self.faculty_name_edit.text()})?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.admin_controller.delete_faculty(int(faculty_id_text)):
                QMessageBox.information(self, "Success", "Faculty deleted successfully.")
                self._clear_faculty_fields()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete faculty. Check logs.")

    # -------------------- Consultation Tab --------------------
    def _create_consultations_tab(self):
        consultation_tab_content = QWidget()
        consultation_tab_content.setObjectName("tabContentWidget")
        layout = QVBoxLayout(consultation_tab_content)
        layout.setSpacing(15)
        
        table_group = QGroupBox("All Consultation Requests")
        table_layout = QVBoxLayout(table_group) # Set layout for groupbox directly
        
        # Optional: Filters for consultations (e.g., by status, faculty, date)
        # filter_layout = QHBoxLayout()
        # ... add filter widgets ...
        # table_layout.addLayout(filter_layout)
        
        headers = ["ID", "Student", "Faculty", "Course", "Subject", "Status", "Requested At", "Updated At"]
        self.consultation_table = self._create_general_table(headers)
        # Consider making subject/details columns wider or allowing text wrap
        # self.consultation_table.setWordWrap(True) # For all cells - might be too much
        # self.consultation_table.resizeRowsToContents() # If word wrap is enabled

        # Refresh button
        # self.consultation_refresh_button = QPushButton("Refresh List")
        # self.consultation_refresh_button.setObjectName("secondaryAdminButton")
        # self.consultation_refresh_button.clicked.connect(self.load_consultations_data)
        # table_layout.addWidget(self.consultation_refresh_button, 0, Qt.AlignRight)

        table_layout.addWidget(self.consultation_table)
        # table_group.setLayout(table_layout) # Already set in constructor
        layout.addWidget(table_group)
        return consultation_tab_content

    # -------------------- Data Loading Functions --------------------
    def load_all_data(self):
        logger_admin_dash.info("AdminDashboardScreen: load_all_data() called.")
        self.load_students_data()
        self.load_faculty_data()
        self.load_consultations_data()

    def load_students_data(self):
        logger_admin_dash.debug("Loading students data...")
        students = self.admin_controller.get_all_students()
        self.students_table.setRowCount(0) 
        if students:
            for row_num, student_data in enumerate(students):
                self.students_table.insertRow(row_num)
                self.students_table.setItem(row_num, 0, QTableWidgetItem(str(student_data.get('student_id', ''))))
                self.students_table.setItem(row_num, 1, QTableWidgetItem(student_data.get('name', '')))
                self.students_table.setItem(row_num, 2, QTableWidgetItem(student_data.get('student_number', '')))
                self.students_table.setItem(row_num, 3, QTableWidgetItem(student_data.get('course', '')))
                self.students_table.setItem(row_num, 4, QTableWidgetItem(student_data.get('department', '')))
                self.students_table.setItem(row_num, 5, QTableWidgetItem(student_data.get('rfid_tag', '')))
                created_at = student_data.get('created_at')
                self.students_table.setItem(row_num, 6, QTableWidgetItem(str(created_at.strftime("%Y-%m-%d %H:%M")) if created_at else ''))
        # self.students_table.resizeColumnsToContents() # Can make UI jumpy, QSS can define column widths or header stretch

    def load_faculty_data(self):
        logger_admin_dash.debug("Loading faculty data...")
        faculty_list = self.admin_controller.get_all_faculty()
        self.faculty_table.setRowCount(0)
        if faculty_list:
            for row_num, faculty_data in enumerate(faculty_list):
                self.faculty_table.insertRow(row_num)
                self.faculty_table.setItem(row_num, 0, QTableWidgetItem(str(faculty_data.get('faculty_id', ''))))
                self.faculty_table.setItem(row_num, 1, QTableWidgetItem(faculty_data.get('name', '')))
                self.faculty_table.setItem(row_num, 2, QTableWidgetItem(faculty_data.get('department', '')))
                self.faculty_table.setItem(row_num, 3, QTableWidgetItem(faculty_data.get('ble_identifier', '')))
                self.faculty_table.setItem(row_num, 4, QTableWidgetItem(faculty_data.get('office_location', '')))
                self.faculty_table.setItem(row_num, 5, QTableWidgetItem(faculty_data.get('contact_details', '')))
                status_item = QTableWidgetItem(faculty_data.get('current_status', 'Offline'))
                self.faculty_table.setItem(row_num, 6, status_item)
                status_updated_at = faculty_data.get('status_updated_at')
                self.faculty_table.setItem(row_num, 7, QTableWidgetItem(str(status_updated_at.strftime("%Y-%m-%d %H:%M")) if status_updated_at else ''))
                self._style_status_cell(status_item, faculty_data.get('current_status', 'Offline'))

    def load_consultations_data(self):
        logger_admin_dash.debug("Loading consultations data...")
        consultations = self.admin_controller.get_all_consultations()
        self.consultation_table.setRowCount(0)
        if consultations:
            for row_num, consult_data in enumerate(consultations):
                self.consultation_table.insertRow(row_num)
                self.consultation_table.setItem(row_num, 0, QTableWidgetItem(str(consult_data.get('consultation_id', ''))))
                student_info = f"{consult_data.get('student_name', 'N/A')} (ID: {consult_data.get('student_id', 'N/A')})"
                self.consultation_table.setItem(row_num, 1, QTableWidgetItem(student_info))
                faculty_info = f"{consult_data.get('faculty_name', 'N/A')} (ID: {consult_data.get('faculty_id', 'N/A')})"
                self.consultation_table.setItem(row_num, 2, QTableWidgetItem(faculty_info))
                self.consultation_table.setItem(row_num, 3, QTableWidgetItem(consult_data.get('course_code', '')))
                self.consultation_table.setItem(row_num, 4, QTableWidgetItem(consult_data.get('subject', '')))
                # Details can be long, consider tooltip or separate view if too much for table
                # details_item = QTableWidgetItem(consult_data.get('request_details', ''))
                # self.consultation_table.setItem(row_num, 5, details_item)
                status_item = QTableWidgetItem(consult_data.get('status', 'Pending'))
                self.consultation_table.setItem(row_num, 5, status_item) # Index changed from 6 due to removing details
                self._style_status_cell(status_item, consult_data.get('status', 'Pending'))
                
                requested_at = consult_data.get('requested_at')
                self.consultation_table.setItem(row_num, 6, QTableWidgetItem(str(requested_at.strftime("%Y-%m-%d %H:%M")) if requested_at else ''))
                updated_at = consult_data.get('updated_at')
                self.consultation_table.setItem(row_num, 7, QTableWidgetItem(str(updated_at.strftime("%Y-%m-%d %H:%M")) if updated_at else ''))
    
    def _style_status_cell(self, item: QTableWidgetItem, status_text: str):
        status_text = status_text.lower()
        color = QColor(Qt.black) # Default
        if status_text == 'available' or status_text == 'approved':
            color = QColor(STATUS_GREEN)
        elif status_text == 'unavailable' or status_text == 'rejected' or status_text == 'cancelled':
            color = QColor(STATUS_RED)
        elif status_text == 'busy' or status_text == 'pending' or status_text == 'in-progress':
            color = QColor(STATUS_ORANGE)
        elif status_text == 'offline' or status_text == 'completed' or status_text == 'deferred':
            color = QColor(Qt.darkGray)
        item.setForeground(color)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        item.setTextAlignment(Qt.AlignCenter)

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Mock AdminController and its methods for standalone testing
    class MockAdminController:
        def get_all_students(self):
            print("Mock: Getting all students")
            return [
                {'student_id': 1, 'rfid_tag': 'S001', 'name': 'Alice Wonderland', 'department': 'CS', 'created_at': '2023-01-01'},
                {'student_id': 2, 'rfid_tag': 'S002', 'name': 'Bob The Builder', 'department': 'Engineering', 'created_at': '2023-01-02'},
            ]
        def add_student(self, rfid, name, dept): print(f"Mock: Adding student {rfid}, {name}, {dept}"); return True
        def update_student(self, sid, rfid, name, dept): print(f"Mock: Updating student {sid}"); return True
        def delete_student(self, sid): print(f"Mock: Deleting student {sid}"); return True

        def get_all_faculty(self):
            print("Mock: Getting all faculty")
            return [
                {'faculty_id': 1, 'name': 'Dr. Elara Vance', 'department': 'Physics', 'ble_identifier': 'BLE_F001', 'office_location': 'A101', 'contact_details': 'ev@uni.com', 'current_status': 'Available', 'status_updated_at': '2023-10-10 10:00'},
                {'faculty_id': 2, 'name': 'Prof. Orion Pax', 'department': 'Cybertronics', 'ble_identifier': 'BLE_F002', 'office_location': 'C202', 'contact_details': 'op@uni.com', 'current_status': 'Busy', 'status_updated_at': '2023-10-10 11:00'},
            ]
        def add_faculty(self, name, dept, ble, office, contact): print(f"Mock: Adding faculty {name}"); return True
        def update_faculty(self, fid, name, dept, ble, office, contact): print(f"Mock: Updating faculty {fid}"); return True
        def delete_faculty(self, fid): print(f"Mock: Deleting faculty {fid}"); return True

        def get_all_consultations(self):
            print("Mock: Getting all consultations")
            return [
                {'consultation_id': 1, 'student_name': 'Alice', 'student_id':1, 'faculty_name': 'Dr. Vance', 'faculty_id':1, 'course_code': 'PHY101', 'subject': 'Quantum Entanglement', 'request_details': 'Need help with homework.', 'status': 'Pending', 'requested_at': '2023-10-10 09:00', 'updated_at': '2023-10-10 09:00'},
                {'consultation_id': 2, 'student_name': 'Bob', 'student_id':2, 'faculty_name': 'Prof. Pax', 'faculty_id':2, 'course_code': 'CYB202', 'subject': 'AI Ethics', 'request_details': 'Project discussion.', 'status': 'Approved', 'requested_at': '2023-10-09 14:00', 'updated_at': '2023-10-09 15:00'},
            ]

    app = QApplication(sys.argv)
    admin_screen = AdminDashboardScreen(MockAdminController())
    admin_screen.show()
    sys.exit(app.exec_()) 