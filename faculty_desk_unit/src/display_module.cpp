#include "display_module.h"
#include "config.h"

TFT_eSPI tft = TFT_eSPI(); // Invoke custom library startup file

// Basic layout parameters (adjust for your 2.4" ST7789, typically 240x320 or 320x240)
#define SCREEN_WIDTH  tft.width()  // Typically 240 for ST7789 in portrait
#define SCREEN_HEIGHT tft.height() // Typically 320 for ST7789 in portrait

#define HEADER_HEIGHT 30
#define STATUS_TEXT_Y (HEADER_HEIGHT + 20)
#define MSG_AREA_Y (STATUS_TEXT_Y + 60)
#define CONN_STATUS_Y (SCREEN_HEIGHT - 20)

void display_init() {
    tft.init();
    tft.setRotation(0); // Adjust rotation as needed (0, 1, 2, 3)
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setTextDatum(MC_DATUM); // Middle-Center datum
    
    // Draw header area (e.g., faculty name)
    tft.fillRect(0, 0, SCREEN_WIDTH, HEADER_HEIGHT, TFT_DARKCYAN);
    tft.setTextColor(TFT_WHITE, TFT_DARKCYAN);
    tft.setTextDatum(MC_DATUM);
    tft.drawString(FACULTY_NAME, SCREEN_WIDTH / 2, HEADER_HEIGHT / 2 + 2, 2); // Font 2 for name
    display_show_connection_status("WiFi: ?", "MQTT: ?");
}

void display_set_faculty_name(const char* name) {
    tft.fillRect(0, 0, SCREEN_WIDTH, HEADER_HEIGHT, TFT_DARKCYAN);
    tft.setTextColor(TFT_WHITE, TFT_DARKCYAN);
    tft.setTextDatum(MC_DATUM);
    tft.drawString(name, SCREEN_WIDTH / 2, HEADER_HEIGHT / 2 + 2, 2);
}

void display_set_status(const char* status_text, bool is_present) {
    // Clear previous status area
    tft.fillRect(0, HEADER_HEIGHT + 5, SCREEN_WIDTH, 50, TFT_BLACK);
    
    tft.setTextDatum(MC_DATUM);
    tft.setTextPadding(SCREEN_WIDTH - 20); // Padding for text background

    if (is_present) {
        tft.setTextColor(TFT_GREEN, TFT_BLACK);
    } else {
        tft.setTextColor(TFT_RED, TFT_BLACK);
    }
    tft.drawString(status_text, SCREEN_WIDTH / 2, STATUS_TEXT_Y, 4); // Font 4 for status
    tft.setTextPadding(0); // Reset padding
}

// Simple message display (will be overwritten by next status update or message)
void display_show_message(const char* title, const char* message, int duration_ms) {
    tft.fillRect(0, MSG_AREA_Y, SCREEN_WIDTH, SCREEN_HEIGHT - MSG_AREA_Y - 25, TFT_BLACK); // Clear message area
    tft.setTextColor(TFT_YELLOW, TFT_BLACK);
    tft.setTextDatum(TC_DATUM); // Top-Center
    tft.drawString(title, SCREEN_WIDTH / 2, MSG_AREA_Y + 10, 2); // Font 2 for title

    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setTextDatum(TL_DATUM); // Top-Left for message body
    tft.setCursor(10, MSG_AREA_Y + 35);
    tft.setTextWrap(true);
    tft.print(message);
    tft.setTextWrap(false);
    // If duration_ms > 0, a timer in main loop should handle clearing it.
    // For simplicity here, it just displays. Main loop needs to manage timed messages.
}

void display_clear() {
    tft.fillScreen(TFT_BLACK);
    display_init(); // Re-draw basic structure
}

void display_show_connection_status(const char* wifi_status, const char* mqtt_status) {
    tft.fillRect(0, CONN_STATUS_Y - 15, SCREEN_WIDTH, 20, TFT_DARKGREY);
    tft.setTextColor(TFT_WHITE, TFT_DARKGREY);
    tft.setTextDatum(TL_DATUM);
    tft.drawString(wifi_status, 5, CONN_STATUS_Y - 10, 2); // Font 2
    tft.setTextDatum(TR_DATUM);
    tft.drawString(mqtt_status, SCREEN_WIDTH - 5, CONN_STATUS_Y - 10, 2); // Font 2
} 