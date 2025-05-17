from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Faculty:
    faculty_id: int = field(default=None) # Handled by DB (SERIAL)
    name: str
    department: str
    ble_identifier: str # e.g., MAC address
    office_location: str = field(default=None) # Optional for MVP
    contact_details: str = field(default=None) # Optional for MVP
    current_status: str = field(default='Unavailable') # "Available", "Unavailable"
    status_updated_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Placeholder for a method to convert to dict for DB or API
    def to_dict(self):
        return {
            "faculty_id": self.faculty_id,
            "name": self.name,
            "department": self.department,
            "ble_identifier": self.ble_identifier,
            "office_location": self.office_location,
            "contact_details": self.contact_details,
            "current_status": self.current_status,
            "status_updated_at": self.status_updated_at.isoformat() if self.status_updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 