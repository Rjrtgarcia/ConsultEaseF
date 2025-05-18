import time
import threading
import logging
import random # For simulation

try:
    import serial
    import serial.tools.list_ports
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False
    logging.warning("pyserial library not found. Real RFID reader functionality will be unavailable. Please install it: pip install pyserial")

try:
    import evdev
    from evdev import InputDevice, categorize, ecodes, KeyEvent
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    logging.warning("evdev library not found. evdev RFID reader functionality will be unavailable.")

# Mock evdev objects if not available, to allow basic class definition
# This helps in environments where evdev cannot be installed (e.g., Windows for development)
class InputDevice:
    def __init__(self, path):
        logging.warning(f"evdev not available, RFID hardware functionality will be disabled. Mocking InputDevice for {path}.")
        self.path = path
    def read_loop(self):
        logging.warning("evdev.read_loop() called on mock InputDevice. RFID hardware disabled.")
        # Simulate a long sleep to prevent tight loop in mock usage if not handled carefully
        while True:
            time.sleep(1)
            yield None # Yield None to avoid breaking the loop structure
    def close(self):
        pass
    def grab(self):
        pass
    def ungrab(self):
        pass
class ecodes:
    KEY_ENTER = 0 # Placeholder
    EV_KEY = 0    # Placeholder
class KeyEvent:
    key_down = 1  # Placeholder value for key down event type
def categorize(event):
    return event # Placeholder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration for Actual Reader ---
HARDWARE_VID = 0xFFFF # Provided by user
HARDWARE_PID = 0x0035 # Provided by user
BAUD_RATE = 9600      # Common default, adjust if your reader uses a different rate

# --- Configuration for Actual Serial Reader ---
SERIAL_HARDWARE_VID = 0xFFFF # Provided by user
SERIAL_HARDWARE_PID = 0x0035 # Provided by user
SERIAL_BAUD_RATE = 9600      # Common default, adjust if your reader uses a different rate

# --- Key mapping for evdev (simplified, may need expansion) ---
# This maps evdev ecodes.KEY_* to characters.
# This is a basic example; a more comprehensive map might be needed based on your reader's output.
EVDEV_KEY_MAP = {
    ecodes.KEY_0: '0', ecodes.KEY_1: '1', ecodes.KEY_2: '2', ecodes.KEY_3: '3', ecodes.KEY_4: '4',
    ecodes.KEY_5: '5', ecodes.KEY_6: '6', ecodes.KEY_7: '7', ecodes.KEY_8: '8', ecodes.KEY_9: '9',
    ecodes.KEY_A: 'A', ecodes.KEY_B: 'B', ecodes.KEY_C: 'C', ecodes.KEY_D: 'D', ecodes.KEY_E: 'E',
    ecodes.KEY_F: 'F', ecodes.KEY_G: 'G', ecodes.KEY_H: 'H', ecodes.KEY_I: 'I', ecodes.KEY_J: 'J',
    ecodes.KEY_K: 'K', ecodes.KEY_L: 'L', ecodes.KEY_M: 'M', ecodes.KEY_N: 'N', ecodes.KEY_O: 'O',
    ecodes.KEY_P: 'P', ecodes.KEY_Q: 'Q', ecodes.KEY_R: 'R', ecodes.KEY_S: 'S', ecodes.KEY_T: 'T',
    ecodes.KEY_U: 'U', ecodes.KEY_V: 'V', ecodes.KEY_W: 'W', ecodes.KEY_X: 'X', ecodes.KEY_Y: 'Y',
    ecodes.KEY_Z: 'Z',
    # Add more mappings if your reader outputs other characters (e.g., lowercase, symbols)
}

