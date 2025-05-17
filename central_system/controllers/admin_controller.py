import logging

class AdminController:
    def __init__(self, db_service):
        self.db_service = db_service
        logging.info("AdminController initialized with direct call pattern.")

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
                logging.info(f"AdminController: Student added via admin: {name} ({rfid_tag})")
                return True
            logging.warning(f"AdminController: Failed to add student {name} via db_service.")
            return False
        except Exception as e:
            logging.error(f"AdminController: Error adding student {name}: {e}")
            return False

    def update_student(self, student_id, rfid_tag, name, department):
        try:
            student = self.db_service.update_student(student_id, rfid_tag, name, department)
            if student:
                logging.info(f"AdminController: Student updated via admin: ID {student_id}")
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

    # --- Consultation Management --- #
    def get_all_consultations(self):
        try:
            return self.db_service.get_all_consultations_with_details() 
        except Exception as e:
            logging.error(f"AdminController: Error getting all consultations: {e}")
            return []

    def cleanup(self):
        # Add any cleanup logic if AdminController itself manages resources
        logging.info("AdminController cleaned up (if applicable).") 