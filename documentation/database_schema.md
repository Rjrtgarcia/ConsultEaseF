# ConsultEase Database Schema (MVP Draft)

This document outlines the initial database schema for the ConsultEase system, focusing on the Minimum Viable Product (MVP) requirements.

## Tables

### 1. `students`
Stores information about students.

| Column        | Data Type     | Constraints              | Description                           |
|---------------|---------------|--------------------------|---------------------------------------|
| `student_id`  | SERIAL        | PRIMARY KEY              | Unique identifier for the student     |
| `rfid_tag`    | VARCHAR(50)   | UNIQUE, NOT NULL         | RFID tag ID associated with the student |
| `name`        | VARCHAR(255)  | NOT NULL                 | Full name of the student              |
| `department`  | VARCHAR(100)  |                          | Student's department (optional for MVP) |
| `created_at`  | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()   | Timestamp of record creation          |
| `updated_at`  | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()   | Timestamp of last record update       |

**Indexes**:
*   `idx_students_rfid_tag` ON `rfid_tag`

### 2. `faculty`
Stores information about faculty members.

| Column          | Data Type     | Constraints              | Description                               |
|-----------------|---------------|--------------------------|-------------------------------------------|
| `faculty_id`    | SERIAL        | PRIMARY KEY              | Unique identifier for the faculty member  |
| `name`          | VARCHAR(255)  | NOT NULL                 | Full name of the faculty member           |
| `department`    | VARCHAR(100)  | NOT NULL                 | Faculty member's department               |
| `ble_identifier`| VARCHAR(100)  | UNIQUE, NOT NULL         | Unique BLE beacon identifier (e.g., MAC address) |
| `office_location`| VARCHAR(100) |                          | Office location (optional for MVP)        |
| `contact_details`| TEXT         |                          | Contact details (optional for MVP)        |
| `current_status`| VARCHAR(20)   | DEFAULT 'Unavailable'  | Current availability status ("Available", "Unavailable") - *May be managed by MQTT updates rather than direct DB writes from ESP32 for MVP* |
| `status_updated_at` | TIMESTAMPTZ | DEFAULT NOW()          | Timestamp of last status update            |
| `created_at`    | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()   | Timestamp of record creation              |
| `updated_at`    | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()   | Timestamp of last record update           |

**Indexes**:
*   `idx_faculty_ble_identifier` ON `ble_identifier`
*   `idx_faculty_department` ON `department`

### 3. `consultations`
Stores information about consultation requests.

| Column             | Data Type     | Constraints                          | Description                                       |
|--------------------|---------------|--------------------------------------|---------------------------------------------------|
| `consultation_id`  | SERIAL        | PRIMARY KEY                          | Unique identifier for the consultation request    |
| `student_id`       | INTEGER       | NOT NULL, FOREIGN KEY REFERENCES `students(student_id)` | ID of the student making the request            |
| `faculty_id`       | INTEGER       | NOT NULL, FOREIGN KEY REFERENCES `faculty(faculty_id)`   | ID of the faculty member for whom request is made |
| `course_code`      | VARCHAR(50)   |                                      | Course code related to the consultation           |
| `subject`          | VARCHAR(255)  |                                      | Subject/brief reason for consultation             |
| `request_details`  | TEXT          |                                      | Detailed information about the consultation       |
| `status`           | VARCHAR(20)   | NOT NULL DEFAULT 'Pending'         | Status of the request (e.g., "Pending", "Accepted", "Rejected", "Completed") - *MVP might only use "Pending" and "Viewed"* |
| `requested_at`     | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()               | Timestamp when the request was made               |
| `updated_at`       | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()               | Timestamp of last request update                  |

**Indexes**:
*   `idx_consultations_student_id` ON `student_id`
*   `idx_consultations_faculty_id` ON `faculty_id`
*   `idx_consultations_status` ON `status`

## Relationships
- A `student` can have many `consultations`.
- A `faculty` member can have many `consultations`.

## Notes for MVP
- The `faculty.current_status` might be primarily driven by MQTT and reflected in the application layer. Storing it in the DB provides a last known state but real-time view is via MQTT.
- Timestamps for `created_at` and `updated_at` can be managed by PostgreSQL triggers or application logic.
- Further normalization or additional tables (e.g., `departments`) can be considered post-MVP. 