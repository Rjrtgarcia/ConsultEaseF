# Active Context: ConsultEase System

## 1. Current Focus
The primary focus is to move the ConsultEase project to a "deployment-ready" state. This involves several major workstreams based on recent user clarifications:
1.  **Central System UI Overhaul:** Modernizing the PyQt5 UI for a user-friendly experience.
2.  **ESP32 Faculty Desk Unit Development:** Implementing the complete firmware logic (BLE, Display, MQTT).
3.  **Integration & End-to-End Testing:** Ensuring robust interaction between the Central System and ESP32 units (Level B testing: full end-to-end with actual units).
4.  **Comprehensive Documentation:** Creating deployment guides, troubleshooting manuals, and user manuals for all user types.

## 2. Recent Activities
*   Resolved critical bugs in the Admin Dashboard related to database schema updates and PyQt5 widget lifecycle.
*   Successfully integrated `pyserial` for hardware RFID reading in the Central System, including a feature for admins to capture new student RFID tags directly.
*   Added `student_number` and `course` fields to the `students` database table and integrated them through the `AdminDashboardScreen` and `AdminController`.
*   Received user clarification on the scope of "complete and make it ready for deployment":
    *   No specific advanced network/security configurations required for RPi/MQTT/Postgres for this phase.
    *   ESP32 logic is mostly unimplemented and is a major task.
    *   Testing level is B (full end-to-end with actual ESP32s).
    *   Key new feature: Modernize and improve UI/UX.
    *   Documentation: Deployment guide, troubleshooting, and user manuals are required.
    *   Definition of complete: Involves adding significant new functionality (ESP32, UI overhaul) and comprehensive documentation.
*   Updated `progress.md` to reflect the current project state and goals.

## 3. Next Steps
1.  **Develop a Comprehensive Project Plan:** Create a detailed, phased plan covering:
    *   Phase A: UI Overhaul (Central System - PyQt5).
    *   Phase B: ESP32 Development (Firmware for Faculty Desk Units).
    *   Phase C: Integration & End-to-End Testing.
    *   Phase D: Documentation (Deployment, Troubleshooting, User Manuals).
2.  **Present Project Plan:** Submit the plan to the user for review and approval.
3.  **Execute Approved Plan:** Begin implementation of the first phase of the approved plan.

## 4. Active Decisions & Considerations
*   **UI Modernization:** This is a top priority for the Central System. The approach will likely involve reviewing current UI flows, potentially using custom styling (QSS), and focusing on intuitive layouts.
*   **ESP32 Development from Scratch:** Since the ESP32 logic is minimal, this will be a substantial development effort. Placeholder BLE IDs will be used initially.
*   **End-to-End Testing:** Will require a (simulated or actual) ESP32 unit to interact with the RPi. The focus is on validating the complete workflow.
*   **Documentation:** Will be created progressively, likely after major components are stable.
*   **Iterative Approach:** While a plan will be in place, flexibility will be needed, especially during UI design and ESP32 development.

## 5. Additional Notes
*   The project involves both hardware and software components, requiring careful integration planning.
*   The custom instructions regarding Memory Bank management and planning mode are being actively followed.
*   The user has provided a very detailed specification, which will serve as the primary source of truth for planning and development.
*   **Project will start with an MVP (Minimum Viable Product) focusing on core student-faculty interaction.**
*   **MQTT broker and PostgreSQL server will be new setups, included in the project scope.**
*   **Faculty will use personal BLE beacons; the system will scan for these.**
*   **RFID simulation will use a predefined list of test student profiles.**
*   **Backward compatible MQTT topics are for forward-thinking (lower MVP priority).**
*   **PyQt5 will be used for the Central System UI.** 