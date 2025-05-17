import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

# Import models once they are defined, assuming they are in ../models
# from ..models import Student, Faculty # This relative import might need adjustment based on execution context

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Replace with your actual database connection details
DB_NAME = "consultease_db"
DB_USER = "consultease_user"
DB_PASSWORD = "app_password" # Make sure to use a strong password and manage it securely
DB_HOST = "localhost"
DB_PORT = "5432"

class DatabaseService:
    def __init__(self):
        self.conn_params = {
            "dbname": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "host": DB_HOST,
            "port": DB_PORT,
        }
        self._ensure_tables_exist()

    def _get_connection(self):
        """Establishes and returns a database connection."""
        try:
            conn = psycopg2.connect(**self.conn_params)
            return conn
        except psycopg2.Error as e:
            logging.error(f"Error connecting to PostgreSQL database: {e}")
            raise

    def _execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """Helper function to execute SQL queries."""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if commit:
                    conn.commit()
                    if cur.description: # Check if there are columns to fetch (e.g., RETURNING clause)
                        return cur.fetchone() if fetch_one else (cur.fetchall() if fetch_all else None)
                    return None # For non-returning commits like UPDATE without RETURNING
                if fetch_one:
                    return cur.fetchone()
                if fetch_all:
                    return cur.fetchall()
            return None # Should not reach here if fetch_one or fetch_all is True and query is valid
        except psycopg2.Error as e:
            logging.error(f"Database query error: {e}\nQuery: {query}\nParams: {params}")
            if conn and not commit: # Rollback if it was not a commit operation that failed
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def _ensure_tables_exist(self):
        """Checks if the required tables exist and creates them if not."""
        # This matches the schema in documentation/database_schema.md
        create_students_table_sql = """
        CREATE TABLE IF NOT EXISTS students (
            student_id SERIAL PRIMARY KEY,
            rfid_tag VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            department VARCHAR(100),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_students_rfid_tag ON students(rfid_tag);
        """

        create_faculty_table_sql = """
        CREATE TABLE IF NOT EXISTS faculty (
            faculty_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            department VARCHAR(100) NOT NULL,
            ble_identifier VARCHAR(100) UNIQUE NOT NULL,
            office_location VARCHAR(100),
            contact_details TEXT,
            current_status VARCHAR(20) DEFAULT 'Unavailable',
            status_updated_at TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_faculty_ble_identifier ON faculty(ble_identifier);
        CREATE INDEX IF NOT EXISTS idx_faculty_department ON faculty(department);
        """

        create_consultations_table_sql = """
        CREATE TABLE IF NOT EXISTS consultations (
            consultation_id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
            faculty_id INTEGER NOT NULL REFERENCES faculty(faculty_id) ON DELETE CASCADE,
            course_code VARCHAR(50),
            subject VARCHAR(255),
            request_details TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'Pending',
            requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_consultations_student_id ON consultations(student_id);
        CREATE INDEX IF NOT EXISTS idx_consultations_faculty_id ON consultations(faculty_id);
        CREATE INDEX IF NOT EXISTS idx_consultations_status ON consultations(status);
        """

        try:
            logging.info("Ensuring database tables exist...")
            self._execute_query(create_students_table_sql, commit=True)
            self._execute_query(create_faculty_table_sql, commit=True)
            self._execute_query(create_consultations_table_sql, commit=True)
            logging.info("Database tables checked/created successfully.")
            self._seed_initial_data() # Add call to seeding method
        except psycopg2.Error as e:
            logging.error(f"Error creating database tables: {e}")
            # If tables can't be created, the service is likely unusable.
            raise RuntimeError(f"Failed to create essential database tables: {e}")

    def _seed_initial_data(self):
        """Seeds the database with initial sample data if tables are empty."""
        try:
            # Check if students table is empty
            if not self.get_all_students():
                logging.info("Students table is empty. Seeding initial student data...")
                self.add_student(
                    rfid_tag="SIM_STU_001",
                    name="John Doe (Sample)",
                    department="Computer Science"
                )
                logging.info("Sample student added.")

            # Check if faculty table is empty
            if not self.get_all_faculty(): # Assuming get_all_faculty returns a list
                logging.info("Faculty table is empty. Seeding initial faculty data...")
                self.add_faculty(
                    name="Dr. Jane Smith (Sample)",
                    department="Software Engineering",
                    ble_identifier="FAC_BLE_001_SAMPLE",
                    office_location="Tech Park Room 101",
                    contact_details="jane.smith@example.com",
                    current_status="Available"
                )
                logging.info("Sample faculty added.")
            
            logging.info("Initial data seeding check complete.")

        except Exception as e:
            logging.error(f"Error during initial data seeding: {e}")
            # Depending on the severity, you might want to raise this or just log it
            # For now, just logging, as failure to seed might not be critical for app startup

    # --- Student Management ---
    def add_student(self, rfid_tag: str, name: str, department: str = None):
        """Adds a new student to the database."""
        query = sql.SQL("""
            INSERT INTO students (rfid_tag, name, department, updated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING student_id, rfid_tag, name, department, created_at, updated_at;
        """)
        try:
            now = datetime.now()
            return self._execute_query(query, (rfid_tag, name, department, now), fetch_one=True, commit=True)
        except psycopg2.IntegrityError as e:
            logging.warning(f"Could not add student with RFID {rfid_tag}. It might already exist. Error: {e}")
            return None # Or re-raise a custom exception

    def get_student_by_rfid(self, rfid_tag: str):
        """Retrieves a student by their RFID tag."""
        query = sql.SQL("SELECT * FROM students WHERE rfid_tag = %s;")
        return self._execute_query(query, (rfid_tag,), fetch_one=True)

    def get_student_by_id(self, student_id: int):
        """Retrieves a student by their ID."""
        query = sql.SQL("SELECT * FROM students WHERE student_id = %s;")
        return self._execute_query(query, (student_id,), fetch_one=True)

    def get_all_students(self):
        """Retrieves all students from the database."""
        query = sql.SQL("SELECT student_id, rfid_tag, name, department, created_at FROM students ORDER BY name;")
        return self._execute_query(query, fetch_all=True)

    def update_student(self, student_id: int, rfid_tag: str, name: str, department: str = None):
        """Updates an existing student's details in the database."""
        query = sql.SQL("""
            UPDATE students
            SET rfid_tag = %s, name = %s, department = %s, updated_at = %s
            WHERE student_id = %s
            RETURNING student_id, rfid_tag, name, department, updated_at;
        """)
        try:
            now = datetime.now()
            return self._execute_query(query, (rfid_tag, name, department, now, student_id), fetch_one=True, commit=True)
        except psycopg2.IntegrityError as e: # Catch issues like duplicate RFID tag on update
            logging.error(f"Error updating student ID {student_id} due to integrity constraint: {e}")
            return None
        except Exception as e:
            logging.error(f"Error updating student ID {student_id}: {e}")
            return None

    def delete_student(self, student_id: int):
        """Deletes a student from the database. Returns True on success, False otherwise."""
        # Note: ON DELETE CASCADE for consultations related to this student is handled by the DB schema.
        query = sql.SQL("DELETE FROM students WHERE student_id = %s;")
        try:
            self._execute_query(query, (student_id,), commit=True) # No RETURNING needed for simple delete
            # To confirm deletion, we could check if execute_query affected rows, but basic success is usually enough
            # For simplicity, if no exception, assume success.
            logging.info(f"Student with ID {student_id} deleted successfully.")
            return True
        except psycopg2.Error as e: # Specific psycopg2 errors, e.g. foreign key if not cascaded
            logging.error(f"Database error deleting student ID {student_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error deleting student ID {student_id}: {e}")
            return False

    # --- Faculty Management (MVP: Add and Get) ---
    def add_faculty(self, name: str, department: str, ble_identifier: str,
                    office_location: str = None, contact_details: str = None,
                    current_status: str = 'Unavailable'):
        """Adds a new faculty member."""
        query = sql.SQL("""
            INSERT INTO faculty (name, department, ble_identifier, office_location, contact_details, current_status, status_updated_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING faculty_id, name, department, ble_identifier, office_location, contact_details, current_status, status_updated_at, created_at, updated_at;
        """)
        try:
            now = datetime.now()
            return self._execute_query(query, (name, department, ble_identifier, office_location, contact_details, current_status, now, now), fetch_one=True, commit=True)
        except psycopg2.IntegrityError as e:
            logging.warning(f"Could not add faculty {name} with BLE ID {ble_identifier}. It might already exist. Error: {e}")
            return None

    def get_faculty_by_id(self, faculty_id: int):
        """Retrieves a faculty member by their ID."""
        query = sql.SQL("SELECT * FROM faculty WHERE faculty_id = %s;")
        return self._execute_query(query, (faculty_id,), fetch_one=True)

    def get_all_faculty(self, name_filter: str = None, department_filter: str = None, status_filter: str = None):
        """Retrieves all faculty members, with optional filters."""
        base_query = "SELECT faculty_id, name, department, ble_identifier, office_location, current_status, status_updated_at FROM faculty"
        conditions = []
        params = []

        if name_filter:
            conditions.append("name ILIKE %s") # Case-insensitive search
            params.append(f"%{name_filter}%")
        if department_filter:
            conditions.append("department = %s")
            params.append(department_filter)
        if status_filter:
            conditions.append("current_status = %s")
            params.append(status_filter)

        if conditions:
            query_string = f"{base_query} WHERE {' AND '.join(conditions)}"
        else:
            query_string = base_query
        
        query_string += " ORDER BY name;" # Default sort by name
        
        query = sql.SQL(query_string)
        return self._execute_query(query, tuple(params) if params else None, fetch_all=True)

    def update_faculty_details(self, faculty_id: int, name: str, department: str, 
                               ble_identifier: str, office_location: str = None, 
                               contact_details: str = None):
        """Updates an existing faculty member's details (excluding status)."""
        query = sql.SQL("""
            UPDATE faculty 
            SET name = %s, department = %s, ble_identifier = %s, 
                office_location = %s, contact_details = %s, updated_at = %s
            WHERE faculty_id = %s
            RETURNING faculty_id, name, department, ble_identifier, office_location, contact_details, updated_at;
        """)
        try:
            now = datetime.now()
            return self._execute_query(query, (name, department, ble_identifier, office_location, contact_details, now, faculty_id), fetch_one=True, commit=True)
        except psycopg2.IntegrityError as e: # Catch issues like duplicate BLE ID
            logging.error(f"Error updating faculty ID {faculty_id} due to integrity constraint: {e}")
            return None
        except Exception as e:
            logging.error(f"Error updating faculty details for ID {faculty_id}: {e}")
            return None

    def delete_faculty(self, faculty_id: int):
        """Deletes a faculty member from the database. Returns True on success, False otherwise."""
        # Note: ON DELETE CASCADE for consultations related to this faculty is handled by the DB schema.
        query = sql.SQL("DELETE FROM faculty WHERE faculty_id = %s;")
        try:
            self._execute_query(query, (faculty_id,), commit=True)
            logging.info(f"Faculty with ID {faculty_id} deleted successfully.")
            return True
        except psycopg2.Error as e:
            logging.error(f"Database error deleting faculty ID {faculty_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error deleting faculty ID {faculty_id}: {e}")
            return False

    def update_faculty_status(self, faculty_id: int, new_status: str):
        """Updates the status of a faculty member."""
        # This method will be primarily called by the MQTT service when updates are received.
        query = sql.SQL("""
            UPDATE faculty
            SET current_status = %s, status_updated_at = %s, updated_at = %s
            WHERE faculty_id = %s
            RETURNING faculty_id, current_status, status_updated_at;
        """)
        try:
            now = datetime.now()
            return self._execute_query(query, (new_status, now, now, faculty_id), fetch_one=True, commit=True)
        except Exception as e:
            logging.error(f"Error updating faculty status for ID {faculty_id}: {e}")
            return None
            
    def update_faculty_status_by_ble_id(self, ble_identifier: str, new_status: str):
        """Updates the status of a faculty member by their BLE identifier."""
        query = sql.SQL("""
            UPDATE faculty
            SET current_status = %s, status_updated_at = %s, updated_at = %s
            WHERE ble_identifier = %s
            RETURNING faculty_id, name, current_status, status_updated_at;
        """)
        try:
            now = datetime.now()
            updated_faculty = self._execute_query(query, (new_status, now, now, ble_identifier), fetch_one=True, commit=True)
            if updated_faculty:
                logging.info(f"Status for faculty {updated_faculty.get('name')} (BLE: {ble_identifier}) updated to {new_status}")
            else:
                logging.warning(f"No faculty found with BLE ID {ble_identifier} to update status.")
            return updated_faculty
        except Exception as e:
            logging.error(f"Error updating faculty status for BLE ID {ble_identifier}: {e}")
            return None

    # --- Consultation Management ---
    def add_consultation_request(self, student_id: int, faculty_id: int, course_code: str = None, 
                               subject: str = None, request_details: str = None):
        """Adds a new consultation request."""
        query = sql.SQL("""
            INSERT INTO consultations (student_id, faculty_id, course_code, subject, request_details, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING consultation_id, student_id, faculty_id, course_code, subject, request_details, status, requested_at, updated_at;
        """)
        try:
            now = datetime.now()
            return self._execute_query(query, (student_id, faculty_id, course_code, subject, request_details, now), fetch_one=True, commit=True)
        except psycopg2.Error as e:
            logging.error(f"Error adding consultation request for student {student_id} to faculty {faculty_id}: {e}")
            return None

    def get_consultations_for_faculty(self, faculty_id: int, status_filter: str = None):
        """Retrieves consultation requests for a specific faculty member, optionally filtered by status."""
        base_query = """
            SELECT c.*, s.name as student_name 
            FROM consultations c
            JOIN students s ON c.student_id = s.student_id
            WHERE c.faculty_id = %s
        """
        params = [faculty_id]
        
        query_string = base_query
        if status_filter:
            query_string += " AND c.status = %s"
            params.append(status_filter)
        
        query_string += " ORDER BY c.requested_at DESC;"
        
        query = sql.SQL(query_string)
        return self._execute_query(query, tuple(params), fetch_all=True)

    def get_all_consultations_with_details(self):
        """Retrieves all consultation requests with student and faculty names."""
        query = sql.SQL("""
            SELECT 
                c.consultation_id, c.student_id, s.name as student_name, 
                c.faculty_id, f.name as faculty_name,
                c.course_code, c.subject, c.request_details, c.status, 
                c.requested_at, c.updated_at
            FROM consultations c
            JOIN students s ON c.student_id = s.student_id
            JOIN faculty f ON c.faculty_id = f.faculty_id
            ORDER BY c.requested_at DESC;
        """)
        try:
            return self._execute_query(query, fetch_all=True)
        except Exception as e:
            logging.error(f"Error retrieving all consultations with details: {e}")
            return []

    def update_consultation_status(self, consultation_id: int, new_status: str):
        """Updates the status of a consultation request."""
        query = sql.SQL("""
            UPDATE consultations
            SET status = %s, updated_at = %s
            WHERE consultation_id = %s
            RETURNING consultation_id, status, updated_at;
        """)
        try:
            now = datetime.now()
            return self._execute_query(query, (new_status, now, consultation_id), fetch_one=True, commit=True)
        except Exception as e:
            logging.error(f"Error updating consultation status for ID {consultation_id}: {e}")
            return None

