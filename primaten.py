#!/usr/bin/env python3
"""
Primaten – erweiterte Kultursimulation mit GUI
Eine agentenbasierte Simulation zur Erforschung kultureller Dynamiken in Primatengruppen
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
    """Klasse für einen einzelnen Primaten"""
    def __init__(self, status=0, alter=0, geschlecht=0, kultur=0, macht=0):
        self.status = status      # 0=kein Primat, 1=jung, 2=erwachsen
        self.alter = alter        # in Ticks
        self.geschlecht = geschlecht  # 1=weiblich, 2=männlich
        self.kultur = kultur      # 1-9 für verschiedene Kulturen
        self.macht = macht        # Sozialer Einfluss (1-9)

class PrimatenSimulation:
    """Hauptklasse für die Primaten-Simulation"""
    
    def __init__(self, breite=60, hoehe=60, initial_dichte=0.1):
        self.breite = breite
        self.hoehe = hoehe
        self.raum = np.empty((hoehe, breite), dtype=object)
        self.tick_index = 0
        self.history = []
        self.max_history = 5000
        self.kultur_farben = [
            None, '#e6194B', '#3cb44b', '#ffe119', '#4363d8', 
            '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c'
        ]
        self.initialisiere_raum(initial_dichte)
        
    def initialisiere_raum(self, dichte=0.1):
        """Initialisiert den Raum mit zufällig verteilten Primaten"""
        for y in range(self.hoehe):
            for x in range(self.breite):
                if random.random() < dichte:
                    # Zufällige Eigenschaften für neuen Primaten
                    geschlecht = 1 if random.random() < 0.5 else 2
                    kultur = random.randint(1, 9)
                    macht = random.randint(1, 9)
                    self.raum[y][x] = Primat(1, 0, geschlecht, kultur, macht)
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
                nachbarn_pos.append(self.raum[ny][nx])
        return nachbarn_pos
    
    def kind_erzeugen(self, mutter):
        """Erzeugt ein neues Kind basierend auf der Mutter"""
        geschlecht = 1 if random.random() < 0.5 else 2
        return Primat(1, 0, geschlecht, mutter.kultur, mutter.macht)
    
    def neue_generation(self, x, y):
        """Berechnet den neuen Zustand für eine Position"""
        aktuell = self.raum[y][x]
        nachbarn = self.nachbarn(x, y)
        
        # Kopie des aktuellen Zustands
        neu = Primat(aktuell.status, aktuell.alter, aktuell.geschlecht, 
                    aktuell.kultur, aktuell.macht)
        
        # Alterungsprozess
        if neu.status > 0:
            if random.random() < 0.8:
                neu.alter += 1
            if neu.alter > 19:
                neu.status = 0  # Tod
            elif neu.alter >= 3 and neu.status == 1:
                neu.status = 2  # Erwachsen werden
        
        # Geburt neuer Primaten
        if neu.status == 0:
            weibchen = [p for p in nachbarn if p.status == 2 and p.geschlecht == 1]
            maennchen = [p for p in nachbarn if p.status == 2 and p.geschlecht == 2]
            
            if weibchen and maennchen and random.random() < 0.25:
                mutter = random.choice(weibchen)
                return self.kind_erzeugen(mutter)
            
            # Spontane Entstehung (Migration)
            if random.random() < 0.001:
                geschlecht = 1 if random.random() < 0.5 else 2
                kultur = random.randint(1, 9)
                macht = random.randint(1, 9)
                return Primat(1, 0, geschlecht, kultur, macht)
        
        # Isolationstod - wenn komplett von anderen Kulturen umgeben
        if neu.status > 0:
            fremde = [p for p in nachbarn if p.kultur != neu.kultur]
            if len(fremde) == 8:  # Alle Nachbarn sind fremd
                return Primat()
        
        # Kulturelle Beeinflussung
        if neu.status == 2:
            staerkere = [p for p in nachbarn if p.status == 2 and p.macht > neu.macht]
            if staerkere:
                einflussreichster = max(staerkere, key=lambda p: p.macht)
                if random.random() < 0.3:
                    neu.kultur = einflussreichster.kultur
                    neu.macht = max(0, neu.macht - 1)
            else:
                neu.macht = min(9, neu.macht + 0.1)
        
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
                    kultur_zaehler[p.kultur - 1] += 1
                    gesamt_population += 1
        
        # Anteile berechnen
        anteile = [count / gesamt_population if gesamt_population > 0 else 0 
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
        self.root.title("Primaten – erweiterte Kultursimulation")
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
    
    def hex_to_rgb(self, hex_color):
        """Wandelt Hex-Farben in RGB um"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def zeichne_status(self):
        """Zeichnet die Status-Ansicht"""
        canvas = self.status_canvas
        canvas.delete("all")
        
        breite = canvas.winfo_width()
        hoehe = canvas.winfo_height()
        zell_groesse = min(breite // self.simulation.breite, hoehe // self.simulation.hoehe)
        
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
            # Hier könnte man mit PIL ein echtes PNG erstellen
            # Für diese Version zeigen wir einfach eine Info an
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