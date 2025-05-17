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

    # --- Student Management --- #
    def get_all_students(self):
        try:
            return self.db_service.get_all_students()
        except Exception as e:
            logging.error(f"AdminController: Error getting all students: {e}")
            return []

    def add_student(self, rfid_tag, name, department):
        try:
            student = self.db_service.add_student(rfid_tag, name, department)
            if student:
                logging.info(f"AdminController: Student added: {name} ({rfid_tag})")
                return True
            return False
        except Exception as e:
            logging.error(f"AdminController: Error adding student {name}: {e}")
            return False

    def update_student(self, student_id, rfid_tag, name, department):
        try:
            # The DatabaseService needs an update_student method
            # For now, let's assume it will exist and work similarly to add_student or faculty update
            student = self.db_service.update_student(student_id, rfid_tag, name, department)
            if student:
                logging.info(f"AdminController: Student updated: ID {student_id}")
                return True
            return False
        except Exception as e:
            logging.error(f"AdminController: Error updating student ID {student_id}: {e}")
            return False

    def delete_student(self, student_id):
        try:
            # The DatabaseService needs a delete_student method
            if self.db_service.delete_student(student_id):
                logging.info(f"AdminController: Student deleted: ID {student_id}")
                return True
            return False
        except Exception as e:
            logging.error(f"AdminController: Error deleting student ID {student_id}: {e}")
            # Could be due to foreign key constraints (consultations)
            return False

    # --- Faculty Management --- #
    def get_all_faculty(self):
        try:
            return self.db_service.get_all_faculty()
        except Exception as e:
            logging.error(f"AdminController: Error getting all faculty: {e}")
            return []

    def add_faculty(self, name, department, ble_identifier, office_location=None, contact_details=None):
        try:
            faculty = self.db_service.add_faculty(name, department, ble_identifier, office_location, contact_details)
            if faculty:
                logging.info(f"AdminController: Faculty added: {name}")
                return True
            return False
        except Exception as e:
            logging.error(f"AdminController: Error adding faculty {name}: {e}")
            return False

    def update_faculty(self, faculty_id, name, department, ble_identifier, office_location=None, contact_details=None):
        try:
            # The DatabaseService needs an update_faculty method that can update all these fields
            # The current one `update_faculty_status` is only for status.
            # Let's assume a more general `update_faculty_details` or similar exists / will be added.
            faculty = self.db_service.update_faculty_details(faculty_id, name, department, ble_identifier, office_location, contact_details)
            if faculty:
                logging.info(f"AdminController: Faculty updated: ID {faculty_id}")
                return True
            return False
        except Exception as e:
            logging.error(f"AdminController: Error updating faculty ID {faculty_id}: {e}")
            return False

    def delete_faculty(self, faculty_id):
        try:
            # The DatabaseService needs a delete_faculty method
            if self.db_service.delete_faculty(faculty_id):
                logging.info(f"AdminController: Faculty deleted: ID {faculty_id}")
                return True
            return False
        except Exception as e:
            logging.error(f"AdminController: Error deleting faculty ID {faculty_id}: {e}")
            # Could be due to foreign key constraints (consultations)
            return False

    # --- Consultation Management --- #
    def get_all_consultations(self):
        try:
            # This method in DatabaseService should join with student and faculty tables to get names
            return self.db_service.get_all_consultations_with_details() 
        except Exception as e:
            logging.error(f"AdminController: Error getting all consultations: {e}")
            return [] 