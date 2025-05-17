import logging
from PyQt5.QtCore import QObject, pyqtSignal

class AdminController(QObject):
    students_data_changed = pyqtSignal()
    faculty_data_changed = pyqtSignal()
    consultations_data_changed = pyqtSignal()
    rfid_tag_scanned_for_student = pyqtSignal(str) # Signal to send the scanned tag to the view

    def __init__(self, db_service, rfid_service):
        super().__init__()
        self.db_service = db_service
        self.rfid_service = rfid_service
        self._scanned_tag_for_new_student = None
        logging.info("AdminController initialized with direct call pattern.")

    def _emit_all_data_changed_signals(self):
        self.students_data_changed.emit()
        self.faculty_data_changed.emit()
        self.consultations_data_changed.emit()

    def load_all_data(self):
        self.load_students()
        self.load_faculty()
        self.load_consultations()

    # --- RFID Tag Scanning for New Student ---
    def handle_scan_tag_for_new_student_button(self):
        """
        Called when the 'Scan RFID' button is pressed in the Add Student form.
        """
        print("AdminController: Initiating single tag capture.")
        self.rfid_service.start_capture_single_tag(self._on_tag_scanned_for_new_student)

    def _on_tag_scanned_for_new_student(self, tag_id):
        """
        Callback for RFIDService when a tag is captured for a new student.
        """
        if tag_id:
            print(f"AdminController: Tag captured for new student: {tag_id}")
            self._scanned_tag_for_new_student = tag_id
            self.rfid_tag_scanned_for_student.emit(tag_id)
            # It's important to stop capture mode if it's a one-time deal
            # self.rfid_service.stop_capture_single_tag() # Assuming RFIDService handles this or provides a way
        else:
            print("AdminController: Single tag capture failed or was cancelled.")
            self.rfid_tag_scanned_for_student.emit("") # Emit empty string or handle error appropriately

    def get_scanned_tag_for_new_student(self):
        """
        Allows the view to retrieve the last scanned tag if needed,
        though signaling is preferred.
        """
        return self._scanned_tag_for_new_student
    # --- End RFID Tag Scanning ---

    # --- Student Management --- #
    def get_all_students(self):
        try:
            return self.db_service.get_all_students()
        except Exception as e:
            logging.error(f"AdminController: Error getting all students: {e}")
            return []

    def add_student(self, rfid_tag: str, name: str, student_number: str = None, course: str = None, department: str = None):
        try:
            student = self.db_service.add_student(rfid_tag, name, student_number, course, department)
            if student:
                logging.info(f"AdminController: Student added via admin: {name} ({rfid_tag})")
                # self.students_data_changed.emit() # Emit signal after successful add
                return True
            logging.warning(f"AdminController: Failed to add student {name} via db_service.")
            return False
        except Exception as e:
            logging.error(f"AdminController: Error adding student {name}: {e}")
            return False

    def update_student(self, student_id: int, rfid_tag: str, name: str, student_number: str = None, course: str = None, department: str = None):
        try:
            student = self.db_service.update_student(student_id, rfid_tag, name, student_number, course, department)
            if student:
                logging.info(f"AdminController: Student updated via admin: ID {student_id}")
                # self.students_data_changed.emit() # Emit signal after successful update
                return True
            logging.warning(f"AdminController: Failed to update student ID {student_id} via db_service.")
            return False
        except Exception as e:
            logging.error(f"AdminController: Error updating student ID {student_id}: {e}")
            return False

    def delete_student(self, student_id):
        try:
            if self.db_service.delete_student(student_id):
                logging.info(f"AdminController: Student deleted via admin: ID {student_id}")
                return True
            logging.warning(f"AdminController: Failed to delete student ID {student_id} via db_service.")
            return False
        except Exception as e:
            logging.error(f"AdminController: Error deleting student ID {student_id}: {e}")
            return False

    def load_students(self):
        self._emit_all_data_changed_signals()

    # --- Faculty Management --- #
    def get_all_faculty(self):
        try:
            return self.db_service.get_all_faculty()
        except Exception as e:
            logging.error(f"AdminController: Error getting all faculty: {e}")
            return []

    def add_faculty(self, name, department, ble_identifier, office_location=None, contact_details=None, current_status='Unavailable'):
        try:
            # Note: admin_dashboard_screen doesn't pass current_status, so using default from db_service.add_faculty
            faculty = self.db_service.add_faculty(name, department, ble_identifier, office_location, contact_details, current_status)
            if faculty:
                logging.info(f"AdminController: Faculty added via admin: {name}")
                return True
            logging.warning(f"AdminController: Failed to add faculty {name} via db_service.")
            return False
        except Exception as e:
            logging.error(f"AdminController: Error adding faculty {name}: {e}")
            return False

    def update_faculty(self, faculty_id, name, department, ble_identifier, office_location=None, contact_details=None):
        try:
            # This should call update_faculty_details in db_service
            faculty = self.db_service.update_faculty_details(faculty_id, name, department, ble_identifier, office_location, contact_details)
            if faculty:
                logging.info(f"AdminController: Faculty updated via admin: ID {faculty_id}")
                return True
            logging.warning(f"AdminController: Failed to update faculty ID {faculty_id} via db_service.")
            return False
        except Exception as e:
            logging.error(f"AdminController: Error updating faculty ID {faculty_id}: {e}")
            return False

    def delete_faculty(self, faculty_id):
        try:
            if self.db_service.delete_faculty(faculty_id):
                logging.info(f"AdminController: Faculty deleted via admin: ID {faculty_id}")
                return True
            logging.warning(f"AdminController: Failed to delete faculty ID {faculty_id} via db_service.")
            return False
        except Exception as e:
            logging.error(f"AdminController: Error deleting faculty ID {faculty_id}: {e}")
            return False

    def load_faculty(self):
        self._emit_all_data_changed_signals()

    # --- Consultation Management --- #
    def get_all_consultations(self):
        try:
            return self.db_service.get_all_consultations_with_details() 
        except Exception as e:
            logging.error(f"AdminController: Error getting all consultations: {e}")
            return []

    def load_consultations(self):
        self._emit_all_data_changed_signals()

    def cleanup(self):
        # Add any cleanup logic if AdminController itself manages resources
        logging.info("AdminController cleaned up (if applicable).") 