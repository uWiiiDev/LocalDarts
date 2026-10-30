/**
 * LocalDarts Frontend Application
 * Supports 1-6 players, 16 dart games with built-in instructions,
 * multi-language UI (DE / EN / FR), interactive SVG Dartboard, and 4-point calibration.
 */

const SECTORS = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];
const R_INNER_BULL = 6.35 / 170.0;
const R_OUTER_BULL = 15.9 / 170.0;
const R_TRIPLE_INNER = 97.4 / 170.0;
const R_TRIPLE_OUTER = 107.4 / 170.0;
const R_DOUBLE_INNER = 160.0 / 170.0;
const R_DOUBLE_OUTER = 1.0;

// --- Translations (DE / EN / FR) ---
const I18N = {
  de: {
    brand_sub: "Lokales 3-Kamera Autodarts System",
    tab_scoreboard: "🎯 Scoreboard & Board",
    tab_calibration: "📷 Kamera-Kalibrierung",
    tab_diagnostics: "🔬 Vision-Diagnose & Stats",
    tab_help: "❓ Hilfe & Anleitung",
    btn_new_game: "➕ Neues Spiel",
    btn_rules_info: "📖 Spielregeln",
    caller_on: "🔊 Caller: AN",
    caller_off: "🔇 Caller: AUS",
    round_word: "Runde",
    active_throw: "Am Wurf",
    cricket_overview: "🏏 Cricket Übersicht",
    ttt_overview: "❌⭕ Tic-Tac-Toe 3×3 Raster (3 Marks zum Erobern)",
    current_visit: "AKTUELLE AUFNAHME",
    click_slot_to_edit: "(Klicke einen Slot zum Korrigieren)",
    btn_undo: "↩️ Undo",
    btn_empty_board: "📷 Leeres Board",
    btn_next_player: "👋 Pfeile gezogen / Weiter",
    lbl_auto_takeout: "Auto-Takeout (Automatischer Spielerwechsel)",
    visit_total: "Aufnahme",
    ready_word: "Bereit",
    click_field_prompt: "Feld anklicken...",
    manual_word: "Manuell",
    live_cams_title: "📹 Live 3-Kamera Triangulation",
    live_cams_legend: "Grünes Gitter = Kalibrierung | Roter Kreis = Erkannte Spitze",
    interactive_board_title: "🎯 Interaktives Dartboard (Live-Treffer & Korrektur)",
    chk_sim_vision: "Klick = 3D-Kamerawurf simulieren",
    board_click_hint: "Klicke direkt in ein Feld auf dem Dartboard (oder nutze das Tastenfeld unten), um einen Wurf einzutragen oder einen markierten Slot zu korrigieren.",
    cal_sidebar_title: "📷 Kamera & Referenzpunkte",
    cal_select_slot: "Kamera-Slot auswählen",
    cal_video_source: "Video-Quelle (/dev/video* / DirectShow / Simulator)",
    btn_assign: "Zuweisen",
    btn_rescan_cams: "🔍 Alle 3 USB-Kameras neu suchen & automatisch zuweisen",
    cal_preset_label: "Kalibrierungs-Vorlage (4 Punkte auf Double-Außenring)",
    cal_click_4_pts: "Klicke diese 4 Punkte der Reihe nach im Kamerabild rechts an:",
    btn_save_cal: "💾 Kalibrierung speichern",
    btn_clear_pts: "🗑️ Punkte löschen",
    btn_demo_cal: "✨ Demo-/Simulations-Kalibrierung für alle 3 Kameras laden",
    cv_tuning_title: "⚙️ OpenCV Erkennungs-Feintuning",
    lbl_diff_thresh: "Differenz-Schwellwert",
    lbl_min_area: "Min. Dart-Konturfläche (px²)",
    lbl_settle_ms: "Beruhigungszeit nach Wurf (ms)",
    cal_cam_view_title: "1. Kamerabild – Klicke Punkt P1 bis P4",
    btn_refresh_frame: "🔄 Bild aktualisieren",
    cal_drag_hint: "Tipp: Klicke auf die 4 markierten Kreuzungspunkte am äußeren Draht des Double-Rings. Bereits gesetzte Punkte (P1–P4) kannst du mit der Maus ziehen!",
    cal_warped_title: "2. Entzerrte Draufsicht (Homographie-Prüfung)",
    cal_warped_hint: "Hier siehst du das mathematisch entzerrte Bild der Kamera. Wenn die Ringe deckungsgleich mit deinem echten Board sind, arbeitet die Erkennung millimetergenau.",
    diag_diff_title: "🔬 Live Differenz-Masken (Hintergrund-Subtraktion)",
    btn_recapture_bg: "📷 Referenzbild jetzt neu aufnehmen",
    diag_diff_desc: "Weiß = Veränderung gegenüber dem letzten ruhenden Zustand. Grün = Erkannte Dart-Kontur. Roter Kreis = Berechnete Pfeilspitze.",
    stats_summary_title: "📊 Trefferbild & Spieler-Statistiken",
    modal_new_game_title: "🎯 Neues Spiel starten",
    lbl_select_game_mode: "Spielmodus auswählen (16 Spiele)",
    lbl_start_points: "Ziel-/Start-Punkte",
    lbl_out_mode: "Check-Out Modus",
    lbl_in_mode: "Check-In Modus",
    lbl_legs_to_win: "Legs zum Sieg (First to)",
    lbl_cricket_variant: "Cricket-Variante",
    lbl_target_sector: "Zielsektor für Scoring 100",
    lbl_players_up_to_6: "Spieler (1 bis 6 Spieler)",
    btn_add_player: "➕ Spieler hinzufügen",
    btn_cancel: "Abbrechen",
    btn_start_game: "🚀 Spiel starten",
    guide_header: "📖 Spielanleitung",
    player_default_prefix: "Spieler",
    optgrp_classic: "🏆 Turnier & Klassiker",
    optgrp_party: "🎉 Party & Mehrspieler",
    optgrp_training: "🏋️ Profi- & Checkout-Training",
  },
  en: {
    brand_sub: "Local 3-Camera Autodarts System",
    tab_scoreboard: "🎯 Scoreboard & Board",
    tab_calibration: "📷 Camera Calibration",
    tab_diagnostics: "🔬 Vision Diagnostics & Stats",
    tab_help: "❓ Help & Manual",
    btn_new_game: "➕ New Game",
    btn_rules_info: "📖 Game Rules",
    caller_on: "🔊 Caller: ON",
    caller_off: "🔇 Caller: OFF",
    round_word: "Round",
    active_throw: "Throwing",
    cricket_overview: "🏏 Cricket Scoreboard",
    ttt_overview: "❌⭕ Tic-Tac-Toe 3×3 Grid (3 Marks to claim)",
    current_visit: "CURRENT VISIT",
    click_slot_to_edit: "(Click a slot to correct)",
    btn_undo: "↩️ Undo",
    btn_empty_board: "📷 Empty Board",
    btn_next_player: "👋 Takeout / Next Player",
    lbl_auto_takeout: "Auto-Takeout (Auto Next Player)",
    visit_total: "Turn",
    ready_word: "Ready",
    click_field_prompt: "Click sector...",
    manual_word: "Manual",
    live_cams_title: "📹 Live 3-Camera Triangulation",
    live_cams_legend: "Green spider = Calibration | Red circle = Detected tip",
    interactive_board_title: "🎯 Interactive Dartboard (Live Hits & Correction)",
    chk_sim_vision: "Click = Simulate 3D Camera Throw",
    board_click_hint: "Click any segment on the dartboard (or use the keypad below) to enter a throw or correct a selected slot.",
    cal_sidebar_title: "📷 Camera & Reference Points",
    cal_select_slot: "Select Camera Slot",
    cal_video_source: "Video Source (/dev/video* / DirectShow / Simulator)",
    btn_assign: "Assign",
    btn_rescan_cams: "🔍 Rescan & Auto-Assign All 3 USB Cameras",
    cal_preset_label: "Calibration Preset (4 Points on Outer Double Wire)",
    cal_click_4_pts: "Click these 4 points in order on the camera feed on the right:",
    btn_save_cal: "💾 Save Calibration",
    btn_clear_pts: "🗑️ Clear Points",
    btn_demo_cal: "✨ Load Demo/Simulation Calibration for all 3 Cameras",
    cv_tuning_title: "⚙️ OpenCV Detection Fine-Tuning",
    lbl_diff_thresh: "Difference Threshold",
    lbl_min_area: "Min. Dart Contour Area (px²)",
    lbl_settle_ms: "Settle Time after Throw (ms)",
    cal_cam_view_title: "1. Camera View – Click Points P1 to P4",
    btn_refresh_frame: "🔄 Refresh Frame",
    cal_drag_hint: "Tip: Click the 4 marked intersections on the outer Double ring wire. You can drag existing points (P1–P4) with your mouse!",
    cal_warped_title: "2. Rectified Top-Down View (Homography Check)",
    cal_warped_hint: "This shows the mathematically unwarped top-down view. When the drawn rings align with your physical board, detection is millimeter-accurate.",
    diag_diff_title: "🔬 Live Difference Masks (Background Subtraction)",
    btn_recapture_bg: "📷 Recapture Empty Board Reference",
    diag_diff_desc: "White = Pixel change vs. previous settled state. Green = Detected dart contour. Red circle = Triangulated dart tip.",
    stats_summary_title: "📊 Hit Dispersion & Player Statistics",
    modal_new_game_title: "🎯 Start New Game",
    lbl_select_game_mode: "Select Game Mode (16 Games)",
    lbl_start_points: "Target / Start Score",
    lbl_out_mode: "Check-Out Mode",
    lbl_in_mode: "Check-In Mode",
    lbl_legs_to_win: "Legs to Win (First to)",
    lbl_cricket_variant: "Cricket Variant",
    lbl_target_sector: "Target Sector for Scoring 100",
    lbl_players_up_to_6: "Players (1 to 6 Players)",
    btn_add_player: "➕ Add Player",
    btn_cancel: "Cancel",
    btn_start_game: "🚀 Start Game",
    guide_header: "📖 Game Instructions",
    player_default_prefix: "Player",
    optgrp_classic: "🏆 Tournament & Classics",
    optgrp_party: "🎉 Party & Multiplayer",
    optgrp_training: "🏋️ Pro & Checkout Training",
  },
  fr: {
    brand_sub: "Système Autodarts Local à 3 Caméras",
    tab_scoreboard: "🎯 Scoreboard & Cible",
    tab_calibration: "📷 Calibration Caméras",
    tab_diagnostics: "🔬 Diagnostic Vision & Stats",
    tab_help: "❓ Aide & Guide",
    btn_new_game: "➕ Nouvelle Partie",
    btn_rules_info: "📖 Règles du jeu",
    caller_on: "🔊 Annonceur: OUI",
    caller_off: "🔇 Annonceur: NON",
    round_word: "Tour",
    active_throw: "Au tir",
    cricket_overview: "🏏 Tableau Cricket",
    ttt_overview: "❌⭕ Grille Tic-Tac-Toe 3×3 (3 touches pour conquérir)",
    current_visit: "VOLÉE ACTUELLE",
    click_slot_to_edit: "(Cliquez sur une fléchette pour corriger)",
    btn_undo: "↩️ Annuler",
    btn_empty_board: "📷 Cible Vide",
    btn_next_player: "👋 Fléchettes retirées / Suivant",
    lbl_auto_takeout: "Auto-Takeout (Joueur suivant auto)",
    visit_total: "Volée",
    ready_word: "Prêt",
    click_field_prompt: "Cliquez la cible...",
    manual_word: "Manuel",
    live_cams_title: "📹 Triangulation 3 Caméras en Direct",
    live_cams_legend: "Grille verte = Calibration | Cercle rouge = Pointe détectée",
    interactive_board_title: "🎯 Cible Interactive (Impacts en direct & Correction)",
    chk_sim_vision: "Clic = Simuler lancer caméra 3D",
    board_click_hint: "Cliquez directement sur un secteur de la cible (ou utilisez le clavier ci-dessous) pour saisir un lancer ou corriger une fléchette.",
    cal_sidebar_title: "📷 Caméras & Points de Référence",
    cal_select_slot: "Choisir la Caméra",
    cal_video_source: "Source Vidéo (/dev/video* / DirectShow / Simulateur)",
    btn_assign: "Affecter",
    btn_rescan_cams: "🔍 Rechercher & Affecter les 3 Caméras USB",
    cal_preset_label: "Modèle de Calibration (4 points sur l'anneau Double extérieur)",
    cal_click_4_pts: "Cliquez sur ces 4 points dans l'ordre sur l'image de droite :",
    btn_save_cal: "💾 Enregistrer Calibration",
    btn_clear_pts: "🗑️ Effacer Points",
    btn_demo_cal: "✨ Charger Calibration Démo pour les 3 Caméras",
    cv_tuning_title: "⚙️ Réglage Détection OpenCV",
    lbl_diff_thresh: "Seuil de différence",
    lbl_min_area: "Surface min. du contour (px²)",
    lbl_settle_ms: "Temps de stabilisation (ms)",
    cal_cam_view_title: "1. Vue Caméra – Cliquez les points P1 à P4",
    btn_refresh_frame: "🔄 Actualiser l'image",
    cal_drag_hint: "Astuce : Cliquez sur les 4 intersections du fil extérieur Double. Vous pouvez déplacer les points (P1–P4) avec la souris !",
    cal_warped_title: "2. Vue de Dessus Redressée (Contrôle Homographie)",
    cal_warped_hint: "Voici l'image redressée mathématiquement. Si les anneaux correspondent exactement à votre cible réelle, la détection est précise au millimètre.",
    diag_diff_title: "🔬 Masques de Différence en Direct",
    btn_recapture_bg: "📷 Capturer l'image de référence maintenant",
    diag_diff_desc: "Blanc = Changement détecté. Vert = Contour de la fléchette. Cercle rouge = Pointe calculée.",
    stats_summary_title: "📊 Dispersion & Statistiques des Joueurs",
    modal_new_game_title: "🎯 Nouvelle Partie",
    lbl_select_game_mode: "Choisir le Mode de Jeu (16 Jeux)",
    lbl_start_points: "Points de départ / objectif",
    lbl_out_mode: "Mode de sortie (Check-Out)",
    lbl_in_mode: "Mode d'entrée (Check-In)",
    lbl_legs_to_win: "Manches gagnantes (First to)",
    lbl_cricket_variant: "Variante Cricket",
    lbl_target_sector: "Secteur cible pour Scoring 100",
    lbl_players_up_to_6: "Joueurs (1 à 6 Joueurs)",
    btn_add_player: "➕ Ajouter un joueur",
    btn_cancel: "Annuler",
    btn_start_game: "🚀 Lancer la partie",
    guide_header: "📖 Règles du jeu",
    player_default_prefix: "Joueur",
    optgrp_classic: "🏆 Tournoi & Classiques",
    optgrp_party: "🎉 Soirée & Multijoueur",
    optgrp_training: "🏋️ Entraînement Pro & Checkout",
  },
};

