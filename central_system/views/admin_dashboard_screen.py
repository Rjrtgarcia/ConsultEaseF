from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont

class AdminDashboardScreen(QWidget):
    # Signals for controller interaction if needed later, for now direct calls
    # e.g., request_load_students = pyqtSignal()
    request_logout_from_admin_panel = pyqtSignal() # Signal to logout

    def __init__(self, admin_controller, main_dashboard_ref, parent=None):
        super().__init__(parent)
        self.admin_controller = admin_controller
        self.main_dashboard_ref = main_dashboard_ref # To refresh if needed
        self.setWindowTitle("Admin Dashboard - ConsultEase")
        self.setGeometry(150, 150, 1000, 700)
        self.setMinimumSize(800, 500)
        self._init_ui()
        self._connect_signals()
        self.load_all_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_students_tab(), "Manage Students")
        self.tabs.addTab(self._create_faculty_tab(), "Manage Faculty")
        self.tabs.addTab(self._create_consultations_tab(), "View Consultations")
        layout.addWidget(self.tabs)

        # Add Logout Button
        self.logout_button = QPushButton("Logout and Return to Login")
        self.logout_button.clicked.connect(self.request_logout_from_admin_panel.emit)
        # Add some styling or place it appropriately, e.g., in a bottom hbox
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.logout_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _connect_signals(self):
        # Connect signals from controller to update tables
        self.admin_controller.students_data_changed.connect(self.load_students_data)
        self.admin_controller.faculty_data_changed.connect(self.load_faculty_data)
        self.admin_controller.consultations_data_changed.connect(self.load_consultations_data)
        # Connect signal from controller for RFID tag scanned for new student
        self.admin_controller.rfid_tag_scanned_for_student.connect(self.update_rfid_tag_entry_for_new_student)

    def _create_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Read-only
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        return table

    # -------------------- Student Tab --------------------
    def _create_students_tab(self):
        student_tab = QWidget()
        main_layout = QHBoxLayout(student_tab)

        # Left side: Add/Edit Student Form
        form_group = QGroupBox("Add/Edit Student")
        form_layout_container = QVBoxLayout()
        form_layout = QFormLayout()

        self.student_id_entry = QLineEdit() # For editing, hidden for new
        self.student_id_entry.setReadOnly(True)
        self.student_name_entry = QLineEdit()
        self.student_number_entry = QLineEdit()
        self.course_entry = QLineEdit()
        self.department_entry = QLineEdit()
        self.rfid_tag_entry = QLineEdit()

        form_layout.addRow("Student ID (for edit):", self.student_id_entry)
        form_layout.addRow("Name:", self.student_name_entry)
        form_layout.addRow("Student Number:", self.student_number_entry)
        form_layout.addRow("Course:", self.course_entry)
        form_layout.addRow("Department:", self.department_entry)
        
        # RFID Tag field with Scan button
        rfid_layout = QHBoxLayout()
        rfid_layout.addWidget(self.rfid_tag_entry)
        self.scan_rfid_button_student = QPushButton("Scan RFID Tag")
        rfid_layout.addWidget(self.scan_rfid_button_student)
        form_layout.addRow("RFID Tag:", rfid_layout)

        form_layout_container.addLayout(form_layout)

        student_buttons_layout = QHBoxLayout()
        self.add_student_button = QPushButton("Add Student")
        self.update_student_button = QPushButton("Update Student")
        self.clear_student_form_button = QPushButton("Clear Form")
        student_buttons_layout.addWidget(self.add_student_button)
        student_buttons_layout.addWidget(self.update_student_button)
        student_buttons_layout.addWidget(self.clear_student_form_button)
        form_layout_container.addLayout(student_buttons_layout)
        form_group.setLayout(form_layout_container)

        # Right side: Students Table
        table_group = QGroupBox("Registered Students")
        table_layout = QVBoxLayout()
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(7) # ID, Name, Student No, Course, Dept, RFID, Actions
        self.students_table.setHorizontalHeaderLabels(["ID", "Name", "Student No.", "Course", "Department", "RFID Tag", "Created At"])
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.students_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.students_table.setSelectionBehavior(QTableWidget.SelectRows)
        table_layout.addWidget(self.students_table)
        table_group.setLayout(table_layout)

        main_layout.addWidget(form_group, 1) # Form takes 1 part of stretch
        main_layout.addWidget(table_group, 2) # Table takes 2 parts of stretch

        # Connect buttons
        self.add_student_button.clicked.connect(self._add_student)
        self.update_student_button.clicked.connect(self._update_student)
        self.clear_student_form_button.clicked.connect(self._clear_student_form)
        self.students_table.itemDoubleClicked.connect(self._load_student_data_to_form)
        self.scan_rfid_button_student.clicked.connect(self._on_scan_rfid_for_student_clicked) # Connect the new button

        return student_tab

    @pyqtSlot(str)
    def update_rfid_tag_entry_for_new_student(self, tag_id):
        print(f"AdminDashboardScreen: Received tag to update UI: {tag_id}")
        self.rfid_tag_entry.setText(tag_id)
        if not tag_id:
            QMessageBox.warning(self, "RFID Scan", "Failed to scan RFID tag or scan was cancelled.")

    def _on_scan_rfid_for_student_clicked(self):
        print("AdminDashboardScreen: 'Scan RFID for Student' button clicked.")
        self.rfid_tag_entry.clear() # Clear previous tag before new scan
        QMessageBox.information(self, "RFID Scan", "Please scan the student's RFID tag now.")
        self.admin_controller.handle_scan_tag_for_new_student_button()

    def _clear_student_form(self):
        self.student_id_entry.setText("N/A")
        self.student_name_entry.clear()
        self.student_number_entry.clear()
        self.course_entry.clear()
        self.department_entry.clear()
        self.rfid_tag_entry.clear()
        self.students_table.clearSelection()

    def _load_student_data_to_form(self):
        selected_rows = self.students_table.selectedItems()
        if not selected_rows:
            self._clear_student_form()
            return
        
        row = selected_rows[0].row()
        self.student_id_entry.setText(self.students_table.item(row, 0).text())
        self.student_name_entry.setText(self.students_table.item(row, 1).text())
        self.student_number_entry.setText(self.students_table.item(row, 2).text())
        self.course_entry.setText(self.students_table.item(row, 3).text())
        self.department_entry.setText(self.students_table.item(row, 4).text())
        self.rfid_tag_entry.setText(self.students_table.item(row, 5).text())

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
            self.admin_controller.load_students() 
        else:
            QMessageBox.critical(self, "Error", "Failed to add student. Check logs, ensure RFID is unique, or student exists.")

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
            self.admin_controller.load_students()
        else:
            QMessageBox.critical(self, "Error", "Failed to update student. Check logs or ensure RFID uniqueness.")

    def _delete_student(self):
        student_id_text = self.student_id_entry.text().replace("Selected ID: ", "")
        if student_id_text == "N/A":
            QMessageBox.warning(self, "Selection Error", "Please select a student to delete.")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete student ID {student_id_text}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            student_id = int(student_id_text)
            if self.admin_controller.delete_student(student_id):
                QMessageBox.information(self, "Success", "Student deleted successfully.")
                self._clear_student_form()
                self.load_students_data()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete student. Check logs or if student has related consultations.")

    # -------------------- Faculty Tab --------------------
    def _create_faculty_tab(self):
        faculty_tab = QWidget()
        layout = QHBoxLayout(faculty_tab)

        # Form Group
        form_group = QGroupBox("Faculty Details")
        form_layout = QFormLayout()

        self.faculty_id_label = QLabel("Selected ID: N/A")
        self.faculty_name_edit = QLineEdit()
        self.faculty_dept_edit = QLineEdit()
        self.faculty_ble_edit = QLineEdit()
        self.faculty_office_edit = QLineEdit()
        self.faculty_contact_edit = QLineEdit()
        # current_status is usually managed by BLE, but admin might override. For now, read-only display or not editable.

        form_layout.addRow(self.faculty_id_label)
        form_layout.addRow("Name:", self.faculty_name_edit)
        form_layout.addRow("Department:", self.faculty_dept_edit)
        form_layout.addRow("BLE Identifier:", self.faculty_ble_edit)
        form_layout.addRow("Office Location:", self.faculty_office_edit)
        form_layout.addRow("Contact Details:", self.faculty_contact_edit)

        self.faculty_add_button = QPushButton("Add Faculty")
        self.faculty_update_button = QPushButton("Update Faculty")
        self.faculty_delete_button = QPushButton("Delete Faculty")
        self.faculty_clear_button = QPushButton("Clear Fields")

        self.faculty_add_button.clicked.connect(self._handle_add_faculty)
        self.faculty_update_button.clicked.connect(self._handle_update_faculty)
        self.faculty_delete_button.clicked.connect(self._handle_delete_faculty)
        self.faculty_clear_button.clicked.connect(self._clear_faculty_fields)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.faculty_add_button)
        button_layout.addWidget(self.faculty_update_button)
        button_layout.addWidget(self.faculty_delete_button)
        button_layout.addWidget(self.faculty_clear_button)
        form_layout.addRow(button_layout)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group, 1)

        # Table Group
        table_group = QGroupBox("Existing Faculty")
        table_layout = QVBoxLayout()
        self.faculty_table = self._create_table(["ID", "Name", "Department", "BLE ID", "Office", "Contact", "Status", "Status Updated"])
        self.faculty_table.itemSelectionChanged.connect(self._load_faculty_to_form)
        
        self.faculty_refresh_button = QPushButton("Refresh List")
        self.faculty_refresh_button.clicked.connect(self.load_faculty_data)

        table_layout.addWidget(self.faculty_refresh_button)
        table_layout.addWidget(self.faculty_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group, 2)

    def _clear_faculty_fields(self):
        self.faculty_id_label.setText("Selected ID: N/A")
        self.faculty_name_edit.clear()
        self.faculty_dept_edit.clear()
        self.faculty_ble_edit.clear()
        self.faculty_office_edit.clear()
        self.faculty_contact_edit.clear()
        self.faculty_table.clearSelection()

    def _load_faculty_to_form(self):
        selected_rows = self.faculty_table.selectedItems()
        if not selected_rows:
            self._clear_faculty_fields()
            return
        
        row = selected_rows[0].row()
        self.faculty_id_label.setText(f"Selected ID: {self.faculty_table.item(row, 0).text()}")
        self.faculty_name_edit.setText(self.faculty_table.item(row, 1).text())
        self.faculty_dept_edit.setText(self.faculty_table.item(row, 2).text())
        self.faculty_ble_edit.setText(self.faculty_table.item(row, 3).text())
        self.faculty_office_edit.setText(self.faculty_table.item(row, 4).text())
        self.faculty_contact_edit.setText(self.faculty_table.item(row, 5).text())
        # Status is usually not directly edited here by admin, it's more for info

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
            self.load_faculty_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to add faculty. Check logs or ensure BLE ID is unique.")

    def _handle_update_faculty(self):
        faculty_id_text = self.faculty_id_label.text().replace("Selected ID: ", "")
        if faculty_id_text == "N/A":
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
            self.load_faculty_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to update faculty. Check logs.")

    def _handle_delete_faculty(self):
        faculty_id_text = self.faculty_id_label.text().replace("Selected ID: ", "")
        if faculty_id_text == "N/A":
            QMessageBox.warning(self, "Selection Error", "Please select a faculty member to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete faculty ID {faculty_id_text}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            faculty_id = int(faculty_id_text)
            if self.admin_controller.delete_faculty(faculty_id):
                QMessageBox.information(self, "Success", "Faculty deleted successfully.")
                self._clear_faculty_fields()
                self.load_faculty_data()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete faculty. Check logs or if faculty has related consultations.")

    # -------------------- Consultation Tab --------------------
    def _create_consultations_tab(self):
        consultation_tab = QWidget()
        layout = QVBoxLayout(consultation_tab)
        
        table_group = QGroupBox("All Consultation Requests")
        table_layout = QVBoxLayout()
        
        self.consultation_table = self._create_table([
            "ID", "Student Name (ID)", "Faculty Name (ID)", "Course Code", 
            "Subject", "Details", "Status", "Requested At", "Updated At"
        ])
        # Make consultation table wider for more details
        self.consultation_table.setColumnWidth(0, 50) # ID
        self.consultation_table.setColumnWidth(1, 200) # Student
        self.consultation_table.setColumnWidth(2, 200) # Faculty
        self.consultation_table.setColumnWidth(3, 100) # Course
        self.consultation_table.setColumnWidth(4, 200) # Subject
        self.consultation_table.setColumnWidth(5, 300) # Details
        self.consultation_table.setColumnWidth(6, 100) # Status
        self.consultation_table.setColumnWidth(7, 150) # Requested
        self.consultation_table.setColumnWidth(8, 150) # Updated
        
        self.consultation_refresh_button = QPushButton("Refresh List")
        self.consultation_refresh_button.clicked.connect(self.load_consultations_data)

        table_layout.addWidget(self.consultation_refresh_button)
        table_layout.addWidget(self.consultation_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

    # -------------------- Data Loading Functions --------------------
    def load_all_data(self):
        self.load_students_data()
        self.load_faculty_data()
        self.load_consultations_data()

    def load_students_data(self):
        students = self.admin_controller.get_all_students()
        self.students_table.setRowCount(0) 
        if students:
            # Headers: ["ID", "Name", "Student No.", "Course", "Department", "RFID Tag", "Created At"]
            # student_data keys from DB: student_id, name, student_number, course, department, rfid_tag, created_at
            for row_num, student_data in enumerate(students):
                self.students_table.insertRow(row_num)
                self.students_table.setItem(row_num, 0, QTableWidgetItem(str(student_data.get('student_id', ''))))
                self.students_table.setItem(row_num, 1, QTableWidgetItem(student_data.get('name', '')))
                self.students_table.setItem(row_num, 2, QTableWidgetItem(student_data.get('student_number', ''))) # Use actual data
                self.students_table.setItem(row_num, 3, QTableWidgetItem(student_data.get('course', '')))       # Use actual data
                self.students_table.setItem(row_num, 4, QTableWidgetItem(student_data.get('department', '')))
                self.students_table.setItem(row_num, 5, QTableWidgetItem(student_data.get('rfid_tag', '')))
                created_at = student_data.get('created_at')
                self.students_table.setItem(row_num, 6, QTableWidgetItem(str(created_at) if created_at else ''))
        self.students_table.resizeColumnsToContents()

    def load_faculty_data(self):
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
                self.faculty_table.setItem(row_num, 6, QTableWidgetItem(faculty_data.get('current_status', '')))
                status_updated_at = faculty_data.get('status_updated_at')
                self.faculty_table.setItem(row_num, 7, QTableWidgetItem(str(status_updated_at) if status_updated_at else ''))
        self.faculty_table.resizeColumnsToContents()

    def load_consultations_data(self):
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
                self.consultation_table.setItem(row_num, 5, QTableWidgetItem(consult_data.get('request_details', '')))
                self.consultation_table.setItem(row_num, 6, QTableWidgetItem(consult_data.get('status', '')))
                
                requested_at = consult_data.get('requested_at')
                self.consultation_table.setItem(row_num, 7, QTableWidgetItem(str(requested_at) if requested_at else ''))
                updated_at = consult_data.get('updated_at')
                self.consultation_table.setItem(row_num, 8, QTableWidgetItem(str(updated_at) if updated_at else ''))
        # No resizeColumnsToContents here due to explicit widths, but ensure last section stretches.
        self.consultation_table.horizontalHeader().setStretchLastSection(True)


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