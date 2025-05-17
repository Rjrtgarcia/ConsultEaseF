#ifndef DISPLAY_MODULE_H
#define DISPLAY_MODULE_H

#include <TFT_eSPI.h>

void display_init();
void display_set_faculty_name(const char* name);
void display_set_status(const char* status_text, bool is_present);
void display_show_message(const char* title, const char* message, int duration_ms = 0);
void display_clear();
void display_show_connection_status(const char* wifi_status, const char* mqtt_status);

#endif // DISPLAY_MODULE_H 