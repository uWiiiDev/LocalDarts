# 🎯 LocalDarts – Ausführliche Hilfe & Kalibrierungs-Anleitung

Willkommen bei **LocalDarts**, deinem lokalen 3-Kamera-Steeldart-System!  
Diese Anleitung erklärt dir Schritt für Schritt, wie du deine **3 USB-Kameras exakt kalibrierst**, wie du die **Framerate (FPS)** und Erkennungsparameter einstellst und wie du das Maximum an Erkennungsgenauigkeit herausholst.

---

## 1. 📷 Die 3 USB-Kameras anschließen & erkennen

1. Verbinde deine 3 USB-Kameras mit dem PC (am besten verteilt auf verschiedene USB-Anschlüsse oder über einen aktiven USB-3.0-Hub).
2. Öffne **LocalDarts** (`http://localhost:8000`) und wechsle oben in den Reiter **„📷 Kamera-Kalibrierung“**.
3. Klicke links auf den Button:  
   **`🔍 Alle 3 USB-Kameras neu suchen & automatisch zuweisen`**
4. LocalDarts öffnet nun alle 3 Kameras automatisch im bandbreitensparenden **MJPG-Modus** und weist sie `Kamera 1`, `Kamera 2` und `Kamera 3` zu.
   - *Falls dein PC zusätzlich eine eingebaute Laptop-Webcam hat:* Du kannst für jeden Kamera-Slot (`Kamera 1`, `Kamera 2`, `Kamera 3`) über das Dropdown **„Video-Quelle“** gezielt auswählen, welche `USB-Kamera #0..#8` verwendet werden soll, und auf **„Zuweisen“** klicken.

---

## 2. 🎯 Schritt-für-Schritt: Die 4-Punkt-Kalibrierung

Damit LocalDarts aus den 3 schrägen Kamerabildern millimetergenau berechnen kann, in welchem Feld eine Pfeilspitze steckt, benötigt jede Kamera **4 feste Referenzpunkte am äußeren Draht des Double-Rings**.

> **💡 WICHTIGSTER MERKSATZ FÜR ALLE 3 KAMERAS:**  
> Du klickst bei **jeder** der 3 Kameras immer auf **dieselben 4 Stellen der echten Dartscheibe** (orientiert an den **Zahlen `20`, `6`, `3` und `11`** auf dem Board) – auch wenn Kamera 2 und Kamera 3 seitlich oder schräg auf die Scheibe blicken und die `20` in deren Kamerabild deshalb unten links oder unten rechts erscheint!

### Die 4 Punkte bei der Standard-Vorlage („Autodarts Standard-Drähte: `5|20`, `13|6`, `17|3`, `8|11`“):

Alle 4 Punkte liegen **außen auf dem äußeren Draht des Double-Rings** (dort, wo das Doppelfeld aufhört und das schwarze Zahlenfeld beginnt):

```
                    [ 20 ]
              🔴 P1 (Draht 5|20)
                \      |      /
                 \  D20|     /
                  \____|____/
                  /         \
     🔵 P4       |           |      🟡 P2
  (Draht 8|11)   |    BULL   |   (Draht 13|6)
    [ 11 ]       |     🎯    |      [ 6 ]
                  \         /
                   \_______/
                  /    |    \
                 /     |D3   \
                /      |      \
              🟢 P3 (Draht 17|3)
                     [ 3 ]
```

1. 🔴 **Punkt `P1` (Rot) – Draht `5 | 20`:**
   - Suche auf deiner Dartscheibe die Zahl **20**.
   - Klicke genau auf die **Kreuzung, wo der Trenndraht zwischen der `5` und der `20` außen auf den äußeren Double-Draht trifft** (linke obere Außenecke des `D20`-Feldes).
2. 🟡 **Punkt `P2` (Gelb) – Draht `13 | 6`:**
   - Suche auf deiner Dartscheibe die Zahl **6**.
   - Klicke genau auf die **Kreuzung, wo der Trenndraht zwischen der `13` und der `6` außen auf den äußeren Double-Draht trifft** (obere Außenecke des `D6`-Feldes).
3. 🟢 **Punkt `P3` (Grün) – Draht `17 | 3`:**
   - Suche auf deiner Dartscheibe die Zahl **3**.
   - Klicke genau auf die **Kreuzung, wo der Trenndraht zwischen der `17` und der `3` außen auf den äußeren Double-Draht trifft** (rechte Außenecke des `D3`-Feldes).
