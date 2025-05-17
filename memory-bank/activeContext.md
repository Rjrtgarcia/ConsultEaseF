# Active Context: ConsultEase System

## 1. Current Focus
As of the start of this session, the primary focus is on understanding the comprehensive "ConsultEase System Development Specification" provided by the user. The immediate goal is to establish the initial Memory Bank documentation and then formulate a set of clarifying questions to ensure a thorough understanding before proceeding with a detailed development plan.

## 2. Recent Activities
*   Received and parsed the detailed system specification.
*   Initiated the creation of core Memory Bank files (`projectbrief.md`, `productContext.md`).

## 3. Next Steps
1.  ~~Complete the creation of the initial set of Memory Bank files:~~
    *   ~~`activeContext.md` (this file)~~
    *   ~~`systemPatterns.md`~~
    *   ~~`techContext.md`~~
    *   ~~`progress.md`~~
2.  ~~Formulate 4-6 clarifying questions based on the provided specification.~~
3.  ~~Present these questions to the user.~~
4.  Process user's answers to clarifying questions.
5.  Update Memory Bank files (`techContext.md`, `systemPatterns.md` if needed) with new information.
6.  Develop a comprehensive project plan focusing on an MVP (Minimum Viable Product).
7.  Present the project plan to the user for approval.

## 4. Active Decisions & Considerations
*   The project involves both hardware and software components, requiring careful integration planning.
*   The custom instructions regarding Memory Bank management and planning mode are being actively followed.
*   The user has provided a very detailed specification, which will serve as the primary source of truth for planning and development.
*   **Project will start with an MVP (Minimum Viable Product) focusing on core student-faculty interaction.**
*   **MQTT broker and PostgreSQL server will be new setups, included in the project scope.**
*   **Faculty will use personal BLE beacons; the system will scan for these.**
*   **RFID simulation will use a predefined list of test student profiles.**
*   **Backward compatible MQTT topics are for forward-thinking (lower MVP priority).**
*   **PyQt5 will be used for the Central System UI.** 