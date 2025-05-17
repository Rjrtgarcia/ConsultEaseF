#ifndef BLE_MODULE_H
#define BLE_MODULE_H

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

void ble_init();
// Returns true if the target beacon is detected with RSSI above threshold
bool ble_check_beacon_presence(const char* target_beacon_id, int rssi_threshold);

#endif // BLE_MODULE_H 