class RFIDService:
    def __init__(self, simulation_mode=False, 
                 use_serial=True, serial_port=None, serial_vid=SERIAL_HARDWARE_VID, serial_pid=SERIAL_HARDWARE_PID, serial_baud=SERIAL_BAUD_RATE,
                 use_evdev=False, evdev_device_path=None, evdev_device_name_keyword=None, evdev_vid=None, evdev_pid=None):
        
        self.simulation_mode = simulation_mode
        self.active_mode = 'simulation' # Default

        self.simulated_rfid_tags = [
            "STUDENT_RFID_001", 
            "STUDENT_RFID_002", 
            "STUDENT_RFID_003",
            "SIM_STU_001", # Matches seeded student
            "NON_EXISTENT_RFID_999"
        ]
        self._rfid_callback = None
        self._is_scanning = False
        self._scan_thread = None
        self._original_rfid_callback = None # For single tag capture
        self._is_in_capture_mode = False    # For single tag capture
        
        # Serial Port Attributes
        self.serial_port_name = serial_port
        self.serial_vid = serial_vid
        self.serial_pid = serial_pid
        self.serial_baud = serial_baud
        self.serial_conn = None

        # Evdev Attributes
        self.evdev_device_path = evdev_device_path
        self.evdev_device_name_keyword = evdev_device_name_keyword
        self.evdev_vid = evdev_vid
        self.evdev_pid = evdev_pid
        self.evdev_device = None
        self._evdev_buffer = ""

        if self.simulation_mode:
            logging.info("RFIDService initialized in SIMULATION mode.")
            self.active_mode = 'simulation'
        elif use_evdev:
            if not EVDEV_AVAILABLE:
                logging.error("Cannot use evdev RFID reader: evdev library is not installed. Falling back to simulation.")
                self.simulation_mode = True
                self.active_mode = 'simulation'
            else:
                self.active_mode = 'evdev'
                logging.info("RFIDService initialized in EVDEV mode.")
                # Connection will be attempted in start_scanning or a dedicated connect method
        elif use_serial: # Default to serial if not simulation and not explicitly evdev
            if not PYSERIAL_AVAILABLE:
                logging.error("Cannot use serial RFID reader: pyserial library is not installed. Falling back to simulation.")
                self.simulation_mode = True
                self.active_mode = 'simulation'
            else:
                self.active_mode = 'serial'
                logging.info("RFIDService initialized in SERIAL mode.")
                # self._connect_to_reader_serial() # Connect attempt deferred to start_scanning
        else:
            logging.warning("No RFID mode specified (simulation, serial, or evdev). Defaulting to simulation.")
            self.simulation_mode = True # Ensure simulation if no valid mode
            self.active_mode = 'simulation'

    def _connect_to_reader(self):
        if self.serial_conn and self.serial_conn.is_open:
            logging.info("Serial connection already open.")
            return

        if not self.serial_port_name:
            logging.info(f"Attempting to find RFID reader with VID:PID {HARDWARE_VID:04X}:{HARDWARE_PID:04X}")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.vid == HARDWARE_VID and port.pid == HARDWARE_PID:
                    self.serial_port_name = port.device
                    logging.info(f"RFID Reader found on port: {self.serial_port_name}")
                    break
            if not self.serial_port_name:
                logging.warning("Could not automatically find RFID reader. Please specify serial_port if known.")
                # List available ports for debugging
                available_ports = [p.device for p in ports]
                logging.info(f"Available serial ports: {available_ports if available_ports else 'None'}")
                # Fallback to simulation if port not found automatically
                # logging.warning("Falling back to RFID simulation mode as reader not found.")
                # self.simulation_mode = True
                return # Stay in non-simulation mode, but scanning will likely fail until port is set

        if self.serial_port_name:
            try:
                self.serial_conn = serial.Serial(self.serial_port_name, BAUD_RATE, timeout=1)
                logging.info(f"Connected to RFID reader on {self.serial_port_name} at {BAUD_RATE} baud.")
            except serial.SerialException as e:
                logging.error(f"Failed to connect to RFID reader on {self.serial_port_name}: {e}")
                self.serial_conn = None # Ensure it's None on failure
                # logging.warning("Falling back to RFID simulation mode due to connection error.")
                # self.simulation_mode = True # Optional: Fallback to simulation on error
        else:
            logging.error("No serial port configured or detected for RFID reader.")
            # self.simulation_mode = True # Optional: Fallback

    def register_rfid_callback(self, callback):
        self._rfid_callback = callback

    def start_capture_single_tag(self, capture_callback):
        """Starts a special mode to capture a single RFID tag.

        The provided capture_callback will be called once when a tag is scanned.
        The service will then automatically revert to its previous callback.
        """
        if self._is_in_capture_mode:
            logging.warning("Already in single tag capture mode. Ignoring new request.")
            return
        
        logging.info("Starting single tag capture mode.")
        self._is_in_capture_mode = True
        self._original_rfid_callback = self._rfid_callback # Store current main callback
        self._rfid_callback = capture_callback            # Set temporary capture callback

        if not self._is_scanning:
            self.start_scanning()
        # Add checks for non-simulation modes if thread died or connection lost
        elif self.active_mode == 'serial' and (not self.serial_conn or not self.serial_conn.is_open):
            self.start_scanning()
        elif self.active_mode == 'evdev' and not self.evdev_device: # Or a better check for evdev connection
            self.start_scanning()
        elif self.simulation_mode and (not self._scan_thread or not self._scan_thread.is_alive()):
            self.start_scanning()

    def stop_capture_single_tag(self):
        """Stops the single tag capture mode and restores the original callback."""
        if not self._is_in_capture_mode:
            return
        logging.info("Stopping single tag capture mode.")
        self._rfid_callback = self._original_rfid_callback
        self._original_rfid_callback = None
        self._is_in_capture_mode = False
        # Note: This does not stop the physical scanning thread if an original callback existed.
        # It just reverts who gets notified. The main start/stop_scanning manages the thread itself.

    def _notify_rfid_scanned(self, rfid_tag):
        if self._is_in_capture_mode:
            # In capture mode, we call the current callback (which is the capture_callback)
            # then immediately stop capture mode.
            if self._rfid_callback:
                try:
                    self._rfid_callback(rfid_tag)
                except Exception as e:
                    logging.error(f"Error executing single capture RFID callback: {e}")
            self.stop_capture_single_tag() # Automatically stop capture after one tag
        elif self._rfid_callback: # Normal operation
            try:
                self._rfid_callback(rfid_tag)
            except Exception as e:
                logging.error(f"Error executing RFID callback: {e}")

    def _scan_loop_simulation(self):
        logging.info("RFID simulation scan loop started.")
        while self._is_scanning:
            time.sleep(random.uniform(3, 6)) 
            if self._is_scanning:
                simulated_tag = random.choice(self.simulated_rfid_tags)
                logging.info(f"[SIMULATED SCAN] RFID Tag: {simulated_tag}")
                self._notify_rfid_scanned(simulated_tag)
        logging.info("RFID simulation scan loop stopped.")

    def _scan_loop_serial(self):
        logging.info("Actual serial RFID scan loop started.")
        if not self.serial_conn or not self.serial_conn.is_open:
            logging.error("Serial RFID reader not connected. Actual scan loop cannot run.")
            self._is_scanning = False 
            return
        
        while self._is_scanning:
            try:
                if self.serial_conn.in_waiting > 0:
                    rfid_data = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                    if rfid_data:
                        logging.info(f"[SERIAL SCAN] Raw data: '{rfid_data}'")
                        self._notify_rfid_scanned(rfid_data)
            except serial.SerialException as e:
                logging.error(f"Serial error during RFID scan: {e}")
                if self.serial_conn and self.serial_conn.is_open: self.serial_conn.close()
                self.serial_conn = None
                self._is_scanning = False # Stop scanning on serial error
                logging.info("Serial connection lost. Stopping scan. Will attempt to reconnect on next start_scanning.")
                break 
            except UnicodeDecodeError as e:
                logging.warning(f"Unicode decode error reading from serial RFID: {e}.")
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    _ = self.serial_conn.read(self.serial_conn.in_waiting)
            except Exception as e:
                logging.error(f"Unexpected error in serial RFID scan loop: {e}")
                time.sleep(1)
            time.sleep(0.1)
        logging.info("Actual serial RFID scan loop stopped.")

    def _scan_loop_evdev(self):
        logging.info(f"Actual evdev RFID scan loop started for device: {self.evdev_device.name}")
        self._evdev_buffer = ""
        try:
            for event in self.evdev_device.read_loop():
                if not self._is_scanning: # Check if scanning was stopped externally
                    break
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    if key_event.keystate == KeyEvent.key_down: # Process on key press
                        key_code = key_event.scancode # or key_event.keycode for named keys
                        char = EVDEV_KEY_MAP.get(key_event.keycode) # Use keycode for map
                        
                        # Handle Enter key as delimiter
                        if key_event.keycode == ecodes.KEY_ENTER or key_event.keycode == ecodes.KEY_KPENTER:
                            if self._evdev_buffer:
                                logging.info(f"[EVDEV SCAN] Tag collected: {self._evdev_buffer}")
                                self._notify_rfid_scanned(self._evdev_buffer)
                                self._evdev_buffer = "" # Reset buffer
                        elif char: # If it's a character we mapped
                            self._evdev_buffer += char
                        # else: logger.debug(f"[EVDEV KEY] Ignored: {key_event.keycode}")
        except OSError as e:
            logging.error(f"OSError in evdev scan loop (device disconnected?): {e}")
            self.evdev_device = None # Mark device as disconnected/unusable
            self._is_scanning = False # Stop scanning indication
        except Exception as e:
            logging.error(f"Unexpected error in evdev scan loop: {e}")
        finally:
            if self.evdev_device: # Release grab if loop exits for any reason
                try: self.evdev_device.ungrab()
                except Exception as e_ungrab: logging.warning(f"Could not ungrab evdev device: {e_ungrab}")
            logging.info("Actual evdev RFID scan loop stopped.")

    def start_scanning(self):
        if self._is_scanning:
            logging.warning("RFID scanning is already active.")
            return

        self._is_scanning = True
        scan_started = False

        if self.simulation_mode or self.active_mode == 'simulation':
            self._scan_thread = threading.Thread(target=self._scan_loop_simulation, daemon=True)
            logging.info("Starting RFID scanning in SIMULATION mode.")
            scan_started = True
        elif self.active_mode == 'evdev':
            if not EVDEV_AVAILABLE: # Should have been caught in init, but double check
                logging.error("Cannot start evdev RFID scanning: evdev library is not available. Falling back to simulation.")
                self.simulation_mode = True; self.active_mode = 'simulation' 
                self._scan_thread = threading.Thread(target=self._scan_loop_simulation, daemon=True)
                scan_started = True
            elif self._connect_to_reader_evdev():
                self._scan_thread = threading.Thread(target=self._scan_loop_evdev, daemon=True)
                logging.info("Starting RFID scanning in EVDEV mode.")
                scan_started = True
            else:
                logging.error("Failed to connect to evdev reader. Cannot start evdev scanning. Falling back to simulation.")
                self.simulation_mode = True; self.active_mode = 'simulation' 
                self._scan_thread = threading.Thread(target=self._scan_loop_simulation, daemon=True)
                scan_started = True # Start in sim mode as fallback
        elif self.active_mode == 'serial':
            if not PYSERIAL_AVAILABLE: # Should have been caught in init
                logging.error("Cannot start serial RFID scanning: pyserial is not available. Falling back to simulation.")
                self.simulation_mode = True; self.active_mode = 'simulation' 
                self._scan_thread = threading.Thread(target=self._scan_loop_simulation, daemon=True)
                scan_started = True
            elif self._connect_to_reader_serial():
                self._scan_thread = threading.Thread(target=self._scan_loop_serial, daemon=True)
                logging.info("Starting RFID scanning in SERIAL mode.")
                scan_started = True
            else:
                logging.error("Failed to connect to serial reader. Cannot start serial scanning. Falling back to simulation.")
                self.simulation_mode = True; self.active_mode = 'simulation' 
                self._scan_thread = threading.Thread(target=self._scan_loop_simulation, daemon=True)
                scan_started = True # Start in sim mode as fallback
        
        if scan_started and self._scan_thread:
            self._scan_thread.start()
            logging.info("RFID scan thread initiated.")
        else:
            logging.warning("RFID scan thread not created or not started for the active mode.")
            self._is_scanning = False # Ensure this is false if no thread was started

    def stop_scanning(self):
        if not self._is_scanning:
            return
        self._is_scanning = False
        if self.active_mode == 'evdev' and self.evdev_device: # For evdev, read_loop might need interruption.
            # The loop breaks on self._is_scanning = False. Ungrab is in finally block of loop.
            pass 
        if self._scan_thread and self._scan_thread.is_alive():
            try: self._scan_thread.join(timeout=1.0) 
            except RuntimeError: pass # Already stopped
        self._scan_thread = None
        logging.info("RFID scanning stopped.")

    def close(self):
        self.stop_scanning()
        if self.serial_conn and self.serial_conn.is_open:
            try: self.serial_conn.close(); logging.info("RFID serial connection closed.")
            except Exception as e: logging.error(f"Error closing serial connection: {e}")
        self.serial_conn = None
        
        if self.evdev_device:
            try: 
                # Ungrab might have already happened in the scan loop's finally block
                # self.evdev_device.ungrab() # Attempt ungrab if not already done.
                self.evdev_device.close() 
                logging.info(f"Closed evdev device: {self.evdev_device.name}")
            except Exception as e: logging.error(f"Error closing evdev device: {e}")
        self.evdev_device = None

    def _connect_to_reader_serial(self):
        if self.serial_conn and self.serial_conn.is_open:
            logging.info("Serial connection already open.")
            return True

        if not self.serial_port_name:
            logging.info(f"Attempting to find serial RFID reader with VID:PID {self.serial_vid:04X}:{self.serial_pid:04X}")
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.vid == self.serial_vid and port.pid == self.serial_pid:
                    self.serial_port_name = port.device
                    logging.info(f"Serial RFID Reader found on port: {self.serial_port_name}")
                    break
            if not self.serial_port_name:
                logging.warning("Could not automatically find serial RFID reader.")
                available_ports = [p.device for p in ports]
                logging.info(f"Available serial ports: {available_ports if available_ports else 'None'}")
                return False

        if self.serial_port_name:
            try:
                self.serial_conn = serial.Serial(self.serial_port_name, self.serial_baud, timeout=1)
                logging.info(f"Connected to serial RFID reader on {self.serial_port_name} at {self.serial_baud} baud.")
                return True
            except serial.SerialException as e:
                logging.error(f"Failed to connect to serial RFID reader on {self.serial_port_name}: {e}")
                self.serial_conn = None
                return False
        else:
            logging.error("No serial port configured or detected for serial RFID reader.")
            return False
        
    def _find_evdev_device(self):
        """Finds an evdev device based on path, name keyword, or VID/PID."""
        if self.evdev_device_path:
            try:
                device = InputDevice(self.evdev_device_path)
                logging.info(f"Found evdev device by path: {device.name} ({self.evdev_device_path})")
                return device
            except Exception as e:
                logging.error(f"Error opening evdev device by path {self.evdev_device_path}: {e}")
                return None

        devices = [InputDevice(path) for path in evdev.list_devices()]
        if not devices:
            logging.warning("No evdev input devices found.")
            return None

        for device in devices:
            match = False
            if self.evdev_device_name_keyword and self.evdev_device_name_keyword.lower() in device.name.lower():
                match = True
            elif self.evdev_vid is not None and self.evdev_pid is not None and \
                 device.info.vendor == self.evdev_vid and device.info.product == self.evdev_pid:
                match = True
            
            if match:
                logging.info(f"Found evdev device: {device.name} (Path: {device.path}, VID: {device.info.vendor:04X}, PID: {device.info.product:04X})")
                return device
        
        logging.warning("Could not find a matching evdev device by name keyword, VID/PID.")
        return None

    def _connect_to_reader_evdev(self):
        if self.evdev_device:
            # How to check if an evdev device is still valid/connected without trying to read?
            # For now, assume if it exists, it's potentially usable.
            logging.info(f"Evdev device {self.evdev_device.name} already selected.")
            return True 
            
        self.evdev_device = self._find_evdev_device()
        if self.evdev_device:
            try:
                self.evdev_device.grab() # Grab for exclusive access
                logging.info(f"Successfully grabbed evdev device: {self.evdev_device.name}")
                return True
            except Exception as e: # Typically OSError if already grabbed or permissions issue
                logging.error(f"Failed to grab evdev device {self.evdev_device.name}: {e}. Check permissions or if another process is using it.")
                self.evdev_device = None # Clear if grab fails
                return False
        return False

