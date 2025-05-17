#include "ble_module.h"
#include "config.h"
#include "Arduino.h"

static BLEScan* pBLEScan;
static bool beaconFoundThisScan = false;
static int foundBeaconRSSI = -200; // Initialize to a very low value

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) override {
        // Compare the MAC address of the advertised device with our target beacon ID
        if (advertisedDevice.getAddress().toString() == FACULTY_PERSONAL_BEACON_ID) {
            Serial.print("Target Beacon Found: ");
            Serial.print(advertisedDevice.getAddress().toString().c_str());
            Serial.print(", RSSI: ");
            Serial.println(advertisedDevice.getRSSI());
            beaconFoundThisScan = true;
            foundBeaconRSSI = advertisedDevice.getRSSI();
            // Optional: Stop scan once found to save power, but might miss it if it goes out of range quickly
            // pBLEScan->stop(); 
        }
        // else {
        //     Serial.print("Found other BLE device: ");
        //     Serial.println(advertisedDevice.getAddress().toString().c_str());
        // }
    }
};

void ble_init() {
    Serial.println("Initializing BLE...");
    BLEDevice::init(""); // Initialize BLE, device name can be empty for scanner
    pBLEScan = BLEDevice::getScan(); // Create new scan
    pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pBLEScan->setActiveScan(true); // Active scan uses more power, but gets results faster
    pBLEScan->setInterval(100); // Scan interval in ms
    pBLEScan->setWindow(99);  // Scan window in ms, should be less than or equal to interval
    Serial.println("BLE Initialized.");
}

// Returns true if the target beacon is detected with RSSI above threshold
bool ble_check_beacon_presence(const char* target_beacon_id, int rssi_threshold) {
    beaconFoundThisScan = false; // Reset flag for current scan cycle
    foundBeaconRSSI = -200;
    Serial.println("Starting BLE scan...");
    
    // Perform a scan for the duration specified in config
    // Note: BLEScanResults foundDevices = pBLEScan->start(BLE_SCAN_DURATION_SECONDS, false); is blocking.
    // For continuous non-blocking scan, you might run pBLEScan->start() in a separate task
    // or manage scan start/stop in the main loop with millis().
    // For this MVP, a short blocking scan is used in each check.
    
    pBLEScan->start(BLE_SCAN_DURATION_SECONDS, false); // Blocking scan for specified duration, `false` means don't delete results after scan
    Serial.println("BLE Scan complete.");
    // pBLEScan->clearResults(); // Clear results from this scan to keep memory usage low for next scan

    if (beaconFoundThisScan) {
        if (foundBeaconRSSI >= rssi_threshold) {
            Serial.printf("Beacon %s FOUND with RSSI %d (>= threshold %d)\n", target_beacon_id, foundBeaconRSSI, rssi_threshold);
            return true;
        } else {
            Serial.printf("Beacon %s found but RSSI %d is BELOW threshold %d\n", target_beacon_id, foundBeaconRSSI, rssi_threshold);
            return false;
        }
    } else {
        Serial.printf("Beacon %s NOT found in this scan cycle.\n", target_beacon_id);
        return false;
    }
} 