// --- Short Instructions for All 16 Games in DE / EN / FR ---
const GAME_GUIDES = {
  x01: {
    de: {
      title: "1. X01 (301 / 501 / 701 / 170)",
      desc: "Der offizielle Turnier-Klassiker: Jeder Spieler startet mit 301 oder 501 Punkten und zählt rückwärts auf exakt 0 herunter. Bei 'Double Out' muss der letzte Pfeil in einem Doppel-Feld (oder Double Bull) landen. Wirft man unter 0 oder auf Rest 1, ist die Aufnahme 'Bust' (ungültig).",
    },
    en: {
      title: "1. X01 (301 / 501 / 701 / 170)",
      desc: "The official tournament classic: Players start at 301 or 501 points and count down to exactly 0. In 'Double Out' mode, the winning dart must hit a Double segment (or Inner Bull). Scoring below 0 or leaving 1 results in a 'Bust'.",
    },
    fr: {
      title: "1. X01 (301 / 501 / 701 / 170)",
      desc: "Le classique officiel de tournoi : chaque joueur commence à 301 ou 501 points et descend jusqu'à exactement 0. En mode 'Double Out', la dernière fléchette doit atteindre un Double (ou Bull intérieur). Dépasser 0 annule la volée ('Bust').",
    },
  },
  cricket: {
    de: {
      title: "2. Cricket (Standard / Cut-Throat)",
      desc: "Gespielt wird auf die Zahlen 15 bis 20 sowie Bull. Mit 3 Treffern (Marks: Single=1, Double=2, Triple=3) schließt man ein Feld. Sobald man ein Feld geschlossen hat, bringen weitere Treffer darauf Punkte, solange mindestens ein Gegner dieses Feld noch offen hat. Bei 'Cut-Throat' erhalten die offenen Gegner Strafpunkte!",
    },
    en: {
      title: "2. Cricket (Standard / Cut-Throat)",
      desc: "Played on numbers 15 through 20 and Bull. Hit a number 3 times (Single=1, Double=2, Triple=3 marks) to close it. Once closed by you, extra hits score points as long as at least one opponent hasn't closed it yet. In 'Cut-Throat', points are added to open opponents!",
    },
    fr: {
      title: "2. Cricket (Standard / Cut-Throat)",
      desc: "Se joue sur les secteurs 15 à 20 et le Bull. 3 touches (Simple=1, Double=2, Triple=3) ferment un secteur. Une fois fermé, chaque touche supplémentaire rapporte des points tant qu'un adversaire ne l'a pas fermé. En 'Cut-Throat', les points sont donnés aux adversaires ouverts !",
    },
  },
  atc: {
    de: {
      title: "3. Around the Clock (Rund um die Uhr)",
      desc: "Treffe der Reihe nach alle Zahlen von 1 bis 20 und zum Abschluss das Bullseye. Erst wenn die aktuelle Zahl getroffen wurde, rückt das Ziel auf die nächste Zahl weiter. Wer zuerst das Bullseye trifft, gewinnt!",
    },
    en: {
      title: "3. Around the Clock",
      desc: "Hit every number in sequence from 1 up to 20, finishing on the Bullseye. You only advance to the next target number once you hit your current target. First player to hit the Bullseye wins!",
    },
    fr: {
      title: "3. Around the Clock (Tour d'Horloge)",
      desc: "Touchez dans l'ordre tous les numéros de 1 à 20 puis terminez par le Bullseye. Vous passez au numéro suivant dès que la cible actuelle est touchée.",
    },
  },
  shanghai: {
    de: {
      title: "4. Shanghai",
      desc: "In Runde 1 zählt nur die 1, in Runde 2 nur die 2 usw. (bis Runde 20). Es gewinnt, wer am Ende die meisten Punkte hat – ODER sofort durch ein 'Shanghai': Trifft ein Spieler innerhalb einer Aufnahme (3 Darts) je ein Single, Double UND Triple der aktuellen Rundenzahl, gewinnt er sofort!",
    },
    en: {
      title: "4. Shanghai",
      desc: "In Round 1 only sector 1 scores, in Round 2 only sector 2, up to Round 20. Highest total score wins — OR win instantly with a 'Shanghai': hitting a Single, Double, AND Triple of the round's number in a single 3-dart visit!",
    },
    fr: {
      title: "4. Shanghai",
      desc: "Au tour 1 seul le 1 compte, au tour 2 seul le 2, etc. Le meilleur score final gagne — OU victoire immédiate par 'Shanghai' en touchant un Simple, un Double ET un Triple du numéro du tour en une seule volée !",
    },
  },
  highscore: {
    de: {
      title: "5. Freies Training / Highscore",
      desc: "Alle Felder zählen! Versuche in 10 Runden (30 Darts) eine möglichst hohe Gesamtpunktzahl zu erreichen. Ideal zum Warmwerfen und für die Trefferbild-Analyse.",
    },
    en: {
      title: "5. Free Training / Highscore",
      desc: "All segments score! Try to achieve the highest total score possible across 10 rounds (30 darts). Great for warming up and analyzing your throw grouping.",
    },
    fr: {
      title: "5. Entraînement Libre / Highscore",
      desc: "Tous les secteurs comptent ! Marquez le maximum de points possibles en 10 tours (30 fléchettes). Idéal pour l'échauffement et l'analyse du groupement.",
    },
  },
  elimination: {
    de: {
      title: "6. Elimination (Mensch ärgere dich nicht)",
      desc: "Alle starten bei 0 und zählen hoch bis exakt 301 (oder 501). Der Clou: Landet ein Spieler mit seinem Wurf exakt auf der Punktzahl eines Mitspielers, wird dieser Mitspieler sofort wieder auf 0 zurückgesetzt!",
    },
    en: {
      title: "6. Elimination",
      desc: "Everyone starts at 0 and counts up to exactly 301 (or 501). The twist: if your score lands on the exact same score as an opponent, that opponent is knocked all the way back to 0!",
    },
    fr: {
      title: "6. Elimination",
      desc: "Tout le monde part de 0 et monte jusqu'à exactement 301 (ou 501). Si vous tombez exactement sur le score d'un adversaire, celui-ci retombe immédiatement à 0 !",
    },
  },
  killer: {
    de: {
      title: "7. Killer",
      desc: "Jeder Spieler erhält eine eigene Sektor-Zahl. Triff zuerst das Doppel/Triple deiner eigenen Zahl, um 3 Leben aufzubauen und zum 'KILLER' zu werden. Als Killer jagst du die anderen Spieler: Jeder Treffer auf deren Doppel (1) oder Triple (2) zieht ihnen Leben ab. Wer als Letzter übrig bleibt, gewinnt!",
    },
    en: {
      title: "7. Killer",
      desc: "Each player is assigned a unique number. First hit your own Double/Triple to build up 3 lives and become a 'KILLER'. Once a Killer, hit opponents' Doubles (1) or Triples (2) to take away their lives. Last survivor wins!",
    },
    fr: {
      title: "7. Killer",
      desc: "Chaque joueur reçoit un numéro. Touchez votre propre Double/Triple pour gagner 3 vies et devenir 'KILLER'. Ensuite, visez les Doubles/Triples adverses pour leur retirer des vies. Le dernier survivant gagne !",
    },
  },
  halve_it: {
    de: {
      title: "8. Halve It (Halbieren)",
      desc: "Über 8 Runden gibt es feste Vorgaben: 20 → 16 → Beliebiges Double → 14 → Beliebiges Triple → 18 → Mind. 41 Punkte → Bull. Jeder passende Treffer zählt Punkte. Aber Vorsicht: Wer in einer Runde mit allen 3 Darts das Ziel verfehlt, dessen Gesamtpunktzahl wird halbiert!",
    },
    en: {
      title: "8. Halve It",
      desc: "8 rounds with fixed targets: 20 → 16 → Any Double → 14 → Any Triple → 18 → At least 41 Points → Bull. Matching hits add to your score, but missing the target with all 3 darts cuts your total score in half!",
    },
    fr: {
      title: "8. Halve It (Diviser par deux)",
      desc: "8 tours avec objectifs fixes : 20 → 16 → Double au choix → 14 → Triple au choix → 18 → Min. 41 points → Bull. Si vous manquez l'objectif avec vos 3 fléchettes, votre score total est divisé par deux !",
    },
  },
  gotcha: {
    de: {
      title: "9. Gotcha",
      desc: "Actionreiche Variante bis 301: 1) Exakter Gleichstand setzt Gegner auf 0 zurück. 2) Wer überwirft (Bust), fällt auf den letzten Hunderter-Meilenstein (0, 100, 200) zurück. 3) Wer das rote Bullseye (50) trifft, tauscht sofort seinen Punktestand mit dem Führenden!",
    },
    en: {
      title: "9. Gotcha",
      desc: "Action-packed race to 301: 1) Matching an opponent's score resets them to 0. 2) Busting drops you back to the last 100-point milestone (0, 100, 200). 3) Hitting Inner Bull (50) swaps your score with the current leader!",
    },
    fr: {
      title: "9. Gotcha",
      desc: "Course dynamique vers 301 : 1) Égaler le score d'un adversaire le remet à 0. 2) Dépasser 301 vous ramène au palier de 100 inférieur (0, 100, 200). 3) Toucher le Bull intérieur (50) échange votre score avec le joueur en tête !",
    },
  },
  tictactoe: {
    de: {
      title: "10. Tic-Tac-Toe Darts",
      desc: "Auf einem 3×3-Spielfeld liegen 8 zufällige Zahlen und das Bullseye in der Mitte. Wer auf einem freien Feld zuerst 3 Marks (Single=1, Double=2, Triple=3) sammelt, besetzt dieses Feld. Wer zuerst 3 Felder in einer Reihe, Spalte oder Diagonale erobert, gewinnt!",
    },
    en: {
      title: "10. Tic-Tac-Toe Darts",
      desc: "A 3×3 grid of 8 random sectors with Bullseye in the center. Be the first to score 3 marks (Single=1, Double=2, Triple=3) on an unclaimed square to claim it. Get 3 in a row, column, or diagonal to win!",
    },
    fr: {
      title: "10. Tic-Tac-Toe Darts (Morpion)",
      desc: "Une grille 3×3 de 8 secteurs aléatoires avec le Bull au centre. Marquez 3 touches sur une case libre pour la conquérir. Alignez 3 cases (ligne, colonne ou diagonale) pour gagner !",
    },
  },
  bermuda: {
    de: {
      title: "11. Bermuda Triangle",
      desc: "13 feste Runden: 12 → 13 → 14 → Beliebiges Double → 15 → 16 → 17 → Beliebiges Triple → 18 → 19 → 20 → Single Bull (25) → Double Bull (50). Wer in einer Runde keinen einzigen gültigen Treffer landet, halbiert seine Punkte im Bermuda-Dreieck!",
    },
    en: {
      title: "11. Bermuda Triangle",
      desc: "13 fixed rounds: 12 → 13 → 14 → Any Double → 15 → 16 → 17 → Any Triple → 18 → 19 → 20 → Single Bull (25) → Double Bull (50). Failing to hit the target in a round halves your total score!",
    },
    fr: {
      title: "11. Triangle des Bermudes",
      desc: "13 tours fixes : 12 → 13 → 14 → Double → 15 → 16 → 17 → Triple → 18 → 19 → 20 → Simple Bull (25) → Double Bull (50). Une volée sans touche valide divise votre score par deux !",
    },
  },
  bobs27: {
    de: {
      title: "12. Bob's 27 (Doppel-Training)",
      desc: "Das berühmte Doppel-Training von Weltmeister Bob Anderson: Du startest mit 27 Punkten und wirfst pro Runde 3 Darts auf D1 bis D20 und DBull. Jeder Treffer bringt den Wert des Doppels plus – triffst du das Doppel mit keinem der 3 Darts, wird der Doppelwert abgezogen. Fällst du unter 0, ist das Spiel vorbei!",
    },
    en: {
      title: "12. Bob's 27 (Doubles Practice)",
      desc: "World Champion Bob Anderson's classic routine: Start with 27 points and throw 3 darts per round at D1 through D20 and DBull. Each hit adds the Double's value; 0 hits in a visit subtracts the Double's value. Drop below 0 and you're out!",
    },
    fr: {
      title: "12. Bob's 27 (Entraînement Doubles)",
      desc: "L'exercice légendaire de Bob Anderson : commencez avec 27 points et visez D1 à D20 puis DBull. Chaque touche ajoute la valeur du Double ; 0 touche dans la volée soustrait la valeur du Double. Tomber sous 0 élimine le joueur !",
    },
  },
  jdc_challenge: {
    de: {
      title: "13. JDC Challenge",
      desc: "Offizielles 19-Runden-Leistungstraining: Phase 1 (R1–6): Shanghai auf 10 bis 15 (+100 Bonus für S+D+T). Phase 2 (R7–13): Rund um die Welt auf alle Doppel D1 bis DBull (je 1 Dart pro Doppel = 50 Pkt, DBull = 100 Pkt). Phase 3 (R14–19): Shanghai auf 15 bis 20.",
    },
    en: {
      title: "13. JDC Challenge",
      desc: "Official 19-round routine: Phase 1 (R1–6): Shanghai on 10 to 15 (+100 bonus for S+D+T). Phase 2 (R7–13): Around the World on Doubles D1 to DBull (1 dart per Double = 50 pts, DBull = 100 pts). Phase 3 (R14–19): Shanghai on 15 to 20.",
    },
    fr: {
      title: "13. JDC Challenge",
      desc: "Programme officiel en 19 tours : Phase 1 (T1–6) : Shanghai sur 10 à 15 (+100 bonus S+D+T). Phase 2 (T7–13) : Doubles D1 à DBull (50 pts par Double, 100 pts DBull). Phase 3 (T14–19) : Shanghai sur 15 à 20.",
    },
  },
  catch40: {
    de: {
      title: "14. Catch 40 (Checkouts 61–100)",
      desc: "Du spielst alle Checkouts von 61 bis 100 durch und hast für jedes Ziel maximal 6 Darts (2 Aufnahmen) bei Double-Out. Checkout mit 2 Darts = 3 Punkte (bei 99 sogar 10 Punkte!), mit 3 Darts = 2 Punkte, mit 4–6 Darts = 1 Punkt.",
    },
    en: {
      title: "14. Catch 40 (Checkouts 61–100)",
      desc: "Attempt every Double-Out checkout from 61 up to 100 with up to 6 darts (2 visits) each. Checkout in 2 darts = 3 pts (10 pts on 99!), in 3 darts = 2 pts, in 4–6 darts = 1 pt.",
    },
    fr: {
      title: "14. Catch 40 (Checkouts 61–100)",
      desc: "Tentez tous les checkouts Double-Out de 61 à 100 avec 6 fléchettes max par cible. Réussite en 2 fléchettes = 3 pts (10 pts sur 99 !), en 3 fléchettes = 2 pts, en 4 à 6 fléchettes = 1 pt.",
    },
  },
  checkout121: {
    de: {
      title: "15. 121 Checkout-Leiter",
      desc: "Start bei 121 mit 9 Darts (3 Aufnahmen) zum Checken über Double-Out. Schaffst du das Finish innerhalb von 9 Darts, steigt dein nächstes Ziel um +1 (122, 123, ...). Schaffst du es nicht, geht es 1 Stufe zurück (bis min. 121).",
    },
    en: {
      title: "15. 121 Checkout Ladder",
      desc: "Start at 121 with 9 darts (3 visits) to check out via Double-Out. Succeed within 9 darts and the target climbs by +1 (122, 123, ...); fail and it steps back down (minimum 121).",
    },
    fr: {
      title: "15. Échelle Checkout 121",
      desc: "Commencez à 121 avec 9 fléchettes (3 volées) pour finir en Double-Out. En cas de réussite, la cible augmente de +1 (122, 123...) ; sinon elle recule d'un point (minimum 121).",
    },
  },
  scoring100: {
    de: {
      title: "16. Bulls-Eye / Scoring 100",
      desc: "Ausdauer- & Präzisionstraining mit 99 Darts (33 Aufnahmen) auf deinen gewählten Zielsektor (20, 19, 18 oder Bullseye). Jeder Single-Treffer zählt 1 Mark, Double 2 Marks, Triple 3 Marks.",
    },
    en: {
      title: "16. Bulls-Eye / Scoring 100",
      desc: "Precision & endurance drill throwing 99 darts (33 visits) at your chosen target sector (20, 19, 18, or Bullseye). Single = 1 mark, Double = 2 marks, Triple = 3 marks.",
    },
    fr: {
      title: "16. Bulls-Eye / Scoring 100",
      desc: "Exercice de précision de 99 fléchettes (33 volées) sur votre secteur cible (20, 19, 18 ou Bullseye). Simple = 1 touche, Double = 2 touches, Triple = 3 touches.",
    },
  },
};

