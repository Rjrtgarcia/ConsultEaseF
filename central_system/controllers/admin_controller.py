from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QMessageBox
import logging

class AdminController(QObject):
    def __init__(self, db_service, admin_view):
        super().__init__()
        self.db_service = db_service
        self.admin_view = admin_view

        # Connect signals from the view to controller slots
        self.admin_view.request_add_student.connect(self.add_student)
        self.admin_view.request_add_faculty.connect(self.add_faculty)
        self.admin_view.request_load_students.connect(self.load_students_for_view)
        self.admin_view.request_load_faculty.connect(self.load_faculty_for_view)
        # self.admin_view.request_admin_logout is handled by main_app to switch views

        logging.info("AdminController initialized.")

    @pyqtSlot(dict)
    def add_student(self, student_data: dict):
        logging.info(f"AdminController: Attempting to add student: {student_data}")
        try:
            added = self.db_service.add_student(
                rfid_tag=student_data['rfid_tag'], 
                name=student_data['name'], 
                department=student_data.get('department')
            )
            if added:
                QMessageBox.information(self.admin_view, "Success", "Student added successfully!")
                self.admin_view.student_name_input.clear()
                self.admin_view.student_rfid_input.clear()
                self.admin_view.student_dept_input.clear()
                self.load_students_for_view() # Refresh table
            else:
                QMessageBox.warning(self.admin_view, "DB Error", "Failed to add student. RFID tag might already exist.")
        except Exception as e:
            logging.error(f"AdminController: Error adding student: {e}")
            QMessageBox.critical(self.admin_view, "Error", f"An error occurred: {e}")

    @pyqtSlot(dict)
    def add_faculty(self, faculty_data: dict):
        logging.info(f"AdminController: Attempting to add faculty: {faculty_data}")
        try:
            added = self.db_service.add_faculty(
                name=faculty_data['name'], 
                department=faculty_data['department'], 
                ble_identifier=faculty_data['ble_identifier'],
                office_location=faculty_data.get('office_location')
            )
            if added:
                QMessageBox.information(self.admin_view, "Success", "Faculty member added successfully!")
                self.admin_view.faculty_name_input.clear()
                self.admin_view.faculty_dept_input.clear()
                self.admin_view.faculty_ble_input.clear()
                self.admin_view.faculty_office_input.clear()
                self.load_faculty_for_view() # Refresh table
            else:
                QMessageBox.warning(self.admin_view, "DB Error", "Failed to add faculty. BLE Identifier might already exist.")
        except Exception as e:
            logging.error(f"AdminController: Error adding faculty: {e}")
            QMessageBox.critical(self.admin_view, "Error", f"An error occurred: {e}")

    @pyqtSlot()
    def load_students_for_view(self):
        logging.info("AdminController: Loading students for view.")
        try:
            students = self.db_service.get_all_students()
            self.admin_view.populate_students_table(students if students else [])
        except Exception as e:
            logging.error(f"AdminController: Error loading students: {e}")
            self.admin_view.populate_students_table([])
            # QMessageBox.warning(self.admin_view, "Load Error", "Could not load student list.")

    @pyqtSlot()
    def load_faculty_for_view(self):
        logging.info("AdminController: Loading faculty for view.")
        try:
            faculty = self.db_service.get_all_faculty()
            self.admin_view.populate_faculty_table(faculty if faculty else [])
        except Exception as e:
            logging.error(f"AdminController: Error loading faculty: {e}")
            self.admin_view.populate_faculty_table([])
            # QMessageBox.warning(self.admin_view, "Load Error", "Could not load faculty list.")

    def cleanup(self):
        logging.info("AdminController cleaned up.") 