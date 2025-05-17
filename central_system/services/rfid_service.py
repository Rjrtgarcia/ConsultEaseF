import time
import threading
import logging
import random # For simulation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration for Actual Reader (placeholder) ---
# SERIAL_PORT = '/dev/ttyUSB0' # Example, might vary
# BAUD_RATE = 9600

class RFIDService:
    def __init__(self, simulation_mode=True):
        self.simulation_mode = simulation_mode
        self.simulated_rfid_tags = [
            "STUDENT_RFID_001", 
            "STUDENT_RFID_002", 
            "STUDENT_RFID_003",
            "NON_EXISTENT_RFID_999"
        ] # Predefined list for simulation
        self._rfid_callback = None
        self._is_scanning = False
        self._scan_thread = None
        
        if not self.simulation_mode:
            # Initialize actual RFID reader hardware connection here
            # Example using pyserial (conceptual):
            # try:
            #     import serial
            #     self.serial_conn = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            #     logging.info(f"Connected to RFID reader on {SERIAL_PORT}")
            # except ImportError:
            #     logging.error("pyserial library not found. Please install it: pip3 install pyserial")
            #     raise
            # except serial.SerialException as e:
            #     logging.error(f"Failed to connect to RFID reader on {SERIAL_PORT}: {e}")
            #     # Fallback to simulation or raise an error
            #     logging.warning("Falling back to RFID simulation mode due to hardware error.")
            #     self.simulation_mode = True # Fallback
            logging.warning("Actual RFID reader mode selected, but hardware integration is a placeholder.")
            # For now, if not simulation_mode, it will do nothing until real code is added.

    def register_rfid_callback(self, callback):
        """Registers a callback function to be called when an RFID tag is scanned."""
        self._rfid_callback = callback

    def _notify_rfid_scanned(self, rfid_tag):
        if self._rfid_callback:
            try:
                self._rfid_callback(rfid_tag)
            except Exception as e:
                logging.error(f"Error executing RFID callback: {e}")

    def _scan_loop_simulation(self):
        """Simulates RFID scanning by periodically calling the callback with a random tag."""
        logging.info("RFID simulation scan loop started.")
        while self._is_scanning:
            time.sleep(random.uniform(2, 5)) # Simulate delay between scans
            if self._is_scanning: # Check again, as it might have stopped during sleep
                simulated_tag = random.choice(self.simulated_rfid_tags)
                logging.info(f"[SIMULATED SCAN] RFID Tag: {simulated_tag}")
                self._notify_rfid_scanned(simulated_tag)
        logging.info("RFID simulation scan loop stopped.")

    def _scan_loop_actual(self):
        """Actual RFID scanning loop (placeholder for hardware integration)."""
        logging.info("Actual RFID scan loop started (Placeholder - No hardware interaction yet).")
        # Example using pyserial (conceptual):
        # while self._is_scanning:
        #     try:
        #         if self.serial_conn and self.serial_conn.in_waiting > 0:
        #             rfid_data = self.serial_conn.readline().decode('utf-8').strip()
        #             if rfid_data:
        #                 logging.info(f"[ACTUAL SCAN] RFID Tag: {rfid_data}")
        #                 self._notify_rfid_scanned(rfid_data)
        #     except serial.SerialException as e:
        #         logging.error(f"Error reading from serial port {SERIAL_PORT}: {e}")
        #         # Potentially try to reconnect or stop scanning
        #         self._is_scanning = False # Stop on error for now
        #         break
        #     except Exception as e:
        #         logging.error(f"Unexpected error in RFID scan loop: {e}")
        #     time.sleep(0.1) # Small delay to prevent busy-waiting
        # logging.info("Actual RFID scan loop stopped.")
        # For now, this loop will do nothing until real hardware code is added.
        while self._is_scanning:
            time.sleep(1) # Keep thread alive but inactive
        logging.info("Actual RFID scan loop stopped (Placeholder).")

    def start_scanning(self):
        if self._is_scanning:
            logging.warning("RFID scanning is already active.")
            return

        self._is_scanning = True
        if self.simulation_mode:
            self._scan_thread = threading.Thread(target=self._scan_loop_simulation, daemon=True)
        else:
            # self._scan_thread = threading.Thread(target=self._scan_loop_actual, daemon=True)
            logging.warning("Actual RFID scanning mode is a placeholder. No real scanning will occur.")
            # To prevent errors if called, let's use simulation or a dummy loop for now if not in simulation
            self._scan_thread = threading.Thread(target=self._scan_loop_actual, daemon=True) 
            # Or, you might want to raise an error if simulation_mode is False and no real implementation exists

        if self._scan_thread:
            self._scan_thread.start()
            logging.info("RFID scanning started.")

    def stop_scanning(self):
        if not self._is_scanning:
            logging.info("RFID scanning is not active.")
            return

        self._is_scanning = False
        if self._scan_thread and self._scan_thread.is_alive():
            self._scan_thread.join(timeout=2) # Wait for the thread to finish
        logging.info("RFID scanning stopped.")

    def close(self):
        """Clean up resources, like closing serial connection."""
        self.stop_scanning()
        if not self.simulation_mode and hasattr(self, 'serial_conn') and self.serial_conn:
            # if self.serial_conn.is_open:
            #     self.serial_conn.close()
            #     logging.info("RFID serial connection closed.")
            pass # Placeholder for actual closing logic

# Example Usage (for testing this service directly)
if __name__ == '__main__':
    print("Testing RFIDService...")
    
    # --- Test with Simulation Mode ---
    print("\n--- Testing Simulation Mode ---")
    def my_sim_callback(tag_id):
        print(f"SIMULATED RFID SCANNED: {tag_id}")

    rfid_sim_service = RFIDService(simulation_mode=True)
    rfid_sim_service.register_rfid_callback(my_sim_callback)
    rfid_sim_service.start_scanning()
    
    try:
        print("Simulating scanning for 10 seconds...")
        time.sleep(10) 
    except KeyboardInterrupt:
        print("Simulation interrupted.")
    finally:
        rfid_sim_service.stop_scanning()
        rfid_sim_service.close()
        print("RFID Simulation Service test finished.")

    # --- Test with Actual Reader Mode (Placeholder) ---
    # print("\n--- Testing Actual Reader Mode (Placeholder) ---")
    # def my_actual_callback(tag_id):
    #     print(f"ACTUAL RFID SCANNED: {tag_id}")

    # rfid_actual_service = RFIDService(simulation_mode=False)
    # rfid_actual_service.register_rfid_callback(my_actual_callback)
    # rfid_actual_service.start_scanning()
    
    # try:
    #     print("Placeholder for actual scanning for 10 seconds (will do nothing)...")
    #     print("Manually trigger your RFID reader if you have one connected and configured.")
    #     time.sleep(10) 
    # except KeyboardInterrupt:
    #     print("Actual reader test interrupted.")
    # finally:
    #     rfid_actual_service.stop_scanning()
    #     rfid_actual_service.close()
    #     print("RFID Actual Service (Placeholder) test finished.") 