let appState = {
  lang: localStorage.getItem("localdarts_lang") || "de",
  game: null,
  cameras: null,
  calibration: null,
  detector: null,
  selectedEditSlot: null,
  selectedKeypadMult: 1,
  callerEnabled: true,
  activeTab: "tab-scoreboard",
  playerNamesDraft: ["Spieler 1", "Spieler 2"],
  // Calibration state
  calCamId: 0,
  calPresetId: "autodarts_wires_ccw",
  calPoints: [],
  draggingPointIdx: null,
  calBgImage: new Image(),
};

function t(key) {
  const dict = I18N[appState.lang] || I18N.de;
  return dict[key] || I18N.de[key] || key;
}

function applyLanguageToDOM() {
  document.documentElement.lang = appState.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key) el.textContent = t(key);
  });

  // Update optgroup labels
  const ogClassic = document.getElementById("optgrp-classic");
  const ogParty = document.getElementById("optgrp-party");
  const ogTrain = document.getElementById("optgrp-training");
  if (ogClassic) ogClassic.label = t("optgrp_classic");
  if (ogParty) ogParty.label = t("optgrp_party");
  if (ogTrain) ogTrain.label = t("optgrp_training");

  // Update option titles in #ng-mode
  const modeSelect = document.getElementById("ng-mode");
  if (modeSelect) {
    Array.from(modeSelect.options).forEach((opt) => {
      const g = GAME_GUIDES[opt.value];
      if (g && g[appState.lang]) {
        opt.textContent = g[appState.lang].title;
      }
    });
  }

  // Update Caller button label
  const btnCaller = document.getElementById("btn-toggle-caller");
  if (btnCaller) {
    btnCaller.textContent = appState.callerEnabled ? t("caller_on") : t("caller_off");
  }

  updateGameGuideBox();
  renderGameUI();
}

