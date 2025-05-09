"""
Transition manager for smooth window transitions.
"""
import logging
from PyQt5.QtCore import QObject, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QWidget
from .ui_components import LoadingOverlay

# Set up logging
logger = logging.getLogger(__name__)

class TransitionManager(QObject):
    """
    Manages smooth transitions between windows.

    This class provides methods to handle window transitions with a loading overlay
    to prevent the OS background from being visible during transitions.
    """

    def __init__(self, parent=None):
        """
        Initialize the transition manager.

        Args:
            parent: Parent object
        """
        super().__init__(parent)

        # Create a full-screen overlay widget
        self.overlay = None
        self.overlay_parent = None
        self._create_overlay()

        # Track active window
        self.active_window = None

        # Transition delay (ms)
        self.transition_delay = 100

    def cleanup(self):
        """
        Clean up resources.
        """
        logger.info("Cleaning up transition manager")
        try:
            # Hide and delete overlay
            if hasattr(self, 'overlay_parent') and self.overlay_parent:
                self._hide_overlay(self.overlay_parent)
                self.overlay_parent.deleteLater()

            self.overlay = None
            self.overlay_parent = None
        except Exception as e:
            logger.error(f"Error cleaning up transition manager: {e}")

    def _create_overlay(self):
        """Create the transition overlay."""
        try:
            # Get the primary screen dimensions
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()

            # Create a top-level widget for the overlay
            # Store as instance variable to prevent garbage collection
            self.overlay_parent = QWidget()
            self.overlay_parent.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.overlay_parent.setAttribute(Qt.WA_TranslucentBackground)
            self.overlay_parent.setGeometry(screen_geometry)

            # Create the loading overlay
            self.overlay = LoadingOverlay(self.overlay_parent)
            self.overlay.resize(screen_geometry.width(), screen_geometry.height())

            # Hide initially
            self.overlay_parent.hide()

            logger.info(f"Created transition overlay with dimensions {screen_geometry.width()}x{screen_geometry.height()}")
        except Exception as e:
            logger.error(f"Failed to create transition overlay: {e}")
            self.overlay = None
            self.overlay_parent = None

    def transition_to(self, from_window, to_window, prepare_func=None, message="Loading..."):
        """
        Transition from one window to another with a loading overlay.

        Args:
            from_window: Current window to hide
            to_window: Target window to show
            prepare_func: Optional function to call to prepare the target window
            message: Message to display during transition
        """
        # Check if overlay is available and recreate if needed
        if not self.overlay or not hasattr(self, 'overlay_parent') or not self.overlay_parent:
            logger.warning("Transition overlay not available, recreating...")
            self._create_overlay()

            # If still not available, fall back to direct transition
            if not self.overlay or not hasattr(self, 'overlay_parent') or not self.overlay_parent:
                logger.error("Failed to recreate transition overlay")
                self._direct_transition(from_window, to_window, prepare_func)
                return

        try:
            logger.info(f"Starting transition to {to_window.__class__.__name__}")

            # Show overlay
            self.overlay_parent.show()
            self.overlay_parent.activateWindow()
            self.overlay_parent.raise_()
            self.overlay.show_loading(message)

            # Process events to ensure overlay is visible
            QApplication.processEvents()

            # Hide current window if provided
            if from_window:
                from_window.hide()

            # Prepare the target window if needed
            if prepare_func:
                prepare_func()

            # Use a timer to show the target window after a short delay
            # This ensures the overlay is fully visible before the transition
            QTimer.singleShot(self.transition_delay, lambda: self._complete_transition(to_window))

            # Update active window
            self.active_window = to_window

        except Exception as e:
            logger.error(f"Error during transition: {e}")
            self._direct_transition(from_window, to_window, prepare_func)

    def _complete_transition(self, to_window, overlay_parent=None):
        """
        Complete the transition by showing the target window and hiding the overlay.

        Args:
            to_window: Target window to show
            overlay_parent: Parent widget of the overlay (optional, uses self.overlay_parent if not provided)
        """
        # Use the instance variable if parameter is not provided
        if overlay_parent is None and hasattr(self, 'overlay_parent'):
            overlay_parent = self.overlay_parent

        try:
            # Show and activate the target window
            to_window.show()

            # For fullscreen windows, ensure they are in fullscreen mode
            if hasattr(to_window, 'fullscreen') and to_window.fullscreen:
                logger.info(f"Setting {to_window.__class__.__name__} to fullscreen mode")
                to_window.showFullScreen()
            else:
                logger.info(f"Showing {to_window.__class__.__name__} in normal mode")

            # Ensure the window is active and on top
            to_window.activateWindow()
            to_window.raise_()

            # Process events to ensure window is visible
            QApplication.processEvents()

            # Hide the overlay after a short delay if available
            if overlay_parent:
                # This ensures the target window is fully visible before hiding the overlay
                QTimer.singleShot(self.transition_delay, lambda: self._hide_overlay(overlay_parent))

            logger.info(f"Completed transition to {to_window.__class__.__name__}")

        except Exception as e:
            logger.error(f"Error completing transition: {e}")
            # Hide overlay in case of error
            if overlay_parent:
                try:
                    overlay_parent.hide()
                except Exception as hide_error:
                    logger.error(f"Error hiding overlay: {hide_error}")

            # Show window directly as fallback
            try:
                to_window.show()
                if hasattr(to_window, 'fullscreen') and to_window.fullscreen:
                    logger.info(f"Setting {to_window.__class__.__name__} to fullscreen mode (error fallback)")
                    to_window.showFullScreen()
                else:
                    logger.info(f"Showing {to_window.__class__.__name__} in normal mode (error fallback)")
            except Exception as show_error:
                logger.error(f"Error showing window: {show_error}")

    def _hide_overlay(self, overlay_parent):
        """
        Safely hide the overlay parent widget.

        Args:
            overlay_parent: Parent widget of the overlay
        """
        try:
            if overlay_parent and overlay_parent.isVisible():
                overlay_parent.hide()
        except Exception as e:
            logger.error(f"Error hiding overlay: {e}")

    def _direct_transition(self, from_window, to_window, prepare_func=None):
        """
        Perform a direct transition without the overlay (fallback method).

        Args:
            from_window: Current window to hide
            to_window: Target window to show
            prepare_func: Optional function to call to prepare the target window
        """
        logger.warning("Using direct transition (no overlay)")

        # Hide current window if provided
        if from_window:
            from_window.hide()

        # Prepare the target window if needed
        if prepare_func:
            prepare_func()

        # Show and activate the target window
        to_window.show()
        if hasattr(to_window, 'fullscreen') and to_window.fullscreen:
            logger.info(f"Setting {to_window.__class__.__name__} to fullscreen mode (direct transition)")
            to_window.showFullScreen()
        else:
            logger.info(f"Showing {to_window.__class__.__name__} in normal mode (direct transition)")

        to_window.activateWindow()
        to_window.raise_()

        # Update active window
        self.active_window = to_window