# Example Usage (for testing this service directly)
if __name__ == '__main__':
    print("Testing RFIDService...")
    # Ensure you have pyserial installed: pip install pyserial

    def my_callback(tag_id):
        print(f"RFID SCANNED (Callback): {tag_id}")

    # --- Test with Actual Reader Mode ---
    # Set simulation_mode=False to test with your hardware
    # You might need to specify the port if auto-detection fails, e.g., RFIDService(simulation_mode=False, serial_port='COM3')
    print("\n--- Testing Actual Reader Mode ---")
    # IMPORTANT: Change simulation_mode to False to test with your actual reader.
    # If VID/PID detection fails, you might need to provide the port manually like:
    # rfid_service_actual = RFIDService(simulation_mode=False, serial_port='COMX') # Replace COMX with your port
    rfid_service_actual = RFIDService(simulation_mode=False) 
    rfid_service_actual.register_rfid_callback(my_callback)
    rfid_service_actual.start_scanning()
    
    print("Attempting to scan with actual reader for 20 seconds...")
    print("Please scan an RFID tag.")
    try:
        time.sleep(20) 
    except KeyboardInterrupt:
        print("Actual reader test interrupted by user.")
    finally:
        rfid_service_actual.stop_scanning()
        rfid_service_actual.close()
        print("RFID Actual Service test finished.")

    # --- Test with Simulation Mode (Optional) ---
    # print("\n--- Testing Simulation Mode ---")
    # rfid_sim_service = RFIDService(simulation_mode=True)
    # rfid_sim_service.register_rfid_callback(my_callback)
    # rfid_sim_service.start_scanning()
    # print("Simulating scanning for 10 seconds...")
    # try:
    #     time.sleep(10) 
    # except KeyboardInterrupt:
    #     print("Simulation interrupted.")
    # finally:
    #     rfid_sim_service.stop_scanning()
    #     rfid_sim_service.close()
    #     print("RFID Simulation Service test finished.") 