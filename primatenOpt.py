#!/usr/bin/env python3
"""
Primaten – erweiterte Kultursimulation mit GUI
Eine agentenbasierte Simulation zur Erforschung kultureller Dynamiken in Primatengruppen
Optimierte Version mit 5 Erweiterungen:
1. Kulturelle Hybridisierung
2. Macht-Puffer für Kulturwechsel
3. Weibliche Affinität bei Partnerwahl
4. Ressourcen-System
5. Kulturelle Toleranz
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import random
from datetime import datetime
import csv
from PIL import Image, ImageTk, ImageDraw
import threading
import time

class Primat:
    """Klasse für einen einzelnen Primaten mit erweiterten Eigenschaften"""
    def __init__(self, status=0, alter=0, geschlecht=0, kultur=0, kultur2=0, macht=0):
        self.status = status      # 0=kein Primat, 1=jung, 2=erwachsen
        self.alter = alter        # in Ticks
        self.geschlecht = geschlecht  # 1=weiblich, 2=männlich
        self.kultur = kultur      # Primärkultur (1-9)
        self.kultur2 = kultur2    # Sekundärkultur - NEU: Hybridisierung
        self.macht = macht        # Sozialer Einfluss (1-9)

class PrimatenSimulation:
    """Hauptklasse für die Primaten-Simulation mit 5 Erweiterungen"""
    
    def __init__(self, breite=40, hoehe=40, initial_dichte=0.1):
        self.breite = breite
        self.hoehe = hoehe
        self.raum = np.empty((hoehe, breite), dtype=object)
        self.ressourcen = np.zeros((hoehe, breite), dtype=int)  # NEU: Ressourcen-Ebene
        self.tick_index = 0
        self.history = []
        self.max_history = 5000
        self.kultur_farben = [
            None, '#e6194B', '#3cb44b', '#ffe119', '#4363d8', 
            '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c'
        ]
        # NEU: Kulturelle Toleranz-Werte
        self.kultur_toleranz = [None, 0.2, 0.8, 0.4, 0.9, 0.5, 0.1, 0.7, 0.3, 0.6]
        
        self.initialisiere_raum(initial_dichte)
        self.initialisiere_ressourcen()  # NEU: Ressourcen initialisieren
        
    def initialisiere_ressourcen(self):
        """Initialisiert die Ressourcen-Ebene"""
        for y in range(self.hoehe):
            for x in range(self.breite):
                self.ressourcen[y][x] = random.randint(0, 5)  # 0-5 Ressourcen pro Zelle
        
    def initialisiere_raum(self, dichte=0.1):
        """Initialisiert den Raum mit zufällig verteilten Primaten"""
        for y in range(self.hoehe):
            for x in range(self.breite):
                if random.random() < dichte:
                    # Zufällige Eigenschaften für neuen Primaten
                    geschlecht = 1 if random.random() < 0.5 else 2
                    kultur = random.randint(1, 9)
                    kultur2 = random.randint(1, 9)  # NEU: Sekundärkultur
                    macht = random.randint(1, 9)
                    self.raum[y][x] = Primat(1, 0, geschlecht, kultur, kultur2, macht)
                else:
                    self.raum[y][x] = Primat()
        
        self.tick_index = 0
        self.history = []
        self.berechne_statistik()
    
    def nachbarn(self, x, y):
        """Gibt die 8 Nachbarn einer Position zurück (toroidale Geometrie)"""
        nachbarn_pos = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.breite
                ny = (y + dy) % self.hoehe
                nachbarn_pos.append((self.raum[ny][nx], nx, ny))
        return nachbarn_pos
    
    def kulturelle_naehe(self, p1, p2):
        """NEU: Berechnet kulturelle Ähnlichkeit zwischen zwei Primaten"""
        if (p1.kultur == p2.kultur or p1.kultur == p2.kultur2 or 
            p1.kultur2 == p2.kultur or p1.kultur2 == p2.kultur2):
            return 1
        return 0
    
    def kind_erzeugen(self, mutter, vater):
        """NEU: Erweitert - Kind erbt Primärkultur von Mutter, Sekundärkultur von Vater"""
        geschlecht = 1 if random.random() < 0.5 else 2
        return Primat(1, 0, geschlecht, mutter.kultur, vater.kultur, vater.macht)
    
    def get_nachbar_ressourcen(self, x, y):
        """NEU: Berechnet lokale Ressourcen-Konzentration"""
        sum_r = self.ressourcen[y][x]
        nachbarn = self.nachbarn(x, y)
        for nb, nx, ny in nachbarn:
            sum_r += self.ressourcen[ny][nx]
        return min(10, sum_r // 5)  # Normiert auf 0-10
    
    def check_isolation(self, primat, x, y):
        """NEU: Prüft kulturelle Isolation unter Berücksichtigung der Toleranz"""
        if primat.status <= 0 or primat.kultur <= 0:
            return False
        
        nachbarn = self.nachbarn(x, y)
        fremde_nachbarn = 0
        
        for nb, nx, ny in nachbarn:
            if nb.status > 0 and nb.kultur > 0:
                if not self.kulturelle_naehe(primat, nb):
                    fremde_nachbarn += 1
        
        isolationsgrad = fremde_nachbarn / 8.0
        toleranz = self.kultur_toleranz[primat.kultur]
        sterbewahrscheinlichkeit = isolationsgrad * (1 - toleranz)
        
        return random.random() < sterbewahrscheinlichkeit
    
    def neue_generation(self, x, y):
        """Berechnet den neuen Zustand für eine Position mit allen 5 Erweiterungen"""
        aktuell = self.raum[y][x]
        nachbarn = self.nachbarn(x, y)
        nachbarn_primaten = [nb for nb, nx, ny in nachbarn]
        
        # Kopie des aktuellen Zustands
        neu = Primat(aktuell.status, aktuell.alter, aktuell.geschlecht, 
                    aktuell.kultur, aktuell.kultur2, aktuell.macht)
        
        # NEU: Ressourcen-Verbrauch und Regeneration
        if neu.status > 0 and self.ressourcen[y][x] > 0:
            self.ressourcen[y][x] -= 1
        else:
            self.ressourcen[y][x] = min(5, self.ressourcen[y][x] + 1)
        
        # Alterungsprozess
        if neu.status > 0:
            if random.random() < 0.8:
                neu.alter += 1
            if neu.alter > 19:
                neu.status = 0  # Tod
            elif neu.alter >= 3 and neu.status == 1:
                neu.status = 2  # Erwachsen werden
        
        # NEU: Kulturelle Isolation (Tod durch fehlende Toleranz)
        if neu.status > 0 and self.check_isolation(neu, x, y):
            return Primat()
        
        # Geburt neuer Primaten
        if neu.status == 0:
            weibchen = [p for p in nachbarn_primaten if p.status == 2 and p.geschlecht == 1]
            maennchen = [p for p in nachbarn_primaten if p.status == 2 and p.geschlecht == 2]
            
            # NEU: Weibliche Affinität bei Partnerwahl
            if weibchen and maennchen and random.random() < 0.25:
                # Finde bestes Paar basierend auf Macht und kultureller Nähe
                bestes_paar = None
                bester_score = -1
                
                for w in weibchen:
                    for m in maennchen:
                        affinitaet = self.kulturelle_naehe(w, m)
                        score = 0.8 * m.macht + 0.2 * affinitaet * 9
                        if score > bester_score:
                            bester_score = score
                            bestes_paar = (w, m)
                
                if bestes_paar:
                    return self.kind_erzeugen(bestes_paar[0], bestes_paar[1])
            
            # Spontane Entstehung (Migration)
            if random.random() < 0.0005:
                geschlecht = 1 if random.random() < 0.5 else 2
                kultur = random.randint(1, 9)
                kultur2 = random.randint(1, 9)
                macht = random.randint(1, 9)
                return Primat(1, 0, geschlecht, kultur, kultur2, macht)
        
        # Kulturelle Beeinflussung (nur erwachsene Männchen)
        if neu.status == 2 and neu.geschlecht == 2:
            # NEU: Ressourcen-Bonus für Machtgewinn
            res_bonus = self.get_nachbar_ressourcen(x, y) / 10.0
            
            staerkere = [p for p in nachbarn_primaten 
                        if p.status == 2 and p.geschlecht == 2 and p.macht > neu.macht]
            
            if staerkere:
                einflussreichster = max(staerkere, key=lambda p: p.macht)
                
                # NEU: Macht-Puffer - nur bei großem Unterschied
                if einflussreichster.macht > neu.macht + 3 and random.random() < 0.3:
                    neu.kultur = einflussreichster.kultur
                    neu.kultur2 = einflussreichster.kultur2
                    neu.macht = max(1, neu.macht - 1)
            else:
                # NEU: Machtgewinn durch Ressourcen
                neu.macht = min(9, neu.macht + 0.1 + res_bonus * 0.2)
        
        return neu
    
    def tick(self):
        """Führt einen Simulationsschritt durch"""
        neuer_raum = np.empty((self.hoehe, self.breite), dtype=object)
        
        for y in range(self.hoehe):
            for x in range(self.breite):
                neuer_raum[y][x] = self.neue_generation(x, y)
        
        self.raum = neuer_raum
        self.tick_index += 1
        return self.berechne_statistik()
    
    def berechne_statistik(self):
        """Berechnet Statistiken über die aktuelle Population"""
        kultur_zaehler = [0] * 9
        gesamt_population = 0
        
        for y in range(self.hoehe):
            for x in range(self.breite):
                p = self.raum[y][x]
                if p.status > 0 and p.kultur > 0:
                    # Zähle Primärkultur
                    kultur_zaehler[p.kultur - 1] += 1
                    # NEU: Zähle Sekundärkultur wenn verschieden
                    if p.kultur2 > 0 and p.kultur2 != p.kultur:
                        kultur_zaehler[p.kultur2 - 1] += 1
                    gesamt_population += 1
        
        # Anteile berechnen (kann jetzt >1 sein wegen doppelter Zählung)
        sum_kulturen = sum(kultur_zaehler)
        anteile = [count / sum_kulturen if sum_kulturen > 0 else 0 
                  for count in kultur_zaehler]
        
        # Zur Historie hinzufügen
        datenpunkt = {
            'tick': self.tick_index,
            'population': gesamt_population,
            'anteile': anteile.copy(),
            'kultur_counts': kultur_zaehler.copy()
        }
        
        self.history.append(datenpunkt)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        return anteile, gesamt_population
    
    def monokultur_erkannt(self, anteile, population):
        """Prüft, ob eine Monokultur erreicht wurde"""
        if population < 10:
            return False, None
        
        max_anteil = max(anteile)
        if max_anteil >= 0.995:
            dominante_kultur = anteile.index(max_anteil) + 1
            return True, dominante_kultur
        
        return False, None
    
    def export_csv(self, dateiname=None):
        """Exportiert die Simulationsdaten als CSV"""
        if not dateiname:
            zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
            dateiname = f"kulturverlauf_{zeitstempel}.csv"
        
        with open(dateiname, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Header schreiben
            header = ['tick', 'population'] + [f'kultur_{i+1}' for i in range(9)]
            writer.writerow(header)
            
            # Daten schreiben
            for eintrag in self.history:
                zeile = [eintrag['tick'], eintrag['population']]
                zeile.extend([f"{a:.5f}" for a in eintrag['anteile']])
                writer.writerow(zeile)
        
        return dateiname

class PrimatenGUI:
    """Grafische Benutzeroberfläche für die Primaten-Simulation"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Primaten – erweiterte Kultursimulation (Optimiert)")
        self.root.geometry("1200x800")
        
        # Simulation initialisieren
        self.simulation = PrimatenSimulation(40, 40, 0.1)
        self.laufend = False
        self.tick_intervall = 150  # ms
        
        # GUI-Elemente erstellen
        self.erste_gui()
        self.aktualisiere_anzeige()
        
    def erste_gui(self):
        """Erstellt die grafische Benutzeroberfläche"""
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguration der Grid-Gewichtung
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Steuerungsbereich oben
        control_frame = ttk.LabelFrame(main_frame, text="Simulationssteuerung", padding="5")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(btn_frame, text="🔀 Zufallsverteilung", 
                  command=self.zufallsverteilung).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(btn_frame, text="▶ Start", 
                  command=self.start_simulation, style="Accent.TButton").grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="⏸ Stopp", 
                  command=self.stopp_simulation).grid(row=0, column=2, padx=5)
        
        # Einstellungen
        settings_frame = ttk.Frame(control_frame)
        settings_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.auto_stopp_var = tk.BooleanVar()
        ttk.Checkbutton(settings_frame, text="Auto-Stopp bei Monokultur", 
                       variable=self.auto_stopp_var).grid(row=0, column=0, padx=5)
        
        self.zeige_population_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Population anzeigen", 
                       variable=self.zeige_population_var).grid(row=0, column=1, padx=5)
        
        # Geschwindigkeits-Steuerung
        speed_frame = ttk.Frame(control_frame)
        speed_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(speed_frame, text="Geschwindigkeit:").grid(row=0, column=0, padx=(0, 5))
        self.speed_var = tk.StringVar(value="150")
        speed_combo = ttk.Combobox(speed_frame, textvariable=self.speed_var, 
                                  values=["50", "100", "150", "250", "400"], 
                                  state="readonly", width=8)
        speed_combo.grid(row=0, column=1, padx=5)
        speed_combo.bind('<<ComboboxSelected>>', self.geschwindigkeit_aendern)
        
        # Statistik-Anzeige
        stats_frame = ttk.Frame(control_frame)
        stats_frame.grid(row=1, column=2, sticky=tk.E)
        
        self.stats_label = ttk.Label(stats_frame, 
                                   text="Tick: 0 | Population: 0 | Dominante Kultur: -")
        self.stats_label.grid(row=0, column=0)
        
        # Hauptanzeige-Bereich
        display_frame = ttk.Frame(main_frame)
        display_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
        # Linke Seite: Visualisierungen
        left_frame = ttk.Frame(display_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # Status-Anzeige
        status_frame = ttk.LabelFrame(left_frame, text="Status (Geschlecht & Alter)")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        self.status_canvas = tk.Canvas(status_frame, width=320, height=320, bg="black")
        self.status_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Kultur-Anzeige
        kultur_frame = ttk.LabelFrame(left_frame, text="Kulturverteilung")
        kultur_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        kultur_frame.columnconfigure(0, weight=1)
        kultur_frame.rowconfigure(0, weight=1)
        
        self.kultur_canvas = tk.Canvas(kultur_frame, width=320, height=320, bg="black")
        self.kultur_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Rechte Seite: Diagramm und Legende
        right_frame = ttk.Frame(display_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=3)
        right_frame.rowconfigure(1, weight=1)
        
        # Diagramm
        diagramm_frame = ttk.LabelFrame(right_frame, text="Kulturentwicklung")
        diagramm_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        diagramm_frame.columnconfigure(0, weight=1)
        diagramm_frame.rowconfigure(0, weight=1)
        
        self.diagramm_canvas = tk.Canvas(diagramm_frame, width=400, height=300, bg="black")
        self.diagramm_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Legende und Export
        bottom_right_frame = ttk.Frame(right_frame)
        bottom_right_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        bottom_right_frame.columnconfigure(0, weight=1)
        bottom_right_frame.rowconfigure(0, weight=1)
        bottom_right_frame.rowconfigure(1, weight=0)
        
        # Legende
        legende_frame = ttk.LabelFrame(bottom_right_frame, text="Legende")
        legende_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status-Legende
        status_legende_frame = ttk.Frame(legende_frame)
        status_legende_frame.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(status_legende_frame, text="Status:").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        farben_status = [
            ("weiblich, jung", "#ffb6c1"),
            ("männlich, jung", "#87cefa"), 
            ("weiblich, erwachsen", "#ff69b4"),
            ("männlich, erwachsen", "#1e90ff")
        ]
        
        for i, (text, farbe) in enumerate(farben_status):
            canvas = tk.Canvas(status_legende_frame, width=15, height=15, bg=farbe, highlightthickness=1)
            canvas.grid(row=i+1, column=0, padx=(0, 5), pady=2)
            ttk.Label(status_legende_frame, text=text).grid(row=i+1, column=1, sticky=tk.W, pady=2)
        
        # Kultur-Legende
        kultur_legende_frame = ttk.Frame(legende_frame)
        kultur_legende_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(kultur_legende_frame, text="Kulturen:").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        for i in range(1, 10):
            row = (i-1) // 3 + 1
            col = (i-1) % 3
            farbe = self.simulation.kultur_farben[i]
            canvas = tk.Canvas(kultur_legende_frame, width=15, height=15, bg=farbe, highlightthickness=1)
            canvas.grid(row=row, column=col*2, padx=(5, 2), pady=2)
            ttk.Label(kultur_legende_frame, text=str(i)).grid(row=row, column=col*2+1, sticky=tk.W, pady=2)
        
        # Export-Buttons
        export_frame = ttk.Frame(bottom_right_frame)
        export_frame.grid(row=1, column=0, sticky=tk.E, pady=(5, 0))
        
        ttk.Button(export_frame, text="💾 CSV Export", 
                  command=self.export_csv).grid(row=0, column=0, padx=5)
        ttk.Button(export_frame, text="🖼 PNG Export", 
                  command=self.export_png).grid(row=0, column=1, padx=5)
    
    def zeichne_status(self):
        """Zeichnet die Status-Ansicht mit Ressourcen-Hintergrund"""
        canvas = self.status_canvas
        canvas.delete("all")
        
        breite = canvas.winfo_width()
        hoehe = canvas.winfo_height()
        zell_groesse = min(breite // self.simulation.breite, hoehe // self.simulation.hoehe)
        
        # NEU: Ressourcen als Hintergrund zeichnen
        for y in range(self.simulation.hoehe):
            for x in range(self.simulation.breite):
                ress = self.simulation.ressourcen[y][x] / 5.0  # 0-1 normalisiert
                gruen_wert = int(ress * 120)
                farbe = f"#00{gruen_wert:02x}00"
                x1 = x * zell_groesse
                y1 = y * zell_groesse
                x2 = x1 + zell_groesse
                y2 = y1 + zell_groesse
                canvas.create_rectangle(x1, y1, x2, y2, fill=farbe, outline="")
        
        farb_map = {
            (1, 1): "#ffb6c1",  # weiblich, jung
            (1, 2): "#87cefa",  # männlich, jung
            (2, 1): "#ff69b4",  # weiblich, erwachsen
            (2, 2): "#1e90ff"   # männlich, erwachsen
        }
        
        for y in range(self.simulation.hoehe):
            for x in range(self.simulation.breite):
                p = self.simulation.raum[y][x]
                if p.status > 0:
                    farbe = farb_map.get((p.status, p.geschlecht), "white")
                    x1 = x * zell_groesse
                    y1 = y * zell_groesse
                    x2 = x1 + zell_groesse
                    y2 = y1 + zell_groesse
                    canvas.create_rectangle(x1, y1, x2, y2, fill=farbe, outline="")
    
    def zeichne_kultur(self):
        """Zeichnet die Kultur-Ansicht"""
        canvas = self.kultur_canvas
        canvas.delete("all")
        
        breite = canvas.winfo_width()
        hoehe = canvas.winfo_height()
        zell_groesse = min(breite // self.simulation.breite, hoehe // self.simulation.hoehe)
        
        for y in range(self.simulation.hoehe):
            for x in range(self.simulation.breite):
                p = self.simulation.raum[y][x]
                if p.kultur > 0:
                    farbe = self.simulation.kultur_farben[p.kultur]
                    x1 = x * zell_groesse
                    y1 = y * zell_groesse
                    x2 = x1 + zell_groesse
                    y2 = y1 + zell_groesse
                    canvas.create_rectangle(x1, y1, x2, y2, fill=farbe, outline="")
    
    def zeichne_diagramm(self):
        """Zeichnet das Entwicklungsdiagramm"""
        canvas = self.diagramm_canvas
        canvas.delete("all")
        
        if len(self.simulation.history) < 2:
            return
        
        breite = canvas.winfo_width()
        hoehe = canvas.winfo_height()
        padding = 40
        
        # Fenstergröße für Diagramm
        fenster = min(len(self.simulation.history), 600)
        start_index = max(0, len(self.simulation.history) - fenster)
        daten = self.simulation.history[start_index:]
        
        if len(daten) < 2:
            return
        
        # Koordinaten berechnen
        ticks = [d['tick'] for d in daten]
        min_tick = min(ticks)
        max_tick = max(ticks)
        
        # Raster zeichnen
        canvas.create_rectangle(padding, padding, breite-padding, hoehe-padding, 
                               outline="#666666", fill="black")
        
        # Y-Achse beschriften
        for i in range(6):
            y = padding + i * (hoehe - 2*padding) / 5
            wert = 1.0 - i * 0.2
            canvas.create_text(padding - 10, y, text=f"{wert:.1f}", 
                              fill="white", anchor="e", font=("Arial", 8))
            canvas.create_line(padding, y, breite-padding, y, fill="#333333")
        
        # X-Achse beschriften
        tick_step = max(1, (max_tick - min_tick) // 5)
        for i in range(0, len(daten), max(1, len(daten)//5)):
            if i < len(daten):
                x = padding + i * (breite - 2*padding) / len(daten)
                canvas.create_text(x, hoehe - padding + 15, text=str(daten[i]['tick']), 
                                  fill="white", anchor="n", font=("Arial", 8))
        
        # Kulturlinien zeichnen
        for k in range(9):
            farbe = self.simulation.kultur_farben[k + 1]
            punkte = []
            
            for i, datenpunkt in enumerate(daten):
                x = padding + i * (breite - 2*padding) / len(daten)
                y = hoehe - padding - datenpunkt['anteile'][k] * (hoehe - 2*padding)
                punkte.extend([x, y])
            
            if len(punkte) >= 4:
                canvas.create_line(punkte, fill=farbe, width=2, smooth=True)
        
        # Populationslinie zeichnen (falls aktiviert)
        if self.zeige_population_var.get():
            max_pop = self.simulation.breite * self.simulation.hoehe
            punkte = []
            
            for i, datenpunkt in enumerate(daten):
                x = padding + i * (breite - 2*padding) / len(daten)
                y = hoehe - padding - (datenpunkt['population'] / max_pop) * (hoehe - 2*padding)
                punkte.extend([x, y])
            
            if len(punkte) >= 4:
                canvas.create_line(punkte, fill="white", width=1.5, dash=(4, 2))
    
    def aktualisiere_statistik(self):
        """Aktualisiert die Statistik-Anzeige"""
        if self.simulation.history:
            aktuell = self.simulation.history[-1]
            anteile = aktuell['anteile']
            dominante_kultur = anteile.index(max(anteile)) + 1
            
            text = f"Tick: {aktuell['tick']} | Population: {aktuell['population']} | Dominante Kultur: K{dominante_kultur}"
            
            # Monokultur-Prüfung
            mono, kultur = self.simulation.monokultur_erkannt(anteile, aktuell['population'])
            if mono:
                text += f" | MONOKULTUR: K{kultur}"
                if self.auto_stopp_var.get() and self.laufend:
                    self.stopp_simulation()
                    messagebox.showinfo("Monokultur erkannt", f"Monokultur erreicht: Kultur {kultur}")
            
            self.stats_label.config(text=text)
    
    def aktualisiere_anzeige(self):
        """Aktualisiert alle Anzeigen"""
        self.zeichne_status()
        self.zeichne_kultur()
        self.zeichne_diagramm()
        self.aktualisiere_statistik()
    
    def simulations_loop(self):
        """Haupt-Schleife für die Simulation"""
        if self.laufend:
            self.simulation.tick()
            self.aktualisiere_anzeige()
            self.root.after(self.tick_intervall, self.simulations_loop)
    
    def start_simulation(self):
        """Startet die Simulation"""
        if not self.laufend:
            self.laufend = True
            self.simulations_loop()
    
    def stopp_simulation(self):
        """Stoppt die Simulation"""
        self.laufend = False
    
    def zufallsverteilung(self):
        """Setzt eine neue Zufallsverteilung"""
        self.stopp_simulation()
        self.simulation.initialisiere_raum(0.1)
        self.simulation.initialisiere_ressourcen()  # NEU: Ressourcen auch neu initialisieren
        self.aktualisiere_anzeige()
    
    def geschwindigkeit_aendern(self, event=None):
        """Ändert die Simulationsgeschwindigkeit"""
        self.tick_intervall = int(self.speed_var.get())
    
    def export_csv(self):
        """Exportiert die Daten als CSV"""
        try:
            dateiname = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")],
                title="Simulationsdaten speichern"
            )
            if dateiname:
                export_datei = self.simulation.export_csv(dateiname)
                messagebox.showinfo("Export erfolgreich", f"Daten exportiert nach:\n{export_datei}")
        except Exception as e:
            messagebox.showerror("Export Fehler", f"Fehler beim Export: {str(e)}")
    
    def export_png(self):
        """Exportiert das Diagramm als PNG (vereinfacht)"""
        try:
            messagebox.showinfo("PNG Export", 
                              "PNG Export wird in dieser Version vereinfacht dargestellt.\n"
                              "Die Daten sind im CSV-Export enthalten.")
        except Exception as e:
            messagebox.showerror("Export Fehler", f"Fehler beim PNG-Export: {str(e)}")

def main():
    """Hauptfunktion"""
    try:
        root = tk.Tk()
        app = PrimatenGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Fehler: {e}")
        input("Drücken Sie Enter zum Beenden...")

if __name__ == "__main__":
    main()