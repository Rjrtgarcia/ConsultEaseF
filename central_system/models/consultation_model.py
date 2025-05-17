from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Consultation:
    consultation_id: int = field(default=None)  # Handled by DB (SERIAL)
    student_id: int
    faculty_id: int
    course_code: str = field(default=None)
    subject: str = field(default=None)
    request_details: str = field(default=None)
    status: str = field(default='Pending')  # e.g., Pending, Accepted, Viewed
    requested_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Placeholder for a method to convert to dict for DB or API
    def to_dict(self):
        return {
            "consultation_id": self.consultation_id,
            "student_id": self.student_id,
            "faculty_id": self.faculty_id,
            "course_code": self.course_code,
            "subject": self.subject,
            "request_details": self.request_details,
            "status": self.status,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 