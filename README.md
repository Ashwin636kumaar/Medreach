# MedReach Web Application (Python Edition)

The standalone **Python Web Application** for the **MedReach Diagnostics Field Suite**. It complements the native mobile application (`MedReachNative`), allowing field coordinators, phlebotomists, and managers to run and inspect the application on any desktop or laptop browser.

---

### Features

1. **Dual Viewing Modes (Switch with 1 Click)**:
   - 📱 **Mobile App Simulator**: Realistic interactive smartphone frame with the exact mobile UI, status bar, screen transitions, and bottom sheets.
   - 💻 **Desktop Enterprise Portal**: Widescreen healthcare logistics dashboard with KPI metrics, real-time patient tables, and cold-chain compliance.

2. **Complete Mobile Flow Replicated in Python**:
   - **Login Screen**: Field executive authentication (`ashok.field@medreach.com` / `password123`).
   - **Home Dashboard**: Total collections banner (24, -2°C, EDTA 6, Citrate 6, Serum 2, +10), route distance, filter tabs (Pending/Completed), and real-time search.
   - **Patient Details**: Test groups (CBC, Lipid, Thyroid) with color-coded tube caps (Lavender EDTA, Red Serum, Blue Citrate), barcode association, and collection completion.
   - **Center Collection Details**: Processing center & collection center dropdowns, unique reference numbers, and **Batchsheet Barcode** with **LIMS Fetch**!
   - **Live Web Camera Barcode Scanner**: WebRTC camera stream inside Google Lens-style reticle with white corner brackets and animated red laser beam.

3. **Database Integration**:
   - Directly connects to MySQL database `medreach_db` (with automatic SQLite fallback).

---

### How to Run

1. Open a terminal in this directory:
   ```bash
   cd C:\Users\Dell\.gemini\antigravity\scratch\MedReachWeb
   ```

2. Start the server:
   ```bash
   python server.py
   ```

3. Open your browser:
   👉 **http://localhost:5000**