# Example Usage (for testing this service directly)
if __name__ == '__main__':
    # IMPORTANT: Ensure your PostgreSQL server is running and configured
    # with the DB_NAME, DB_USER, and DB_PASSWORD specified above.
    # The user DB_USER must have CREATETABLE privileges on DB_NAME for _ensure_tables_exist.
    
    print("Attempting to initialize DatabaseService...")
    try:
        db_service = DatabaseService()
        print("DatabaseService initialized. Tables should be created if they didn't exist.")

        # Test adding a student
        # print("\n--- Testing Student Operations ---")
        # new_student = db_service.add_student(rfid_tag="RFID12345TEST", name="Test Student", department="Computer Science")
        # if new_student:
        #     print(f"Added student: {new_student}")
        #     retrieved_student = db_service.get_student_by_rfid("RFID12345TEST")
        #     print(f"Retrieved student by RFID: {retrieved_student}")
        #     retrieved_by_id = db_service.get_student_by_id(new_student['student_id'])
        #     print(f"Retrieved student by ID: {retrieved_by_id}")
        # else:
        #     print("Failed to add student or student already exists.")

        # Test adding faculty
        # print("\n--- Testing Faculty Operations ---")
        # new_faculty = db_service.add_faculty(name="Dr. Testprof", department="Physics", ble_identifier="BLE_TEST_PROF_01")
        # if new_faculty:
        #     print(f"Added faculty: {new_faculty}")
        #     retrieved_faculty = db_service.get_faculty_by_id(new_faculty['faculty_id'])
        #     print(f"Retrieved faculty by ID: {retrieved_faculty}")
            
        #     # Test updating status
        #     updated_status = db_service.update_faculty_status_by_ble_id(ble_identifier="BLE_TEST_PROF_01", new_status="Available")
        #     print(f"Updated faculty status by BLE ID: {updated_status}")

        #     all_faculty = db_service.get_all_faculty()
        #     print(f"All faculty: {all_faculty}")

        #     available_physics_faculty = db_service.get_all_faculty(department_filter="Physics", status_filter="Available")
        #     print(f"Available Physics Faculty: {available_physics_faculty}")

        # else:
        #     print("Failed to add faculty or faculty already exists.")

        # print("\n--- Testing Consultation Operations ---")
        # Assuming student_id=1 and faculty_id=1 exist from previous tests
        # student_for_consult = db_service.get_student_by_rfid("RFID12345TEST")
        # faculty_for_consult = db_service.get_faculty_by_id(1) # Assuming first faculty added has id 1

        # if student_for_consult and faculty_for_consult:
        #     s_id = student_for_consult['student_id']
        #     f_id = faculty_for_consult['faculty_id']
        #     new_req = db_service.add_consultation_request(s_id, f_id, "CS101", "Recursion Help", "Struggling with base cases.")
        #     if new_req:
        #         print(f"Added consultation request: {new_req}")
        #         consult_id = new_req['consultation_id']
                
        #         faculty_reqs = db_service.get_consultations_for_faculty(f_id)
        #         print(f"Consultations for faculty {f_id}: {faculty_reqs}")

        #         updated_consult_status = db_service.update_consultation_status(consult_id, "Viewed")
        #         print(f"Updated consultation status: {updated_consult_status}")
        #     else:
        #         print("Failed to add consultation request.")
        # else:
        #     print("Could not run consultation tests: student or faculty not found from previous tests.")

    except RuntimeError as e:
        print(f"Runtime error during DatabaseService initialization: {e}")
    except psycopg2.Error as e:
        print(f"A psycopg2 error occurred: {e}")
        print("Please ensure your PostgreSQL server is running, accessible, and that the specified database and user exist with correct permissions.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}") 