function updateGameGuideBox() {
  const modeSelect = document.getElementById("ng-mode");
  const selectedMode = modeSelect ? modeSelect.value : "x01";
  const guide = (GAME_GUIDES[selectedMode] && GAME_GUIDES[selectedMode][appState.lang]) || GAME_GUIDES.x01.de;

  const titleEl = document.getElementById("ng-guide-title");
  const textEl = document.getElementById("ng-guide-text");
  if (titleEl && textEl) {
    titleEl.textContent = `${t("guide_header")}: ${guide.title}`;
    textEl.textContent = guide.desc;
  }

  // Also update active game rules box on Scoreboard
  const activeMode = appState.game ? appState.game.mode : selectedMode;
  const activeGuide = (GAME_GUIDES[activeMode] && GAME_GUIDES[activeMode][appState.lang]) || guide;
  const sbTitle = document.getElementById("scoreboard-rules-title");
  const sbText = document.getElementById("scoreboard-rules-text");
  if (sbTitle && sbText) {
    sbTitle.textContent = `${t("guide_header")}: ${activeGuide.title}`;
    sbText.textContent = activeGuide.desc;
  }
}

// --- 1 to 6 Players Input Management ---
function renderPlayerInputs() {
  const container = document.getElementById("ng-players-grid");
  const addBtn = document.getElementById("btn-add-player");
  if (!container) return;

  container.innerHTML = "";
  appState.playerNamesDraft.forEach((name, idx) => {
    const row = document.createElement("div");
    row.className = "player-input-row";
    row.innerHTML = `
      <span class="player-badge-num">${idx + 1}</span>
      <input type="text" class="form-control player-name-input" data-idx="${idx}" value="${name}" maxlength="22" style="padding: 0.42rem 0.65rem;" />
      ${
        appState.playerNamesDraft.length > 1
          ? `<button type="button" class="btn btn-danger btn-sm btn-remove-player" data-idx="${idx}" style="padding: 0.35rem 0.55rem;">✕</button>`
          : ""
      }
    `;
    container.appendChild(row);
  });

  container.querySelectorAll(".player-name-input").forEach((inp) => {
    inp.addEventListener("input", (ev) => {
      const i = parseInt(ev.target.dataset.idx, 10);
      appState.playerNamesDraft[i] = ev.target.value;
    });
  });

  container.querySelectorAll(".btn-remove-player").forEach((btn) => {
    btn.addEventListener("click", (ev) => {
      const i = parseInt(ev.currentTarget.dataset.idx, 10);
      if (appState.playerNamesDraft.length > 1) {
        appState.playerNamesDraft.splice(i, 1);
        renderPlayerInputs();
      }
    });
  });

  if (addBtn) {
    addBtn.disabled = appState.playerNamesDraft.length >= 6;
  }
}

// --- Sound & Voice Caller ---
const audioCtx = typeof window.AudioContext !== "undefined" ? new window.AudioContext() : null;

