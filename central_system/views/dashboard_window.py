from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGridLayout, QScrollArea, QFrame,
                               QLineEdit, QTextEdit, QComboBox, QMessageBox,
                               QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QColor

import os
import logging
from .base_window import BaseWindow
from central_system.utils.ui_components import NotificationBanner

# Set up logging
logger = logging.getLogger(__name__)

class FacultyCard(QFrame):
    """
    Widget to display faculty information and status.
    """
    consultation_requested = pyqtSignal(object)

    def __init__(self, faculty, parent=None):
        super().__init__(parent)
        self.faculty = faculty
        self.init_ui()

    def init_ui(self):
        """
        Initialize the faculty card UI.
        """
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(300, 180)

        # Set styling based on faculty status
        self.update_style()

        # Main layout
        main_layout = QVBoxLayout(self)

        # Faculty name
        name_label = QLabel(self.faculty.name)
        name_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        main_layout.addWidget(name_label)

        # Department
        dept_label = QLabel(self.faculty.department)
        dept_label.setStyleSheet("font-size: 12pt; color: #666;")
        main_layout.addWidget(dept_label)

        # Status indicator
        status_layout = QHBoxLayout()
        status_icon = QLabel("●")
        if self.faculty.status:
            status_icon.setStyleSheet("font-size: 16pt; color: #4caf50;")
            status_text = QLabel("Available")
            status_text.setStyleSheet("font-size: 14pt; color: #4caf50;")
        else:
            status_icon.setStyleSheet("font-size: 16pt; color: #f44336;")
            status_text = QLabel("Unavailable")
            status_text.setStyleSheet("font-size: 14pt; color: #f44336;")

        status_layout.addWidget(status_icon)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # Request consultation button
        request_button = QPushButton("Request Consultation")
        request_button.setEnabled(self.faculty.status)
        request_button.clicked.connect(self.request_consultation)
        main_layout.addWidget(request_button)

    def update_style(self):
        """
        Update the card styling based on faculty status.
        """
        if self.faculty.status:
            self.setStyleSheet('''
                QFrame {
                    background-color: #e8f5e9;
                    border: 2px solid #4caf50;
                    border-radius: 10px;
                }
            ''')
        else:
            self.setStyleSheet('''
                QFrame {
                    background-color: #ffebee;
                    border: 2px solid #f44336;
                    border-radius: 10px;
                }
            ''')

    def update_faculty(self, faculty):
        """
        Update the faculty information.
        """
        # Store the old parent
        old_parent = self.parent()

        # Update faculty data
        self.faculty = faculty

        # Clear existing layout
        if self.layout():
            # Remove all widgets from the layout
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Delete the layout itself
            QWidget().setLayout(self.layout())

        # Update style based on new faculty status
        self.update_style()

        # Reinitialize UI
        self.init_ui()

        # Ensure we're still in the parent's layout if we had one
        if old_parent:
            self.setParent(old_parent)

    def request_consultation(self):
        """
        Emit signal to request a consultation with this faculty.
        """
        self.consultation_requested.emit(self.faculty)

