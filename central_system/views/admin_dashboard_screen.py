from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class AdminDashboardScreen(QWidget):
    # Signals for controller interaction if needed later, for now direct calls
    # e.g., request_load_students = pyqtSignal()

    def __init__(self, admin_controller):
        super().__init__()
        self.admin_controller = admin_controller
        self.setWindowTitle("Admin Dashboard - ConsultEase")
        self.setGeometry(150, 150, 1200, 700) # Adjusted size
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("ConsultEase System Administration")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create tabs
        self.student_tab = QWidget()
        self.faculty_tab = QWidget()
        self.consultation_tab = QWidget()

        self.tabs.addTab(self.student_tab, "Manage Students")
        self.tabs.addTab(self.faculty_tab, "Manage Faculty")
        self.tabs.addTab(self.consultation_tab, "View Consultations")

        # Setup each tab
        self._setup_student_tab()
        self._setup_faculty_tab()
        self._setup_consultation_tab()

        self.load_all_data() # Initial data load

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
    def _setup_student_tab(self):
        layout = QHBoxLayout(self.student_tab)
        
        # Form Group
        form_group = QGroupBox("Student Details")
        form_layout = QFormLayout()
        
        self.student_id_label = QLabel("Selected ID: N/A") # To show ID of selected student for update/delete
        self.student_rfid_edit = QLineEdit()
        self.student_name_edit = QLineEdit()
        self.student_dept_edit = QLineEdit()

        form_layout.addRow(self.student_id_label)
        form_layout.addRow("RFID Tag:", self.student_rfid_edit)
        form_layout.addRow("Name:", self.student_name_edit)
        form_layout.addRow("Department:", self.student_dept_edit)
        
        self.student_add_button = QPushButton("Add Student")
        self.student_update_button = QPushButton("Update Student")
        self.student_delete_button = QPushButton("Delete Student")
        self.student_clear_button = QPushButton("Clear Fields")

        self.student_add_button.clicked.connect(self._handle_add_student)
        self.student_update_button.clicked.connect(self._handle_update_student)
        self.student_delete_button.clicked.connect(self._handle_delete_student)
        self.student_clear_button.clicked.connect(self._clear_student_fields)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.student_add_button)
        button_layout.addWidget(self.student_update_button)
        button_layout.addWidget(self.student_delete_button)
        button_layout.addWidget(self.student_clear_button)
        form_layout.addRow(button_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group, 1) # Form takes 1 part of stretch

        # Table Group
        table_group = QGroupBox("Existing Students")
        table_layout = QVBoxLayout()
        self.student_table = self._create_table(["ID", "RFID Tag", "Name", "Department", "Created At"])
        self.student_table.itemSelectionChanged.connect(self._load_student_to_form)
        
        self.student_refresh_button = QPushButton("Refresh List")
        self.student_refresh_button.clicked.connect(self.load_students_data)
        
        table_layout.addWidget(self.student_refresh_button)
        table_layout.addWidget(self.student_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group, 2) # Table takes 2 parts of stretch

    def _clear_student_fields(self):
        self.student_id_label.setText("Selected ID: N/A")
        self.student_rfid_edit.clear()
        self.student_name_edit.clear()
        self.student_dept_edit.clear()
        self.student_table.clearSelection()

    def _load_student_to_form(self):
        selected_rows = self.student_table.selectedItems()
        if not selected_rows:
            self._clear_student_fields()
            return
        
        row = selected_rows[0].row()
        self.student_id_label.setText(f"Selected ID: {self.student_table.item(row, 0).text()}")
        self.student_rfid_edit.setText(self.student_table.item(row, 1).text())
        self.student_name_edit.setText(self.student_table.item(row, 2).text())
        self.student_dept_edit.setText(self.student_table.item(row, 3).text())

    def _handle_add_student(self):
        rfid = self.student_rfid_edit.text().strip()
        name = self.student_name_edit.text().strip()
        dept = self.student_dept_edit.text().strip()
        if not rfid or not name:
            QMessageBox.warning(self, "Input Error", "RFID Tag and Name are required.")
            return
        if self.admin_controller.add_student(rfid, name, dept):
            QMessageBox.information(self, "Success", "Student added successfully.")
            self._clear_student_fields()
            self.load_students_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to add student. Check logs or ensure RFID is unique.")

    def _handle_update_student(self):
        student_id_text = self.student_id_label.text().replace("Selected ID: ", "")
        if student_id_text == "N/A":
            QMessageBox.warning(self, "Selection Error", "Please select a student to update.")
            return
        student_id = int(student_id_text)
        rfid = self.student_rfid_edit.text().strip()
        name = self.student_name_edit.text().strip()
        dept = self.student_dept_edit.text().strip()
        if not rfid or not name:
            QMessageBox.warning(self, "Input Error", "RFID Tag and Name are required.")
            return
        if self.admin_controller.update_student(student_id, rfid, name, dept):
            QMessageBox.information(self, "Success", "Student updated successfully.")
            self._clear_student_fields()
            self.load_students_data()
        else:
            QMessageBox.critical(self, "Error", "Failed to update student. Check logs.")

    def _handle_delete_student(self):
        student_id_text = self.student_id_label.text().replace("Selected ID: ", "")
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
                self._clear_student_fields()
                self.load_students_data()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete student. Check logs or if student has related consultations.")

    # -------------------- Faculty Tab --------------------
    def _setup_faculty_tab(self):
        layout = QHBoxLayout(self.faculty_tab)

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
    def _setup_consultation_tab(self):
        layout = QVBoxLayout(self.consultation_tab)
        
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
        self.student_table.setRowCount(0) # Clear existing rows
        if students:
            for row_num, student_data in enumerate(students):
                self.student_table.insertRow(row_num)
                self.student_table.setItem(row_num, 0, QTableWidgetItem(str(student_data.get('student_id', ''))))
                self.student_table.setItem(row_num, 1, QTableWidgetItem(student_data.get('rfid_tag', '')))
                self.student_table.setItem(row_num, 2, QTableWidgetItem(student_data.get('name', '')))
                self.student_table.setItem(row_num, 3, QTableWidgetItem(student_data.get('department', '')))
                created_at = student_data.get('created_at')
                self.student_table.setItem(row_num, 4, QTableWidgetItem(str(created_at) if created_at else ''))
        self.student_table.resizeColumnsToContents()


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