function playDartSound(type = "hit") {
  if (!appState.callerEnabled || !audioCtx) return;
  try {
    if (audioCtx.state === "suspended") audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;
    if (type === "180") {
      osc.type = "triangle";
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.setValueAtTime(554.37, now + 0.12);
      osc.frequency.setValueAtTime(659.25, now + 0.24);
      gain.gain.setValueAtTime(0.22, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.65);
      osc.start(now);
      osc.stop(now + 0.65);
    } else {
      osc.type = "sine";
      osc.frequency.setValueAtTime(165, now);
      osc.frequency.exponentialRampToValueAtTime(55, now + 0.09);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);
      osc.start(now);
      osc.stop(now + 0.09);
    }
  } catch (_) {}
}

function speakCaller(text) {
  if (!appState.callerEnabled || !text || typeof window.speechSynthesis === "undefined") return;
  try {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    const langMap = { de: "de-DE", en: "en-GB", fr: "fr-FR" };
    utter.lang = langMap[appState.lang] || "en-GB";
    utter.rate = 1.02;
    utter.pitch = 0.92;
    window.speechSynthesis.speak(utter);
  } catch (_) {}
}

// --- SVG Geometry Helpers ---
function polarToXY(rNorm, angleDegCwFromTop) {
  const rad = (angleDegCwFromTop * Math.PI) / 180.0;
  return {
    x: rNorm * 100.0 * Math.sin(rad),
    y: -rNorm * 100.0 * Math.cos(rad),
  };
}

function createWedgePath(rIn, rOut, startDeg, endDeg) {
  const p1 = polarToXY(rIn, startDeg);
  const p2 = polarToXY(rOut, startDeg);
  const p3 = polarToXY(rOut, endDeg);
  const p4 = polarToXY(rIn, endDeg);
  const rInSvg = rIn * 100.0;
  const rOutSvg = rOut * 100.0;
  return [
    `M ${p1.x.toFixed(2)} ${p1.y.toFixed(2)}`,
    `L ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`,
    `A ${rOutSvg.toFixed(2)} ${rOutSvg.toFixed(2)} 0 0 1 ${p3.x.toFixed(2)} ${p3.y.toFixed(2)}`,
    `L ${p4.x.toFixed(2)} ${p4.y.toFixed(2)}`,
    `A ${rInSvg.toFixed(2)} ${rInSvg.toFixed(2)} 0 0 0 ${p1.x.toFixed(2)} ${p1.y.toFixed(2)}`,
    "Z",
  ].join(" ");
}

function buildInteractiveDartboardSVG(svgEl, isGuideOnly = false) {
  svgEl.innerHTML = "";
  const ns = "http://www.w3.org/2000/svg";

  const surround = document.createElementNS(ns, "circle");
  surround.setAttribute("cx", "0");
  surround.setAttribute("cy", "0");
  surround.setAttribute("r", "122");
  surround.setAttribute("fill", "#101622");
  surround.setAttribute("stroke", "#273552");
  surround.setAttribute("stroke-width", "2");
  svgEl.appendChild(surround);

  SECTORS.forEach((num, idx) => {
    const startDeg = idx * 18.0 - 9.0;
    const endDeg = startDeg + 18.0;
    const isDark = idx % 2 === 0;
    const singleFill = isDark ? "#14181f" : "#e5dec9";
    const ringFill = isDark ? "#d92b2b" : "#169c46";

    const rings = [
      { rIn: R_OUTER_BULL, rOut: R_TRIPLE_INNER, fill: singleFill },
      { rIn: R_TRIPLE_INNER, rOut: R_TRIPLE_OUTER, fill: ringFill },
      { rIn: R_TRIPLE_OUTER, rOut: R_DOUBLE_INNER, fill: singleFill },
      { rIn: R_DOUBLE_INNER, rOut: R_DOUBLE_OUTER, fill: ringFill },
    ];

    rings.forEach((rg) => {
      const path = document.createElementNS(ns, "path");
      path.setAttribute("d", createWedgePath(rg.rIn, rg.rOut, startDeg, endDeg));
      path.setAttribute("fill", rg.fill);
      path.setAttribute("stroke", "#a8b3c2");
      path.setAttribute("stroke-width", "0.45");
      svgEl.appendChild(path);
    });

    const lblPos = polarToXY(1.11, idx * 18.0);
    const txt = document.createElementNS(ns, "text");
    txt.setAttribute("x", lblPos.x.toFixed(2));
    txt.setAttribute("y", (lblPos.y + 3.2).toFixed(2));
    txt.setAttribute("text-anchor", "middle");
    txt.setAttribute("fill", "#e2e8f0");
    txt.setAttribute("font-size", "9.5");
    txt.setAttribute("font-weight", "800");
    txt.textContent = String(num);
    svgEl.appendChild(txt);
  });

  const sBull = document.createElementNS(ns, "circle");
  sBull.setAttribute("cx", "0");
  sBull.setAttribute("cy", "0");
  sBull.setAttribute("r", (R_OUTER_BULL * 100.0).toFixed(2));
  sBull.setAttribute("fill", "#169c46");
  sBull.setAttribute("stroke", "#cbd5e1");
  sBull.setAttribute("stroke-width", "0.55");
  svgEl.appendChild(sBull);

  const dBull = document.createElementNS(ns, "circle");
  dBull.setAttribute("cx", "0");
  dBull.setAttribute("cy", "0");
  dBull.setAttribute("r", (R_INNER_BULL * 100.0).toFixed(2));
  dBull.setAttribute("fill", "#d92b2b");
  dBull.setAttribute("stroke", "#cbd5e1");
  dBull.setAttribute("stroke-width", "0.55");
  svgEl.appendChild(dBull);

  const overlayGroup = document.createElementNS(ns, "g");
  overlayGroup.setAttribute("id", isGuideOnly ? "cal-guide-overlay" : "dart-hits-overlay");
  svgEl.appendChild(overlayGroup);

  if (!isGuideOnly) {
    svgEl.addEventListener("click", (ev) => {
      const pt = svgEl.createSVGPoint();
      pt.x = ev.clientX;
      pt.y = ev.clientY;
      const svgP = pt.matrixTransform(svgEl.getScreenCTM().inverse());
      const bx = svgP.x / 100.0;
      const by = svgP.y / 100.0;
      handleBoardClick(bx, by);
    });
  }
}

function renderDartMarkersOnSVG() {
  const overlay = document.getElementById("dart-hits-overlay");
  if (!overlay || !appState.game) return;
  overlay.innerHTML = "";
  const ns = "http://www.w3.org/2000/svg";

  const activePlayer = appState.game.players[appState.game.current_player_idx];
  if (activePlayer && activePlayer.hit_history) {
    activePlayer.hit_history.forEach((h) => {
      const dot = document.createElementNS(ns, "circle");
      dot.setAttribute("cx", (h.x * 100.0).toFixed(2));
      dot.setAttribute("cy", (h.y * 100.0).toFixed(2));
      dot.setAttribute("r", "1.6");
      dot.setAttribute("fill", "rgba(56, 189, 248, 0.45)");
      overlay.appendChild(dot);
    });
  }

  (appState.game.turn_darts || []).forEach((d, idx) => {
    const cx = d.x * 100.0;
    const cy = d.y * 100.0;

    const pulse = document.createElementNS(ns, "circle");
    pulse.setAttribute("cx", cx.toFixed(2));
    pulse.setAttribute("cy", cy.toFixed(2));
    pulse.setAttribute("r", "5.5");
    pulse.setAttribute("fill", "rgba(0, 212, 138, 0.28)");
    pulse.setAttribute("stroke", "#00f09c");
    pulse.setAttribute("stroke-width", "1.2");
    overlay.appendChild(pulse);

    const pin = document.createElementNS(ns, "circle");
    pin.setAttribute("cx", cx.toFixed(2));
    pin.setAttribute("cy", cy.toFixed(2));
    pin.setAttribute("r", "2.3");
    pin.setAttribute("fill", "#ffffff");
    overlay.appendChild(pin);

    const lbl = document.createElementNS(ns, "text");
    lbl.setAttribute("x", (cx + 6.5).toFixed(2));
    lbl.setAttribute("y", (cy - 4.0).toFixed(2));
    lbl.setAttribute("fill", "#00f09c");
    lbl.setAttribute("font-size", "7.5");
    lbl.setAttribute("font-weight", "900");
    lbl.textContent = `D${idx + 1}:${d.label}`;
    overlay.appendChild(lbl);
  });
}

async function handleBoardClick(bx, by) {
  if (appState.selectedEditSlot !== null) {
    const slotIdx = appState.selectedEditSlot;
    appState.selectedEditSlot = null;
    updateTurnSlotsUI();
    await fetch("/api/game/correct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dart_index: slotIdx, x: bx, y: by }),
    });
    return;
  }

  const viaVision = document.getElementById("chk-throw-via-vision").checked;
  await fetch("/api/game/throw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ x: bx, y: by, via_vision: viaVision }),
  });
}

async function handleKeypadClick(sector, multiplier) {
  if (appState.selectedEditSlot !== null) {
    const slotIdx = appState.selectedEditSlot;
    appState.selectedEditSlot = null;
    updateTurnSlotsUI();
    await fetch("/api/game/correct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dart_index: slotIdx, sector, multiplier }),
    });
    return;
  }

  const viaVision = document.getElementById("chk-throw-via-vision").checked;
  await fetch("/api/game/throw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sector, multiplier, via_vision: viaVision }),
  });
}