class ConsultationRequestForm(QFrame):
    """
    Form to request a consultation with a faculty member.
    """
    request_submitted = pyqtSignal(object, str, str)

    def __init__(self, faculty=None, parent=None):
        super().__init__(parent)
        self.faculty = faculty
        self.init_ui()

    def init_ui(self):
        """
        Initialize the consultation request form UI.
        """
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('''
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 10px;
            }
        ''')

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Form title
        title_label = QLabel("Request Consultation")
        title_label.setStyleSheet("font-size: 20pt; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Faculty information
        if self.faculty:
            faculty_info = QLabel(f"Faculty: {self.faculty.name} ({self.faculty.department})")
            faculty_info.setStyleSheet("font-size: 14pt;")
            main_layout.addWidget(faculty_info)
        else:
            # If no faculty is selected, show a dropdown
            faculty_label = QLabel("Select Faculty:")
            faculty_label.setStyleSheet("font-size: 14pt;")
            main_layout.addWidget(faculty_label)

            self.faculty_combo = QComboBox()
            self.faculty_combo.setStyleSheet("font-size: 14pt; padding: 8px;")
            # Faculty options would be populated separately
            main_layout.addWidget(self.faculty_combo)

        # Course code input
        course_label = QLabel("Course Code (optional):")
        course_label.setStyleSheet("font-size: 14pt;")
        main_layout.addWidget(course_label)

        self.course_input = QLineEdit()
        self.course_input.setStyleSheet("font-size: 14pt; padding: 8px;")
        main_layout.addWidget(self.course_input)

        # Message input
        message_label = QLabel("Consultation Details:")
        message_label.setStyleSheet("font-size: 14pt;")
        main_layout.addWidget(message_label)

        self.message_input = QTextEdit()
        self.message_input.setStyleSheet("font-size: 14pt; padding: 8px;")
        self.message_input.setMinimumHeight(150)
        main_layout.addWidget(self.message_input)

        # Submit button
        button_layout = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet('''
            QPushButton {
                background-color: #f44336;
                min-width: 120px;
            }
        ''')
        cancel_button.clicked.connect(self.cancel_request)

        submit_button = QPushButton("Submit Request")
        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #4caf50;
                min-width: 120px;
            }
        ''')
        submit_button.clicked.connect(self.submit_request)

        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(submit_button)

        main_layout.addLayout(button_layout)

    def set_faculty(self, faculty):
        """
        Set the faculty for the consultation request.
        """
        self.faculty = faculty
        self.init_ui()

    def set_faculty_options(self, faculties):
        """
        Set the faculty options for the dropdown.
        """
        if hasattr(self, 'faculty_combo'):
            self.faculty_combo.clear()
            for faculty in faculties:
                self.faculty_combo.addItem(f"{faculty.name} ({faculty.department})", faculty)

    def get_selected_faculty(self):
        """
        Get the selected faculty from the dropdown.
        """
        if hasattr(self, 'faculty_combo') and self.faculty_combo.count() > 0:
            return self.faculty_combo.currentData()
        return self.faculty

    def submit_request(self):
        """
        Handle the submission of the consultation request.
        """
        faculty = self.get_selected_faculty()
        if not faculty:
            QMessageBox.warning(self, "Consultation Request", "Please select a faculty member.")
            return

        message = self.message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Consultation Request", "Please enter consultation details.")
            return

        course_code = self.course_input.text().strip()

        # Emit signal with the request details
        self.request_submitted.emit(faculty, message, course_code)

    def cancel_request(self):
        """
        Cancel the consultation request.
        """
        self.message_input.clear()
        self.course_input.clear()
        self.setVisible(False)

class DashboardWindow(BaseWindow):
    """
    Main dashboard window with faculty availability display and consultation request functionality.
    """
    # Signal to handle consultation request
    consultation_requested = pyqtSignal(object, str, str)

    def __init__(self, student=None, parent=None):
        self.student = student
        super().__init__(parent)
        self.init_ui()

        # Create notification banner
        self.notification_banner = NotificationBanner(self)

        # Connect search and filter controls to filter method
        self.search_input.textChanged.connect(self.filter_faculty)
        self.filter_combo.currentIndexChanged.connect(self.filter_faculty)

        # Set up auto-refresh timer for faculty status
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_faculty_status)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def init_ui(self):
        """
        Initialize the dashboard UI.
        """
        # Main layout with splitter
        main_layout = QVBoxLayout()

        # Header with welcome message and student info
        header_layout = QHBoxLayout()

        if self.student:
            welcome_label = QLabel(f"Welcome, {self.student.name}")
        else:
            welcome_label = QLabel("Welcome to ConsultEase")
        welcome_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        header_layout.addWidget(welcome_label)

        # Logout button
        logout_button = QPushButton("Logout")
        logout_button.setFixedWidth(100)
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)

        main_layout.addLayout(header_layout)

        # Main content with faculty grid and consultation form
        content_splitter = QSplitter(Qt.Horizontal)

        # Faculty availability grid
        faculty_widget = QWidget()
        faculty_layout = QVBoxLayout(faculty_widget)

        # Search and filter controls
        filter_layout = QHBoxLayout()

        search_label = QLabel("Search:")
        search_label.setFixedWidth(80)
        filter_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or department")
        self.search_input.textChanged.connect(self.filter_faculty)
        filter_layout.addWidget(self.search_input)

        filter_label = QLabel("Filter:")
        filter_label.setFixedWidth(80)
        filter_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All", None)
        self.filter_combo.addItem("Available Only", True)
        self.filter_combo.addItem("Unavailable Only", False)
        self.filter_combo.currentIndexChanged.connect(self.filter_faculty)
        filter_layout.addWidget(self.filter_combo)

        faculty_layout.addLayout(filter_layout)

        # Faculty grid in a scroll area
        self.faculty_grid = QGridLayout()
        self.faculty_grid.setSpacing(20)

        faculty_scroll = QScrollArea()
        faculty_scroll.setWidgetResizable(True)
        faculty_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        faculty_scroll_content = QWidget()
        faculty_scroll_content.setLayout(self.faculty_grid)
        faculty_scroll.setWidget(faculty_scroll_content)

        faculty_layout.addWidget(faculty_scroll)

        # Consultation request form
        self.consultation_form = ConsultationRequestForm()
        self.consultation_form.setVisible(False)
        self.consultation_form.request_submitted.connect(self.handle_consultation_request)

        # Add widgets to splitter
        content_splitter.addWidget(faculty_widget)
        content_splitter.addWidget(self.consultation_form)
        content_splitter.setSizes([700, 300])

        main_layout.addWidget(content_splitter)

        # Set the main layout to a widget and make it the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def populate_faculty_grid(self, faculties):
        """
        Populate the faculty grid with faculty cards.

        Args:
            faculties (list): List of faculty objects
        """
        # Clear existing grid
        while self.faculty_grid.count():
            item = self.faculty_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add faculty cards to grid
        row, col = 0, 0
        max_cols = 3  # Number of columns in the grid

        for faculty in faculties:
            card = FacultyCard(faculty)
            card.consultation_requested.connect(self.show_consultation_form)
            self.faculty_grid.addWidget(card, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def filter_faculty(self):
        """
        Filter faculty grid based on search text and filter selection.
        """
        try:
            # Get search text and filter value
            search_text = self.search_input.text().strip()
            filter_index = self.filter_combo.currentIndex()
            filter_value = self.filter_combo.itemData(filter_index)

            logger.info(f"Filtering faculty - Search: '{search_text}', Filter: {filter_value}")

            # Get faculty controller from parent application
            # We need to access the faculty controller to get the filtered list
            from central_system.controllers import get_faculty_controller
            faculty_controller = get_faculty_controller()

            if faculty_controller:
                # Get filtered faculty list
                faculties = faculty_controller.get_all_faculty(
                    filter_available=filter_value,
                    search_term=search_text if search_text else None
                )

                # Update the grid with filtered results
                self.populate_faculty_grid(faculties)

                # Show notification if no results
                if not faculties:
                    self.show_notification("No faculty members match your search criteria.", "info")
            else:
                logger.error("Could not access faculty controller for filtering")
                self.show_notification("Could not filter faculty list. Please try again.", "error")

        except Exception as e:
            logger.error(f"Error filtering faculty: {str(e)}")
            self.show_notification("An error occurred while filtering. Please try again.", "error")

    def refresh_faculty_status(self):
        """
        Refresh the faculty status from the server.
        """
        try:
            logger.info("Refreshing faculty status")

            # Get faculty controller from parent application
            from central_system.controllers import get_faculty_controller
            faculty_controller = get_faculty_controller()

            if faculty_controller:
                # Get current filter settings
                search_text = self.search_input.text().strip()
                filter_index = self.filter_combo.currentIndex()
                filter_value = self.filter_combo.itemData(filter_index)

                # Get updated faculty list with current filters
                faculties = faculty_controller.get_all_faculty(
                    filter_available=filter_value,
                    search_term=search_text if search_text else None
                )

                # Update the grid with refreshed data
                self.populate_faculty_grid(faculties)
                logger.info(f"Faculty status refreshed - {len(faculties)} faculty members displayed")
            else:
                logger.error("Could not access faculty controller for refresh")

        except Exception as e:
            logger.error(f"Error refreshing faculty status: {str(e)}")

    def show_consultation_form(self, faculty):
        """
        Show the consultation request form for a specific faculty.

        Args:
            faculty (object): Faculty object to request consultation with
        """
        self.consultation_form.set_faculty(faculty)
        self.consultation_form.setVisible(True)

    def handle_consultation_request(self, faculty, message, course_code):
        """
        Handle consultation request submission.

        Args:
            faculty (object): Faculty object
            message (str): Consultation request message
            course_code (str): Optional course code
        """
        # Emit signal to controller
        self.consultation_requested.emit(faculty, message, course_code)

        # Hide the form
        self.consultation_form.setVisible(False)
        self.consultation_form.message_input.clear()
        self.consultation_form.course_input.clear()

        # Show confirmation
        QMessageBox.information(
            self,
            "Consultation Request",
            f"Your consultation request with {faculty.name} has been submitted."
        )

    def logout(self):
        """
        Handle logout button click.
        """
        logger.info("Student logging out")
        # Don't hide the window here - let the transition manager handle it
        # Just emit the signal to change windows
        self.change_window.emit("login", None)

    def show_notification(self, message, message_type="info"):
        """
        Show a notification message to the user.

        Args:
            message (str): Message to display
            message_type (str): Type of message (info, success, warning, error)
        """
        logger.info(f"Showing notification: {message} ({message_type})")
        try:
            # Map message types to NotificationBanner constants
            if message_type == "success":
                banner_type = NotificationBanner.SUCCESS
            elif message_type == "warning":
                banner_type = NotificationBanner.WARNING
            elif message_type == "error":
                banner_type = NotificationBanner.ERROR
            else:
                banner_type = NotificationBanner.INFO

            # Show the notification
            self.notification_banner.show_message(message, banner_type)
        except Exception as e:
            logger.error(f"Error showing notification: {str(e)}")
            # Fallback to message box if notification banner fails
            QMessageBox.information(self, "Notification", message)