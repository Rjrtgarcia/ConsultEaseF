import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add parent directory to path to help with imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('consultease.log')
    ]
)
logger = logging.getLogger(__name__)

# Import models and controllers
from central_system.models import init_db
from central_system.controllers import (
    RFIDController,
    FacultyController,
    ConsultationController,
    AdminController
)

# Import views
from central_system.views import (
    LoginWindow,
    DashboardWindow,
    AdminLoginWindow,
    AdminDashboardWindow
)

# Import the keyboard setup script generator
from central_system.views.login_window import create_keyboard_setup_script

# Import utilities
from central_system.utils import (
    install_keyboard_handler,
    apply_stylesheet,
    TransitionManager
)
# Import icons module separately to avoid early QPixmap creation
from central_system.utils import icons

class ConsultEaseApp:
    """
    Main application class for ConsultEase.
    """

    def __init__(self, fullscreen=False):
        """
        Initialize the ConsultEase application.
        """
        logger.info("Initializing ConsultEase application")

        # Create QApplication instance
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ConsultEase")

        # Set up icons and modern UI (after QApplication is created)
        icons.initialize()
        logger.info("Initialized icons")

        # Apply modern stylesheet (dark theme by default)
        theme = self._get_theme_preference()
        apply_stylesheet(self.app, theme)
        logger.info(f"Applied {theme} theme stylesheet")

        # Create keyboard setup script for Raspberry Pi
        try:
            script_path = create_keyboard_setup_script()
            logger.info(f"Created keyboard setup script at {script_path}")
        except Exception as e:
            logger.error(f"Failed to create keyboard setup script: {e}")

        # Install keyboard handler for touch input
        try:
            self.keyboard_handler = install_keyboard_handler(self.app)
            logger.info("Installed virtual keyboard handler")
        except Exception as e:
            logger.error(f"Failed to install virtual keyboard handler: {e}")
            self.keyboard_handler = None

        # Initialize database
        init_db()

        # Initialize controllers
        self.rfid_controller = RFIDController()
        self.faculty_controller = FacultyController()
        self.consultation_controller = ConsultationController()
        self.admin_controller = AdminController()

        # Ensure default admin exists
        self.admin_controller.ensure_default_admin()

        # Initialize windows
        self.login_window = None
        self.dashboard_window = None
        self.admin_login_window = None
        self.admin_dashboard_window = None

        # Current student
        self.current_student = None

        # Create transition manager for smooth window transitions
        self.transition_manager = TransitionManager()

        # Store fullscreen preference for use in window creation
        self.fullscreen = fullscreen

        # Start controllers
        self.rfid_controller.start()
        self.rfid_controller.register_callback(self.handle_rfid_scan)

        self.faculty_controller.start()
        self.consultation_controller.start()

        # Connect cleanup method
        self.app.aboutToQuit.connect(self.cleanup)

        # Show login window
        self.show_login_window()

    def _get_theme_preference(self):
        """
        Get the user's theme preference.

        Returns:
            str: Theme name ('light' or 'dark')
        """
        # Default to dark theme
        theme = "dark"

        # Check for environment variable
        if "CONSULTEASE_THEME" in os.environ:
            env_theme = os.environ["CONSULTEASE_THEME"].lower()
            if env_theme in ["light", "dark"]:
                theme = env_theme

        # TODO: Add settings file check for theme preference

        return theme

    def run(self):
        """
        Run the application.
        """
        logger.info("Starting ConsultEase application")
        return self.app.exec_()

    def cleanup(self):
        """
        Clean up resources before exiting.
        """
        logger.info("Cleaning up ConsultEase application")

        # Stop controllers
        self.rfid_controller.stop()
        self.faculty_controller.stop()
        self.consultation_controller.stop()

        # Clean up transition manager
        if hasattr(self, 'transition_manager'):
            try:
                self.transition_manager.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up transition manager: {e}")

    def show_login_window(self):
        """
        Show the login window.
        """
        # Initialize login window if needed
        if self.login_window is None:
            self.login_window = LoginWindow()
            self.login_window.student_authenticated.connect(self.handle_student_authenticated)
            self.login_window.change_window.connect(self.handle_window_change)

        # Always set fullscreen flag (in case it changed)
        self.login_window.fullscreen = self.fullscreen
        logger.info(f"Setting login window fullscreen mode: {self.fullscreen}")

        # Determine current active window
        current_window = None
        if self.dashboard_window and self.dashboard_window.isVisible():
            current_window = self.dashboard_window
        elif self.admin_login_window and self.admin_login_window.isVisible():
            current_window = self.admin_login_window
        elif self.admin_dashboard_window and self.admin_dashboard_window.isVisible():
            current_window = self.admin_dashboard_window

        # Use transition manager to handle the window change
        self.transition_manager.transition_to(
            from_window=current_window,
            to_window=self.login_window,
            message="Loading login screen..."
        )

    def show_dashboard_window(self, student=None):
        """
        Show the dashboard window.
        """
        self.current_student = student

        # Initialize dashboard window if needed
        if self.dashboard_window is None:
            self.dashboard_window = DashboardWindow(student)
            self.dashboard_window.change_window.connect(self.handle_window_change)
            self.dashboard_window.consultation_requested.connect(self.handle_consultation_request)
        else:
            # Update student info if needed
            self.dashboard_window.student = student

        # Always set fullscreen flag (in case it changed)
        self.dashboard_window.fullscreen = self.fullscreen
        logger.info(f"Setting dashboard window fullscreen mode: {self.fullscreen}")

        # Determine current active window
        current_window = None
        if self.login_window and self.login_window.isVisible():
            current_window = self.login_window
        elif self.admin_login_window and self.admin_login_window.isVisible():
            current_window = self.admin_login_window
        elif self.admin_dashboard_window and self.admin_dashboard_window.isVisible():
            current_window = self.admin_dashboard_window

        # Define preparation function to populate faculty grid
        def prepare_dashboard():
            faculties = self.faculty_controller.get_all_faculty()
            self.dashboard_window.populate_faculty_grid(faculties)

        # Use transition manager to handle the window change
        self.transition_manager.transition_to(
            from_window=current_window,
            to_window=self.dashboard_window,
            prepare_func=prepare_dashboard,
            message="Loading dashboard..."
        )

    def show_admin_login_window(self):
        """
        Show the admin login window.
        """
        # Initialize admin login window if needed
        if self.admin_login_window is None:
            self.admin_login_window = AdminLoginWindow()
            self.admin_login_window.admin_authenticated.connect(self.handle_admin_authenticated)
            self.admin_login_window.change_window.connect(self.handle_window_change)

        # Always set fullscreen flag (in case it changed)
        self.admin_login_window.fullscreen = self.fullscreen
        logger.info(f"Setting admin login window fullscreen mode: {self.fullscreen}")

        # Determine current active window
        current_window = None
        if self.login_window and self.login_window.isVisible():
            current_window = self.login_window
        elif self.dashboard_window and self.dashboard_window.isVisible():
            current_window = self.dashboard_window
        elif self.admin_dashboard_window and self.admin_dashboard_window.isVisible():
            current_window = self.admin_dashboard_window

        # Use transition manager to handle the window change
        self.transition_manager.transition_to(
            from_window=current_window,
            to_window=self.admin_login_window,
            message="Loading admin login..."
        )

    def show_admin_dashboard_window(self, admin=None):
        """
        Show the admin dashboard window.
        """
        # Initialize admin dashboard window if needed
        if self.admin_dashboard_window is None:
            self.admin_dashboard_window = AdminDashboardWindow(admin)
            self.admin_dashboard_window.change_window.connect(self.handle_window_change)
            self.admin_dashboard_window.faculty_updated.connect(self.handle_faculty_updated)
            self.admin_dashboard_window.student_updated.connect(self.handle_student_updated)

        # Always set fullscreen flag (in case it changed)
        self.admin_dashboard_window.fullscreen = self.fullscreen
        logger.info(f"Setting admin dashboard window fullscreen mode: {self.fullscreen}")

        # Determine current active window
        current_window = None
        if self.login_window and self.login_window.isVisible():
            current_window = self.login_window
        elif self.dashboard_window and self.dashboard_window.isVisible():
            current_window = self.dashboard_window
        elif self.admin_login_window and self.admin_login_window.isVisible():
            current_window = self.admin_login_window

        # Use transition manager to handle the window change
        self.transition_manager.transition_to(
            from_window=current_window,
            to_window=self.admin_dashboard_window,
            message="Loading admin dashboard..."
        )

    def handle_rfid_scan(self, student, rfid_uid):
        """
        Handle RFID scan event.

        Args:
            student (Student): Verified student or None if not verified
            rfid_uid (str): RFID UID that was scanned
        """
        # If login window is active and visible
        if self.login_window and self.login_window.isVisible():
            self.login_window.handle_rfid_read(rfid_uid, student)

    def handle_student_authenticated(self, student):
        """
        Handle student authentication event.

        Args:
            student (Student): Authenticated student
        """
        logger.info(f"Student authenticated: {student.name}")
        self.show_dashboard_window(student)

    def handle_admin_authenticated(self, credentials):
        """
        Handle admin authentication event.

        Args:
            credentials (tuple): Admin credentials (username, password)
        """
        # Unpack credentials from tuple
        username, password = credentials

        # Authenticate admin
        admin = self.admin_controller.authenticate(username, password)

        if admin:
            logger.info(f"Admin authenticated: {username}")
            # Create admin info to pass to dashboard
            admin_info = {
                'id': admin.id,
                'username': admin.username
            }
            self.show_admin_dashboard_window(admin_info)
        else:
            logger.warning(f"Admin authentication failed: {username}")
            if self.admin_login_window:
                self.admin_login_window.show_login_error("Invalid username or password")

    def handle_consultation_request(self, faculty, message, course_code):
        """
        Handle consultation request event.

        Args:
            faculty (dict): Faculty information
            message (str): Consultation message
            course_code (str): Course code
        """
        if not self.current_student:
            logger.error("Cannot request consultation: no student authenticated")
            return

        logger.info(f"Consultation requested with: {faculty['name']}")

        # Create consultation request
        consultation = {
            'student_id': self.current_student.id,
            'faculty_id': faculty['id'],
            'message': message,
            'course_code': course_code,
            'status': 'pending'
        }

        # Add to database
        success = self.consultation_controller.add_consultation(consultation)

        # Show success/error message
        if success:
            self.dashboard_window.show_notification(
                f"Consultation request sent to {faculty['name']}",
                "success"
            )
        else:
            self.dashboard_window.show_notification(
                "Failed to send consultation request. Please try again.",
                "error"
            )

    def handle_faculty_updated(self):
        """
        Handle faculty data updated event.
        """
        # Refresh faculty grid if dashboard is active
        if self.dashboard_window and self.dashboard_window.isVisible():
            faculties = self.faculty_controller.get_all_faculty()
            self.dashboard_window.populate_faculty_grid(faculties)

    def handle_student_updated(self):
        """
        Handle student data updated event.
        """
        # TODO: Update student data in dashboard if needed
        pass

    def handle_window_change(self, window_name, data=None):
        """
        Handle window change event.

        Args:
            window_name (str): Name of window to show
            data (any): Optional data to pass to the window
        """
        if window_name == "login":
            self.show_login_window()
        elif window_name == "dashboard":
            self.show_dashboard_window(data)
        elif window_name == "admin_login":
            self.show_admin_login_window()
        elif window_name == "admin_dashboard":
            self.show_admin_dashboard_window(data)
        else:
            logger.warning(f"Unknown window: {window_name}")

if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("consultease.log")
        ]
    )

    # Enable debug logging for RFID service
    rfid_logger = logging.getLogger('central_system.services.rfid_service')
    rfid_logger.setLevel(logging.DEBUG)

    # Set environment variables if needed
    import os

    # Configure RFID - enable simulation mode since we're on Raspberry Pi
    os.environ['RFID_SIMULATION_MODE'] = 'true'  # Enable if no RFID reader available

    # Check if we're running in fullscreen mode
    fullscreen = os.environ.get('CONSULTEASE_FULLSCREEN', 'false').lower() == 'true'

    # Start the application
    app = ConsultEaseApp(fullscreen=fullscreen)
    sys.exit(app.run())