function buildManualKeypad() {
  const container = document.getElementById("keypad-numbers");
  container.innerHTML = "";
  for (let n = 1; n <= 20; n++) {
    const btn = document.createElement("button");
    btn.className = "num-btn";
    btn.textContent = String(n);
    btn.addEventListener("click", () => handleKeypadClick(n, appState.selectedKeypadMult));
    container.appendChild(btn);
  }
  const btn25 = document.createElement("button");
  btn25.className = "num-btn";
  btn25.style.color = "#4ade80";
  btn25.textContent = "25";
  btn25.addEventListener("click", () => handleKeypadClick(25, 1));
  container.appendChild(btn25);

  const btnBull = document.createElement("button");
  btnBull.className = "num-btn";
  btnBull.style.color = "#f87171";
  btnBull.textContent = "BULL";
  btnBull.addEventListener("click", () => handleKeypadClick(25, 2));
  container.appendChild(btnBull);

  const btnMiss = document.createElement("button");
  btnMiss.className = "num-btn";
  btnMiss.style.color = "#94a3b8";
  btnMiss.textContent = "MISS";
  btnMiss.addEventListener("click", () => handleKeypadClick(0, 0));
  container.appendChild(btnMiss);

  document.querySelectorAll(".mult-btn").forEach((b) => {
    b.addEventListener("click", () => {
      document.querySelectorAll(".mult-btn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      appState.selectedKeypadMult = parseInt(b.dataset.mult, 10);
    });
  });
}

// --- Scoreboard UI Rendering (1 to 6 Players) ---
function renderGameUI() {
  const g = appState.game;
  if (!g) return;

  document.getElementById("announcement-text").textContent = g.last_announcement || "";
  document.getElementById("round-badge").textContent = `${g.mode_title || g.mode.toUpperCase()} • ${t("round_word")} ${g.round_number}`;
  document.getElementById("btn-undo").disabled = !g.can_undo;
  updateGameGuideBox();

  const pContainer = document.getElementById("players-container");
  pContainer.innerHTML = "";
  pContainer.classList.toggle("many-players", g.players.length >= 4);

  g.players.forEach((p, idx) => {
    const isCurrent = idx === g.current_player_idx && !g.winner_name;
    const card = document.createElement("div");
    card.className = `player-card ${isCurrent ? "active" : ""}`;

    let checkoutHtml = "";
    if (p.target_badge) {
      checkoutHtml += `<span class="checkout-dart" style="background:rgba(56,189,248,0.18);border-color:rgba(56,189,248,0.45);color:#7dd3fc;">${p.target_badge}</span>`;
    }
    if (p.checkout_guide && p.checkout_guide.length > 0) {
      checkoutHtml += `<span class="checkout-label">CO:</span>` +
        p.checkout_guide.map((c) => `<span class="checkout-dart">${c}</span>`).join("");
    }

    card.innerHTML = `
      <div class="player-header">
        <div class="player-name">
          <span>${p.name}</span>
          ${isCurrent ? `<span class="active-throw-badge">${t("active_throw")}</span>` : ""}
        </div>
        ${g.mode === "x01" ? `<span class="legs-pill">Legs: <strong>${p.legs_won}</strong>/${g.legs_to_win}</span>` : ""}
      </div>
      <div class="player-score">${p.score}</div>
      <div class="checkout-row" style="flex-wrap:wrap;">${checkoutHtml}</div>
      <div class="player-stats">
        <span>Ø 3-Dart: <strong>${p.three_dart_avg.toFixed(1)}</strong></span>
        <span>First-9: <strong>${p.first9_avg.toFixed(1)}</strong></span>
        <span>Darts: <strong>${p.darts_thrown_leg}</strong></span>
        ${g.mode === "x01" ? `<span>CO: <strong>${p.checkout_hits}/${p.checkout_attempts}</strong></span>` : ""}
        <span>180s: <strong>${p.count_180}</strong></span>
      </div>
    `;
    pContainer.appendChild(card);
  });

  // Cricket Table
  const cricketWrap = document.getElementById("cricket-board-wrap");
  if (g.mode === "cricket") {
    cricketWrap.style.display = "block";
    const hdr = document.getElementById("cricket-header-row");
    hdr.innerHTML = "<th>#</th>" + g.players.map((p) => `<th>${p.name}</th>`).join("");
    const body = document.getElementById("cricket-body");
    body.innerHTML = "";
    [20, 19, 18, 17, 16, 15, 25].forEach((num) => {
      const tr = document.createElement("tr");
      const lbl = num === 25 ? "BULL" : String(num);
      const cells = g.players.map((p) => {
        const m = (p.cricket_marks && p.cricket_marks[String(num)]) || 0;
        const sym = m === 0 ? "·" : m === 1 ? "/" : m === 2 ? "✕" : "⊗";
        return `<td class="cricket-mark ${m >= 3 ? "closed" : ""}">${sym}</td>`;
      }).join("");
      tr.innerHTML = `<td><strong>${lbl}</strong></td>${cells}`;
      body.appendChild(tr);
    });
  } else {
    cricketWrap.style.display = "none";
  }

  // Tic-Tac-Toe 3x3 Board (up to 6 player symbols)
  const tttWrap = document.getElementById("tictactoe-board-wrap");
  if (g.mode === "tictactoe" && g.tictactoe_board) {
    tttWrap.style.display = "block";
    const tttGrid = document.getElementById("tictactoe-grid");
    tttGrid.innerHTML = "";
    const symbols = ["❌", "⭕", "🔺", "⭐", "💎", "⚡"];
    g.tictactoe_board.forEach((cell) => {
      const div = document.createElement("div");
      const claimed = cell.owner_idx !== null && cell.owner_idx !== undefined;
      div.style.background = claimed ? "rgba(0, 212, 138, 0.16)" : "var(--bg-input)";
      div.style.border = `2px solid ${claimed ? "var(--accent)" : "var(--border-col)"}`;
      div.style.borderRadius = "10px";
      div.style.padding = "0.7rem";
      div.style.textAlign = "center";

      let subInfo = "";
      if (claimed) {
        subInfo = `<div style="font-size:0.82rem;font-weight:800;color:var(--accent);margin-top:0.2rem;">${symbols[cell.owner_idx % 6]} ${cell.owner_name}</div>`;
      } else {
        const marksParts = g.players.map((p, pidx) => {
          const m = (cell.marks && cell.marks[String(pidx)]) || 0;
          return `${p.name}: ${m}/3`;
        });
        subInfo = `<div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.2rem;">${marksParts.join(" | ")}</div>`;
      }

      div.innerHTML = `
        <div style="font-size:1.35rem;font-weight:900;color:#fff;">${cell.label}</div>
        ${subInfo}
      `;
      tttGrid.appendChild(div);
    });
  } else if (tttWrap) {
    tttWrap.style.display = "none";
  }

  updateTurnSlotsUI();
  renderDartMarkersOnSVG();
  renderStatsSummaryCards();
}

function updateTurnSlotsUI() {
  const g = appState.game;
  if (!g) return;
  const darts = g.turn_darts || [];
  for (let i = 0; i < 3; i++) {
    const slotEl = document.querySelector(`.dart-slot[data-slot="${i}"]`);
    const valEl = document.getElementById(`slot-val-${i}`);
    const subEl = document.getElementById(`slot-sub-${i}`);
    slotEl.classList.toggle("selected-for-edit", appState.selectedEditSlot === i);
    if (i < darts.length) {
      const d = darts[i];
      slotEl.classList.add("filled");
      valEl.textContent = d.label;
      subEl.textContent = `${d.score} (${d.source === "camera" ? `${d.cameras_used} Cam` : t("manual_word")})`;
    } else {
      slotEl.classList.remove("filled");
      valEl.textContent = "–";
      subEl.textContent = appState.selectedEditSlot === i ? t("click_field_prompt") : t("ready_word");
    }
  }
  document.getElementById("turn-total-val").textContent = g.turn_busted ? "BUST" : String(g.turn_score || 0);
}

function renderVisionStatusUI() {
  const d = appState.detector;
  if (!d) return;
  const dot = document.getElementById("vision-dot");
  const txt = document.getElementById("vision-status-text");
  dot.className = "status-dot";
  if (d.state === "MOTION" || d.state === "SETTLING") dot.classList.add("motion");
  if (d.state === "TAKEOUT") dot.classList.add("takeout");
  txt.textContent = `VISION: ${d.state} (${d.darts_in_board}/3)`;

  document.getElementById("rng-diff-thresh").value = d.diff_threshold;
  document.getElementById("lbl-diff-thresh").textContent = d.diff_threshold;
  document.getElementById("rng-min-area").value = d.min_contour_area;
  document.getElementById("lbl-min-area").textContent = d.min_contour_area;
  document.getElementById("rng-settle-ms").value = d.settle_time_ms;
  document.getElementById("lbl-settle-ms").textContent = d.settle_time_ms;
}

// --- Calibration Tab Logic ---
function populateCalibrationControls() {
  if (!appState.cameras || !appState.calibration) return;

  const devSelect = document.getElementById("cal-device-select");
  const currentSlot = appState.cameras.slots[appState.calCamId];
  devSelect.innerHTML = `<option value="-1">Simulations-Kamera (3D-Board)</option>`;
  (appState.cameras.available_devices || []).forEach((dev) => {
    const opt = document.createElement("option");
    opt.value = String(dev.index);
    opt.textContent = dev.name;
    devSelect.appendChild(opt);
  });
  if (currentSlot) {
    devSelect.value = String(currentSlot.device_index ?? -1);
  }

  for (let i = 0; i < 3; i++) {
    const st = appState.cameras.slots[i];
    const cal = appState.calibration.cameras[i];
    const badge = document.getElementById(`mini-cam-status-${i}`);
    if (badge && st && cal) {
      badge.textContent = `${st.mode === "usb" ? `USB #${st.device_index}` : "Sim"} • ${cal.is_calibrated ? "OK ✓" : "–"}`;
    }
  }

  const presetSelect = document.getElementById("cal-preset-select");
  presetSelect.innerHTML = "";
  Object.values(appState.calibration.presets).forEach((pr) => {
    const opt = document.createElement("option");
    opt.value = pr.id;
    opt.textContent = pr.name;
    presetSelect.appendChild(opt);
  });

  const camCal = appState.calibration.cameras[appState.calCamId];
  if (camCal) {
    appState.calPresetId = camCal.preset_id;
    presetSelect.value = camCal.preset_id;
    appState.calPoints = (camCal.image_points_norm || []).map((p) => [p[0], p[1]]);
  }

  renderCalibrationStepsAndGuide();
  refreshCalibrationSnapshot();
}

function renderCalibrationStepsAndGuide() {
  if (!appState.calibration) return;
  const preset = appState.calibration.presets[appState.calPresetId];
  if (!preset) return;

  const listEl = document.getElementById("cal-steps-list");
  listEl.innerHTML = "";
  const colors = ["#ff5050", "#ffdc00", "#00ff66", "#38bdf8"];

  preset.points.forEach((pt, idx) => {
    const isDone = idx < appState.calPoints.length;
    const isNext = idx === appState.calPoints.length;
    const li = document.createElement("li");
    li.className = `point-step-item ${isNext ? "active-step" : ""} ${isDone ? "done-step" : ""}`;
    li.innerHTML = `
      <span style="display:flex;align-items:center;gap:0.4rem;">
        <span style="width:10px;height:10px;border-radius:50%;background:${colors[idx]};display:inline-block;"></span>
        ${pt.label}
      </span>
      <span>${isDone ? "✅" : isNext ? "👉" : "·"}</span>
    `;
    listEl.appendChild(li);
  });

  const guideOverlay = document.getElementById("cal-guide-overlay");
  if (!guideOverlay) return;
  guideOverlay.innerHTML = "";
  const ns = "http://www.w3.org/2000/svg";

  preset.points.forEach((pt, idx) => {
    const cx = pt.xy[0] * 100.0;
    const cy = pt.xy[1] * 100.0;
    const isNext = idx === appState.calPoints.length;

    const circle = document.createElementNS(ns, "circle");
    circle.setAttribute("cx", cx.toFixed(2));
    circle.setAttribute("cy", cy.toFixed(2));
    circle.setAttribute("r", isNext ? "8.5" : "5.5");
    circle.setAttribute("fill", colors[idx]);
    circle.setAttribute("stroke", "#ffffff");
    circle.setAttribute("stroke-width", isNext ? "2.5" : "1.2");
    guideOverlay.appendChild(circle);

    const txt = document.createElementNS(ns, "text");
    txt.setAttribute("x", (cx * 0.78).toFixed(2));
    txt.setAttribute("y", (cy * 0.78 + 3).toFixed(2));
    txt.setAttribute("text-anchor", "middle");
    txt.setAttribute("fill", "#ffffff");
    txt.setAttribute("font-size", "11");
    txt.setAttribute("font-weight", "900");
    txt.textContent = `P${idx + 1}`;
    guideOverlay.appendChild(txt);
  });
}

function refreshCalibrationSnapshot() {
  const cid = appState.calCamId;
  const ts = Date.now();
  appState.calBgImage.onload = () => {
    drawCalibrationCanvas();
  };
  appState.calBgImage.src = `/api/stream/camera/${cid}?view=annotated&snapshot=1&t=${ts}`;
  document.getElementById("cal-warped-preview").src = `/api/stream/camera/${cid}?view=warped&snapshot=1&t=${ts}`;
}

function drawCalibrationCanvas() {
  const canvas = document.getElementById("calibration-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (appState.calBgImage.complete && appState.calBgImage.naturalWidth > 0) {
    ctx.drawImage(appState.calBgImage, 0, 0, canvas.width, canvas.height);
  }

  const colors = ["#ff5050", "#ffdc00", "#00ff66", "#38bdf8"];
  appState.calPoints.forEach((pt, idx) => {
    const px = pt[0] * canvas.width;
    const py = pt[1] * canvas.height;
    ctx.beginPath();
    ctx.arc(px, py, 9, 0, Math.PI * 2);
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = colors[idx];
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(px, py, 3, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();

    ctx.font = "bold 14px sans-serif";
    ctx.fillStyle = colors[idx];
    ctx.fillText(`P${idx + 1}`, px + 12, py - 8);
  });
}

function setupCalibrationCanvasEvents() {
  const canvas = document.getElementById("calibration-canvas");
  const getNormCoords = (ev) => {
    const rect = canvas.getBoundingClientRect();
    const u = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
    const v = Math.max(0, Math.min(1, (ev.clientY - rect.top) / rect.height));
    return [u, v];
  };

  canvas.addEventListener("mousedown", (ev) => {
    const [u, v] = getNormCoords(ev);
    for (let i = 0; i < appState.calPoints.length; i++) {
      const dist = Math.hypot(appState.calPoints[i][0] - u, appState.calPoints[i][1] - v);
      if (dist < 0.035) {
        appState.draggingPointIdx = i;
        return;
      }
    }
    if (appState.calPoints.length < 4) {
      appState.calPoints.push([u, v]);
      renderCalibrationStepsAndGuide();
      drawCalibrationCanvas();
      if (appState.calPoints.length === 4) {
        saveCurrentCalibration();
      }
    }
  });

  canvas.addEventListener("mousemove", (ev) => {
    if (appState.draggingPointIdx === null) return;
    const [u, v] = getNormCoords(ev);
    appState.calPoints[appState.draggingPointIdx] = [u, v];
    drawCalibrationCanvas();
  });

  window.addEventListener("mouseup", () => {
    if (appState.draggingPointIdx !== null) {
      appState.draggingPointIdx = null;
      if (appState.calPoints.length === 4) {
        saveCurrentCalibration();
      }
    }
  });
}

async function saveCurrentCalibration() {
  if (appState.calPoints.length !== 4) return;
  const res = await fetch("/api/calibration/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cam_id: appState.calCamId,
      preset_id: appState.calPresetId,
      points: appState.calPoints,
    }),
  });
  const data = await res.json();
  appState.calibration = data.calibration;
  renderCalibrationStepsAndGuide();
  refreshCalibrationSnapshot();
}

