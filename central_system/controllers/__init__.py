from .rfid_controller import RFIDController
from .faculty_controller import FacultyController
from .consultation_controller import ConsultationController
from .admin_controller import AdminController

# Global controller instances
_faculty_controller = None

def get_faculty_controller():
    """
    Get the global faculty controller instance.

    Returns:
        FacultyController: The global faculty controller instance
    """
    global _faculty_controller

    # If we don't have a controller instance yet, try to get it from the main app
    if _faculty_controller is None:
        try:
            # Import here to avoid circular imports
            import sys

            # Try to get the main app instance
            from central_system.main import ConsultEaseApp

            # Find the app instance
            for obj in vars(sys.modules['__main__']).values():
                if isinstance(obj, ConsultEaseApp):
                    _faculty_controller = obj.faculty_controller
                    break
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error getting faculty controller: {str(e)}")

    return _faculty_controller

__all__ = [
    'RFIDController',
    'FacultyController',
    'ConsultationController',
    'AdminController',
    'get_faculty_controller'
]