4. 🔵 **Punkt `P4` (Blau) – Draht `8 | 11`:**
   - Suche auf deiner Dartscheibe die Zahl **11**.
   - Klicke genau auf die **Kreuzung, wo der Trenndraht zwischen der `8` und der `11` außen auf den äußeren Double-Draht trifft** (untere Außenecke des `D11`-Feldes).

*(Alternativ kannst du im Dropdown „Kalibrierungs-Vorlage“ auch **„12 / 3 / 6 / 9 Uhr Mitte (Außenkante D20, D6, D3, D11)“** wählen, wenn du lieber mittig auf die Außenkante von D20, D6, D3 und D11 klickst).*

### Feinjustierung per Maus (Drag & Drop):
- Sobald alle 4 Punkte (`P1` bis `P4`) gesetzt sind, erscheint sofort ein **grünes Spinnennetz** über deinem Kamerabild und rechts daneben die **„2. Entzerrte Draufsicht“**.
- **Prüfung:** Schau dir das Bullseye, den Triple-Ring und den Double-Ring an. Liegt das grüne Netz noch um 1–2 Millimeter versetzt?
- **Korrektur:** Klicke einfach mit der Maus auf einen der farbigen Kreise `P1`, `P2`, `P3` oder `P4` im linken Bild, halte die Maustaste gedrückt und **ziehe den Punkt minimal**, bis das grüne Spinnennetz exakt auf allen Drähten deiner echten Dartscheibe liegt!
- Klicke auf **„💾 Kalibrierung speichern“** und wiederhole das Ganze für **`Kamera 2`** und **`Kamera 3`**.

---

## 3. ⚡ Framerate (FPS) & Vorschau-Geschwindigkeit hochsetzen

Im Reiter **„📷 Kamera-Kalibrierung“** findest du links unter **„⚡ Kamera-Framerate (FPS)“** die Einstellung für die Bildrate:

- **15 FPS (USB-Sparmodus):** Ideal, wenn alle 3 Kameras an einem einzigen passiven USB-2.0-Hub hängen.
- **20 FPS (Autodarts-Standard):** Beste Balance aus flüssiger Erkennung und geringer CPU-/USB-Last.
- **30 FPS (Schnell / Flüssig):** Höhere Bildrate für schnellere Bewegungserkennung (empfohlen bei direkten USB-Ports am Mainboard).
- **60 FPS (Maximum):** Nur für High-Speed-USB-Kameras an eigenen USB-3.0-Controllern.

Zusätzlich läuft die OpenCV-Erkennungsschleife im Hintergrund mit bis zu **25 Prüfungen pro Sekunde**, und die Vorschau im Browser aktualisiert sich automatisch flüssig.

---

## 4. 🔬 OpenCV Erkennungs-Feintuning & Tipps für 99 %+ Genauigkeit

1. **„📷 Leeres Board“ vor Spielbeginn klicken:**
   - Wenn das Board frei von Pfeilen ist (und kein Schatten deiner Hand im Bild ist), klicke einmal auf **„📷 Leeres Board“**. Damit merkt sich LocalDarts das exakte Referenzbild deiner leeren Scheibe.
2. **Differenz-Schwellwert (`Standard: 26`):**
   - Bestimmt, ab welchem Helligkeitsunterschied ein Pixel als „Veränderung (Pfeil)“ gewertet wird.
   - *Kameras erkennen manchmal Schatten oder Lichtflackern als Wurf?* $\to$ Schwellwert leicht **erhöhen** (z. B. auf `32–38`).
   - *Dunkle Pfeile (schwarze Barrels/Flights) vor schwarzen Feldern werden übersehen?* $\to$ Schwellwert leicht **senken** (z. B. auf `18–22`).
3. **Min. Dart-Konturfläche (`Standard: 120 px²`):**
   - Filtert winziges Bildrauschen heraus. Wenn deine Kameras sehr weit weg vom Board montiert sind, kannst du den Wert auf `70–90` senken.
4. **Beruhigungszeit nach Wurf (`Standard: 260 ms`):**
   - So lange wartet das System nach dem Einschlag, bis der Pfeil ausgeschwungen hat, bevor die Spitze berechnet wird.
5. **Schnell-Korrektur im Spiel:**
   - Sollte ein Pfeil einmal verdeckt gewesen sein: Klicke im Scoreboard unten einfach auf den Slot **`1. Dart`**, **`2. Dart`** oder **`3. Dart`** (der Slot leuchtet gelb auf) und klicke danach rechts auf dem interaktiven Dartboard (oder im Zahlenfeld darunter) auf das richtige Feld!