function renderStatsSummaryCards() {
  const container = document.getElementById("stats-summary-cards");
  if (!container || !appState.game) return;
  container.innerHTML = "";
  appState.game.players.forEach((p) => {
    const box = document.createElement("div");
    box.style.background = "var(--bg-input)";
    box.style.border = "1px solid var(--border-col)";
    box.style.borderRadius = "10px";
    box.style.padding = "0.85rem";
    box.innerHTML = `
      <div style="font-weight:800;font-size:1rem;margin-bottom:0.45rem;color:var(--accent);">${p.name}</div>
      <div style="font-size:0.82rem;line-height:1.65;color:var(--text-muted);">
        3-Dart Average: <strong style="color:#fff;">${p.three_dart_avg.toFixed(2)}</strong><br/>
        First-9 Average: <strong style="color:#fff;">${p.first9_avg.toFixed(2)}</strong><br/>
        Checkout: <strong style="color:#fff;">${p.checkout_pct}% (${p.checkout_hits}/${p.checkout_attempts})</strong><br/>
        60+ / 100+ / 140+ / 180: <strong style="color:#fff;">${p.count_60_plus} / ${p.count_100_plus} / ${p.count_140_plus} / ${p.count_180}</strong>
      </div>
    `;
    container.appendChild(box);
  });
}

function startCameraPreviewLoop() {
  setInterval(() => {
    const ts = Date.now();
    if (appState.activeTab === "tab-scoreboard") {
      for (let i = 0; i < 3; i++) {
        const img = document.getElementById(`mini-cam-img-${i}`);
        if (img) img.src = `/api/stream/camera/${i}?view=annotated&snapshot=1&t=${ts}`;
      }
    } else if (appState.activeTab === "tab-diagnostics") {
      for (let i = 0; i < 3; i++) {
        const img = document.getElementById(`diag-diff-${i}`);
        if (img) img.src = `/api/stream/camera/${i}?view=diff&snapshot=1&t=${ts}`;
      }
    }
  }, 240);
}

