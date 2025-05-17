# ConsultEase System

A system for enhanced student-faculty interaction, comprising a Central System (Raspberry Pi) and Faculty Desk Units (ESP32).

## Project Structure

- `central_system/`: Contains the Python PyQt5 application for the Raspberry Pi.
- `faculty_desk_unit/`: Contains the C++/Arduino code for the ESP32-based faculty desk units.
- `memory-bank/`: Contains project documentation and context files.
- `documentation/`: Will contain detailed diagrams, schema, etc.

## Phase 0: Setup Instructions

### 1. Central System (Raspberry Pi 4 - Bookworm 64-bit)

**a. System Updates & Python Tools:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-dev build-essential
sudo apt install -y python3-pyqt5 pyqt5-dev-tools
```

**b. PostgreSQL Server:**
```bash
sudo apt install -y postgresql postgresql-contrib
# Post-install: configure user/database (see detailed plan or memory-bank/techContext.md)
# Example:
# sudo -u postgres psql
# ALTER USER postgres PASSWORD 'your_password';
# CREATE DATABASE consultease_db;
# CREATE USER consultease_user WITH PASSWORD 'app_password';
# GRANT ALL PRIVILEGES ON DATABASE consultease_db TO consultease_user;
# \q
# Edit /etc/postgresql/{version}/main/pg_hba.conf if needed and restart: sudo systemctl restart postgresql
```

**c. Mosquitto MQTT Broker:**
```bash
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### 2. Faculty Desk Unit (ESP32)

**a. Development Environment:**
   - **Recommended**: VS Code with the PlatformIO IDE extension.
   - **Alternative**: Arduino IDE.

**b. ESP32 Board Support:**
   - For Arduino IDE: Add `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json` to Board Manager URLs and install "esp32".
   - For PlatformIO: It will handle toolchain installation when you initialize or build the project in `faculty_desk_unit/`.

**c. Libraries (managed via `platformio.ini` or Arduino Library Manager):**
   - TFT Display (e.g., `TFT_eSPI` for ST7789)
   - MQTT Client (e.g., `PubSubClient`)
   - (WiFi and BLE are part of the ESP32 core/SDK)

### 3. Git Repository
This project is managed using Git. Ensure you have Git installed.
```bash
# Already initialized in the project root
cd /path/to/ConsultEaseF
git status
```

## Next Steps
Proceed to Phase 1: Core Central System - Student Interaction (MVP). 