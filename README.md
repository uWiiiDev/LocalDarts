# 🎯 LocalDarts – Lokales 3-Kamera Autodarts System

**LocalDarts** ist eine komplett lokale, quelloffene Alternative zu *Autodarts.io* ohne Cloud-Zwang. Das System erkennt geworfene Steeldarts in Echtzeit über bis zu **3 USB-Kameras** mittels klassischem **OpenCV Computer Vision** (Hintergrund-Subtraktion, Konturanalyse & Multi-Kamera-Sichtlinien-Triangulation) und bietet ein modernes Web-Scoreboard für **bis zu 6 Spieler** auf **Deutsch, Englisch und Französisch**.

---

## ✨ Highlights & Features

- **📹 3-Kamera OpenCV Erkennung & Triangulation**
  - Unterstützt 1 bis 3 USB-Kameras (V4L2 unter Linux, DirectShow unter Windows) sowie einen integrierten **3D-Kamera-Simulator** zum Testen ohne angeschlossene Hardware.
  - **Interaktive 4-Punkt-Homographie-Kalibrierung** direkt im Browser (inkl. ziehbarer Punkte P1–P4, Live-Spinnennetz-Overlay und entzerrter Top-Down-Kontrollansicht).
  - **Automatische Takeout-Erkennung**: Sobald die Pfeile aus dem Board gezogen werden, schaltet das System automatisch zum nächsten Spieler weiter.
- **👥 1 bis 6 Spieler gleichzeitig**
  - Dynamisches Scoreboard-Layout für bis zu 6 Spieler inkl. Checkout-Vorschlägen, 3-Dart-Average, First-9-Average, Doppelquote und 180er-Statistik.
- **🌍 Mehrsprachige Oberfläche & Voice-Caller**
  - Komplett umschaltbar zwischen **🇩🇪 Deutsch**, **🇬🇧 English** und **🇫🇷 Français** (inkl. Sprachausgabe des Callers & Soundeffekten).
- **📖 16 integrierte Dart-Spiele (inkl. Kurzanleitung im Menü)**
  - **Turnier & Klassiker:**
    1. **X01** (`301` / `501` / `701` / `170` Checkout, Straight/Double In, Double/Single/Master Out)
    2. **Cricket** (`Standard` & `Cut-Throat`)
    3. **Around the Clock** (`1` bis `20` + `Bull`)
    4. **Shanghai** (Runden `1–20` + Sofort-Sieg bei Single + Double + Triple)
    5. **Freies Training / Highscore**
  - **Party & Mehrspieler:**
    6. **Elimination** (*Mensch ärgere dich nicht* – `0` auf `301`/`501`, Gleichstand setzt Gegner auf `0` zurück)
    7. **Killer** (Eigene Doppel-Zahl, 3 Leben aufbauen & Gegner eliminieren)
    8. **Halve It / Halbieren** (8 feste Zielrunden – Fehlwurf halbiert den Punktestand)
    9. **Gotcha** (Bis `301`, mit 100er-Meilenstein-Bust & Bullseye-Punktestand-Tausch)
    10. **Tic-Tac-Toe Darts** ($3\times3$-Sektor-Raster mit Bull in der Mitte)
    11. **Bermuda Triangle** (13 Runden von `12` bis `Double Bull`)
  - **Profi- & Checkout-Training:**
    12. **Bob's 27** (Klassisches Doppel-Training `D1` bis `DBull`)
    13. **JDC Challenge** (19 Runden: Shanghai `10–15` + Doubles `D1–DBull` + Shanghai `15–20`)
    14. **Catch 40** (Alle Checkouts von `61` bis `100` in max. 6 Darts)
    15. **121 Checkout-Leiter** (Ab `121` in 9 Darts checken)
    16. **Bulls-Eye / Scoring 100** (99 Darts Präzisionstraining auf Zielsektor)

---

## 🚀 Schnellstart

### 🪟 Windows (Komplettpaket inkl. lokalem Python – keine Installation nötig!)
1. Lade unter **[Releases](../../releases)** die Datei **`LocalDarts-Windows-Full-Offline.zip`** herunter und entpacke sie.
2. Doppelklicke auf **`start_windows.bat`**.
3. Das enthaltene portable Python (`python_embed\`) startet automatisch den Server und öffnet LocalDarts als Desktop-App-Fenster!

### 🐧 Linux
```bash
./start.sh
```
Danach im Browser **[http://localhost:8000](http://localhost:8000)** öffnen.

---

## 🛠️ Eigenes Windows-Paket unter Linux oder Windows neu bauen

- **Unter Linux (erzeugt `dist/LocalDarts-Windows-Full-Offline.zip` inkl. eingebettetem Windows-Python):**
  ```bash
  ./build_windows_bundle_on_linux.sh
  ```
- **Unter Windows (erzeugt `LocalDarts.exe` via PyInstaller bzw. `LocalDarts-Setup.exe` via Inno Setup):**
  - `build_windows_exe.bat` ausführen
  - Optional `installer_windows.iss` mit Inno Setup kompilieren
