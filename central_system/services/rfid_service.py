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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration for Actual Reader ---
HARDWARE_VID = 0xFFFF # Provided by user
HARDWARE_PID = 0x0035 # Provided by user
BAUD_RATE = 9600      # Common default, adjust if your reader uses a different rate

class RFIDService:
    def __init__(self, simulation_mode=False, serial_port=None):
        self.simulation_mode = simulation_mode
        self.serial_port_name = serial_port
        self.serial_conn = None
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
        
        if not self.simulation_mode:
            if not PYSERIAL_AVAILABLE:
                logging.error("Cannot use actual RFID reader: pyserial library is not installed.")
                logging.warning("Falling back to RFID simulation mode.")
                self.simulation_mode = True
            else:
                self._connect_to_reader()

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

    def _notify_rfid_scanned(self, rfid_tag):
        if self._rfid_callback:
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

    def _scan_loop_actual(self):
        logging.info("Actual RFID scan loop started.")
        if not self.serial_conn or not self.serial_conn.is_open:
            logging.error("RFID reader not connected or port not open. Actual scan loop cannot run.")
            # Try to reconnect once, then abort if still fails
            self._connect_to_reader()
            if not self.serial_conn or not self.serial_conn.is_open:
                 logging.error("Failed to reconnect to RFID reader. Stopping actual scan loop.")
                 self._is_scanning = False # Stop the loop indication
                 # Optionally notify UI or main app about hardware failure
        
        while self._is_scanning:
            if not self.serial_conn or not self.serial_conn.is_open:
                logging.warning("Serial connection lost. Attempting to reconnect...")
                self._connect_to_reader()
                if not self.serial_conn or not self.serial_conn.is_open:
                    logging.error("Reconnect failed. Stopping scan.")
                    self._is_scanning = False
                    break # Exit loop
                else:
                    logging.info("Successfully reconnected to RFID reader.")
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    # Read a line, assuming the reader sends data terminated by a newline
                    # Adjust encoding and strip characters as necessary based on your reader's output
                    rfid_data = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                    if rfid_data: # Ensure it's not an empty string
                        logging.info(f"[ACTUAL SCAN] Raw data: '{rfid_data}'")
                        # Further parsing might be needed here depending on the reader's output format
                        # For example, if it sends "ID: AABBCCDD", you'd parse out "AABBCCDD"
                        parsed_tag = rfid_data # Assume direct tag for now
                        self._notify_rfid_scanned(parsed_tag)
            except serial.SerialException as e:
                logging.error(f"Serial error during RFID scan: {e}")
                # Attempt to close and reopen the connection or stop
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                self.serial_conn = None
                logging.info("Serial connection closed due to error. Will attempt to reconnect.")
                time.sleep(2) # Wait a bit before trying to reconnect in the next loop iteration
            except UnicodeDecodeError as e:
                logging.warning(f"Unicode decode error reading from RFID: {e}. Raw data might not be ASCII or UTF-8.")
                # You might want to read raw bytes and inspect them if this happens often
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    _ = self.serial_conn.read(self.serial_conn.in_waiting) # Clear buffer
            except Exception as e:
                logging.error(f"Unexpected error in actual RFID scan loop: {e}")
                time.sleep(1) # Prevent rapid error looping
            time.sleep(0.1) # Small delay to be friendly to the CPU
        logging.info("Actual RFID scan loop stopped.")

    def start_scanning(self):
        if self._is_scanning:
            logging.warning("RFID scanning is already active.")
            return

        self._is_scanning = True
        if self.simulation_mode:
            self._scan_thread = threading.Thread(target=self._scan_loop_simulation, daemon=True)
            logging.info("Starting RFID scanning in SIMULATION mode.")
        else:
            if not PYSERIAL_AVAILABLE:
                logging.error("Cannot start actual RFID scanning: pyserial is not available. Falling back to simulation.")
                self.simulation_mode = True # Force simulation
                self._scan_thread = threading.Thread(target=self._scan_loop_simulation, daemon=True)
            elif not self.serial_conn or not self.serial_conn.is_open:
                logging.warning("Actual RFID reader not connected. Attempting to connect before starting scan loop.")
                self._connect_to_reader()
                if not self.serial_conn or not self.serial_conn.is_open:
                    logging.error("Failed to connect to RFID reader. Cannot start actual scanning. Check connection/port.")
                    # Optionally fallback to simulation or just don't start
                    self._is_scanning = False
                    return # Don't start the thread if connection failed
                else:
                    logging.info("Starting RFID scanning in ACTUAL hardware mode.")
                    self._scan_thread = threading.Thread(target=self._scan_loop_actual, daemon=True)
            else:
                logging.info("Starting RFID scanning in ACTUAL hardware mode.")
                self._scan_thread = threading.Thread(target=self._scan_loop_actual, daemon=True)
        
        if self._scan_thread:
            self._scan_thread.start()
            logging.info("RFID scan thread initiated.")
        else:
            logging.warning("Scan thread not created.")

    def stop_scanning(self):
        if not self._is_scanning:
            # logging.info("RFID scanning is not active.") # Can be noisy
            return

        self._is_scanning = False
        if self._scan_thread and self._scan_thread.is_alive():
            try:
                self._scan_thread.join(timeout=1.5) # Wait for the thread to finish
            except RuntimeError as e:
                logging.warning(f"RuntimeError joining scan thread: {e} (possibly already stopped or never started properly)")
        self._scan_thread = None
        logging.info("RFID scanning stopped.")

    def close(self):
        self.stop_scanning()
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logging.info("RFID serial connection closed.")
            except Exception as e:
                logging.error(f"Error closing serial connection: {e}")
        self.serial_conn = None

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