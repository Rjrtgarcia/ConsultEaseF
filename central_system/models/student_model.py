from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Student:
    student_id: int = field(default=None) # Handled by DB (SERIAL)
    rfid_tag: str
    name: str
    department: str = field(default=None) # Optional for MVP
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Placeholder for a method to convert to dict for DB or API
    def to_dict(self):
        return {
            "student_id": self.student_id,
            "rfid_tag": self.rfid_tag,
            "name": self.name,
            "department": self.department,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 