// --- WebSocket Connection ---
function connectWebSocket() {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${window.location.host}/ws`);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.cameras) appState.cameras = msg.cameras;
    if (msg.calibration) appState.calibration = msg.calibration;
    if (msg.detector) {
      appState.detector = msg.detector;
      renderVisionStatusUI();
    }
    if (msg.game) {
      const prevSpeech = appState.game ? appState.game.last_caller_speech : "";
      appState.game = msg.game;
      renderGameUI();
      if (msg.event === "dart_detected") {
        const turnSum = msg.game.turn_score;
        playDartSound(turnSum === 180 ? "180" : "hit");
        if (msg.game.last_caller_speech) speakCaller(msg.game.last_caller_speech);
      } else if (msg.event === "takeout_detected" && msg.game.last_caller_speech !== prevSpeech) {
        speakCaller(msg.game.last_caller_speech);
      }
    }
    if (msg.event === "init" || msg.event === "cameras_update" || msg.event === "calibration_update") {
      populateCalibrationControls();
    }
  };

  ws.onclose = () => {
    setTimeout(connectWebSocket, 1500);
  };
}

// --- Event Listeners Setup ---
document.addEventListener("DOMContentLoaded", () => {
  buildInteractiveDartboardSVG(document.getElementById("interactive-dartboard"), false);
  buildInteractiveDartboardSVG(document.getElementById("cal-guide-svg"), true);
  buildManualKeypad();
  setupCalibrationCanvasEvents();

  // Language switcher
  const langSelect = document.getElementById("lang-select");
  langSelect.value = appState.lang;
  langSelect.addEventListener("change", (ev) => {
    appState.lang = ev.target.value;
    localStorage.setItem("localdarts_lang", appState.lang);
    applyLanguageToDOM();
  });

  renderPlayerInputs();
  applyLanguageToDOM();
  connectWebSocket();
  startCameraPreviewLoop();

  // Scoreboard collapsible rules info button
  document.getElementById("btn-toggle-rules-banner").addEventListener("click", () => {
    const box = document.getElementById("scoreboard-rules-box");
    box.style.display = box.style.display === "none" ? "block" : "none";
  });

  // Add player button (up to 6 players)
  document.getElementById("btn-add-player").addEventListener("click", () => {
    if (appState.playerNamesDraft.length < 6) {
      const nextNum = appState.playerNamesDraft.length + 1;
      appState.playerNamesDraft.push(`${t("player_default_prefix")} ${nextNum}`);
      renderPlayerInputs();
    }
  });

  // Tab navigation
  document.querySelectorAll(".nav-tab").forEach((tabBtn) => {
    tabBtn.addEventListener("click", () => {
      document.querySelectorAll(".nav-tab").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      tabBtn.classList.add("active");
      const targetId = tabBtn.dataset.tab;
      appState.activeTab = targetId;
      document.getElementById(targetId).classList.add("active");
      if (targetId === "tab-calibration") {
        populateCalibrationControls();
      }
    });
  });

  // Caller toggle
  const btnCaller = document.getElementById("btn-toggle-caller");
  btnCaller.addEventListener("click", () => {
    appState.callerEnabled = !appState.callerEnabled;
    btnCaller.textContent = appState.callerEnabled ? t("caller_on") : t("caller_off");
  });

  // Turn slots click-to-edit
  document.querySelectorAll(".dart-slot").forEach((slotEl) => {
    slotEl.addEventListener("click", () => {
      const idx = parseInt(slotEl.dataset.slot, 10);
      const dartsLen = (appState.game?.turn_darts || []).length;
      if (idx >= dartsLen) return;
      appState.selectedEditSlot = appState.selectedEditSlot === idx ? null : idx;
      updateTurnSlotsUI();
    });
  });

  const chkTakeout = document.getElementById("chk-auto-takeout");
  if (chkTakeout) {
    chkTakeout.addEventListener("change", (ev) => {
      fetch("/api/detector/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ auto_takeout_enabled: ev.target.checked }),
      });
    });
  }

  document.getElementById("btn-undo").addEventListener("click", () => {
    fetch("/api/game/undo", { method: "POST" });
  });

  document.getElementById("btn-reset-bg").addEventListener("click", () => {
    fetch("/api/detector/reset_reference", { method: "POST" });
  });

  document.getElementById("btn-diag-reset-bg").addEventListener("click", () => {
    fetch("/api/detector/reset_reference", { method: "POST" });
  });

  document.getElementById("btn-next-player").addEventListener("click", () => {
    fetch("/api/game/next", { method: "POST" });
  });

  // Calibration controls
  document.getElementById("cal-cam-select").addEventListener("change", (ev) => {
    appState.calCamId = parseInt(ev.target.value, 10);
    populateCalibrationControls();
  });

  document.getElementById("btn-assign-device").addEventListener("click", async () => {
    const devIdx = parseInt(document.getElementById("cal-device-select").value, 10);
    await fetch("/api/cameras/assign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slot_id: appState.calCamId, device_index: devIdx }),
    });
    setTimeout(refreshCalibrationSnapshot, 250);
  });

  document.getElementById("btn-rescan-cameras").addEventListener("click", async () => {
    await fetch("/api/cameras/rescan", { method: "POST" });
    setTimeout(() => {
      populateCalibrationControls();
      refreshCalibrationSnapshot();
    }, 450);
  });

  const fpsSelect = document.getElementById("cal-fps-select");
  if (fpsSelect) {
    fpsSelect.addEventListener("change", async (ev) => {
      const target_fps = parseInt(ev.target.value, 10) || 20;
      await fetch("/api/cameras/fps", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_fps }),
      });
      setTimeout(refreshCalibrationSnapshot, 300);
    });
  }

  document.getElementById("cal-preset-select").addEventListener("change", (ev) => {
    appState.calPresetId = ev.target.value;
    renderCalibrationStepsAndGuide();
  });

  document.getElementById("btn-save-cal").addEventListener("click", saveCurrentCalibration);

  document.getElementById("btn-clear-cal-pts").addEventListener("click", async () => {
    appState.calPoints = [];
    await fetch(`/api/calibration/reset/${appState.calCamId}`, { method: "POST" });
    renderCalibrationStepsAndGuide();
    refreshCalibrationSnapshot();
  });

  document.getElementById("btn-auto-sim-cal").addEventListener("click", async () => {
    await fetch("/api/calibration/auto_sim/-1", { method: "POST" });
    populateCalibrationControls();
  });

  document.getElementById("btn-refresh-cal-frame").addEventListener("click", refreshCalibrationSnapshot);

  // Detector sliders
  const sendDetectorSettings = () => {
    const diff_threshold = parseInt(document.getElementById("rng-diff-thresh").value, 10);
    const min_contour_area = parseInt(document.getElementById("rng-min-area").value, 10);
    const settle_time_ms = parseInt(document.getElementById("rng-settle-ms").value, 10);
    document.getElementById("lbl-diff-thresh").textContent = diff_threshold;
    document.getElementById("lbl-min-area").textContent = min_contour_area;
    document.getElementById("lbl-settle-ms").textContent = settle_time_ms;
    fetch("/api/detector/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ diff_threshold, min_contour_area, settle_time_ms }),
    });
  };
  document.getElementById("rng-diff-thresh").addEventListener("change", sendDetectorSettings);
  document.getElementById("rng-min-area").addEventListener("change", sendDetectorSettings);
  document.getElementById("rng-settle-ms").addEventListener("change", sendDetectorSettings);

  // New Game Modal
  const modal = document.getElementById("modal-newgame");
  const openModal = () => {
    updateGameGuideBox();
    renderPlayerInputs();
    modal.classList.add("open");
  };
  const closeModal = () => modal.classList.remove("open");

  document.getElementById("btn-open-newgame").addEventListener("click", openModal);
  document.getElementById("btn-close-newgame").addEventListener("click", closeModal);
  document.getElementById("btn-cancel-newgame").addEventListener("click", closeModal);

  document.getElementById("ng-mode").addEventListener("change", (ev) => {
    const m = ev.target.value;
    document.getElementById("ng-x01-options").style.display = ["x01", "elimination", "gotcha"].includes(m) ? "block" : "none";
    document.getElementById("ng-cricket-options").style.display = m === "cricket" ? "block" : "none";
    document.getElementById("ng-scoring100-options").style.display = m === "scoring100" ? "block" : "none";
    updateGameGuideBox();
  });

  document.getElementById("btn-start-newgame").addEventListener("click", async () => {
    const mode = document.getElementById("ng-mode").value;
    const x01_start_score = parseInt(document.getElementById("ng-start-score").value, 10);
    const out_mode = document.getElementById("ng-out-mode").value;
    const double_in = document.getElementById("ng-double-in").value === "1";
    const legs_to_win = parseInt(document.getElementById("ng-legs").value, 10) || 3;
    const cricket_variant = document.getElementById("ng-cricket-variant").value;
    const training_target_sector = parseInt(document.getElementById("ng-target-sector").value, 10) || 20;
    const player_names = appState.playerNamesDraft.map((s) => s.trim()).filter(Boolean).slice(0, 6);

    await fetch("/api/game/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode,
        player_names: player_names.length ? player_names : ["Spieler 1"],
        x01_start_score,
        double_in,
        out_mode,
        legs_to_win,
        cricket_variant,
        training_target_sector,
      }),
    });
    closeModal();
  });
});
