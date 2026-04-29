##    Lab2.py
##    ───────
##    Punto de entrada del Laboratorio 2 - Estructura de Datos II
##    Universidad del Norte

##    Antes de ejecutar, instalar la librería del mapa:
##        pip install tkintermapview

##  Ejecutar:
##      python Lab2.py


import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import datetime

# Intentamos importar tkintermapview; si no está, avisamos al usuario
try:
    import tkintermapview
    MAPA_DISPONIBLE = True
except ImportError:
    MAPA_DISPONIBLE = False

# ── Módulos propios ───────────────────────────────────────────────────────────
from models.graph            import Graph
from models.grafo_analizador import GrafoAnalizador
from models.Importcsv        import FlightLoader

# ============================================================
# PALETA DE COLORES
# ============================================================
COLOR_FONDO     = "#2c3e50"
COLOR_PANEL     = "#34495e"
COLOR_TARJETA   = "#1C2128"
COLOR_BORDE     = "#7f8c8d"
COLOR_BOTON     = "#3498db"
COLOR_EXITO     = "#2ecc71"
COLOR_ERROR     = "#e74c3c"
COLOR_ALERTA    = "#f39c12"
COLOR_TEXTO     = "#ecf0f1"
COLOR_TEXTO_SEC = "#bdc3c7"

## Se define la cantidad de Pines por defecto a mostrar en el mapa.
default_pin : int = 300

# ============================================================
# VISUALIZADOR DE MAPA
# ============================================================
class VisualizadorMapa(tk.Frame):
    """
    Muestra los aeropuertos sobre un mapa real usando tkintermapview.
    Permite marcar aeropuertos individuales y trazar rutas (camino mínimo).
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="black", **kwargs)

        self.grafo = None
        # Guardamos referencias a los markers y paths para poder borrarlos
        self._markers = []
        self._paths   = []

        if not MAPA_DISPONIBLE:
            # Si no está instalada la librería mostramos un mensaje claro
            tk.Label(
                self,
                text=(
                    "⚠  tkintermapview no está instalado.\n\n"
                    "Instálalo con:\n"
                    "    pip install tkintermapview\n\n"
                    "Luego reinicia la aplicación."
                ),
                bg="black", fg=COLOR_ALERTA,
                font=("Arial", 13), justify="center"
            ).pack(expand=True)
            self.widget_mapa = None
            return

        # Widget del mapa
        self.widget_mapa = tkintermapview.TkinterMapView(
            self, corner_radius=0
        )
        self.widget_mapa.pack(fill="both", expand=True)

        # Punto de partida: centro del mundo
        self.widget_mapa.set_position(20, 0)
        self.widget_mapa.set_zoom(2)

    # ──────────────────────────────────────────────────────────────────────────
    # Métodos de dibujo
    # ──────────────────────────────────────────────────────────────────────────

    def limpiar(self):
        """Borra todos los marcadores y rutas del mapa."""
        if not MAPA_DISPONIBLE or self.widget_mapa is None:
            return
        for m in self._markers:
            m.delete()
        for p in self._paths:
            p.delete()
        self._markers.clear()
        self._paths.clear()

    def mostrar_aeropuertos(self, aeropuertos, resaltar=None):
        """
        Pone un pin en el mapa por cada aeropuerto de la lista.
        Si resaltar es un código IATA, ese pin se muestra de otro color.

        aeropuertos: lista de objetos Airport
        resaltar:    código IATA (str) o None
        """
        if not MAPA_DISPONIBLE or self.widget_mapa is None:
            return

        self.limpiar()

        # Para no congelar la app con miles de pins, limitamos a 300 por defecto,
        # mas el usuario lo puede modificar.
        # El enunciado pide mostrar la geolocalización, no dibujar cada arista.
        muestra = aeropuertos[:default_pin]

        for a in muestra:
            # Saltamos aeropuertos con coordenadas inválidas (0, 0)
            if a.lat == 0.0 and a.lon == 0.0:
                continue

            texto_popup = f"{a.code} — {a.name}\n{a.city}, {a.country}"

            if a.code == resaltar:
                # Pin amarillo para el aeropuerto seleccionado
                marker = self.widget_mapa.set_marker(
                    a.lat, a.lon,
                    text=a.code,
                    marker_color_circle="#f39c12",
                    marker_color_outside="#d68910",
                    text_color="#2c3e50",
                    font=("Arial", 9, "bold"),
                    command=lambda m, info=texto_popup: messagebox.showinfo("Aeropuerto", info)
                )
            else:
                marker = self.widget_mapa.set_marker(
                    a.lat, a.lon,
                    text=a.code,
                    marker_color_circle="#3498db",
                    marker_color_outside="#1a6fa8",
                    text_color="black",
                    font=("Arial", 8),
                    command=lambda m, info=texto_popup: messagebox.showinfo("Aeropuerto", info)
                )
            self._markers.append(marker)

        # Si hay un aeropuerto resaltado, centramos el mapa en él
        if resaltar and self.grafo:
            a = self.grafo.airport_by_code(resaltar)
            if a and not (a.lat == 0 and a.lon == 0):
                self.widget_mapa.set_position(a.lat, a.lon)
                self.widget_mapa.set_zoom(5)

    def mostrar_camino(self, grafo, camino):
        """
        Dibuja el camino mínimo sobre el mapa.
        - Pin verde: origen
        - Pin rojo:  destino
        - Pin naranja: escalas intermedias
        - Línea azul conectando todos los puntos
        """
        if not MAPA_DISPONIBLE or self.widget_mapa is None:
            return

        self.limpiar()

        coordenadas = []

        for i, code in enumerate(camino):
            a = grafo.airport_by_code(code)
            if not a or (a.lat == 0 and a.lon == 0):
                continue

            coordenadas.append((a.lat, a.lon))
            texto_popup = f"{a.code} — {a.name}\n{a.city}, {a.country}"

            if i == 0:
                color_circulo  = "#27ae60"
                color_exterior = "#1a7a44"
                etiqueta = f"✈ {a.code}"
            elif i == len(camino) - 1:
                color_circulo  = "#e74c3c"
                color_exterior = "#922b21"
                etiqueta = f"🏁 {a.code}"
            else:
                color_circulo  = "#f39c12"
                color_exterior = "#d68910"
                etiqueta = f"{i}. {a.code}"

            marker = self.widget_mapa.set_marker(
                a.lat, a.lon,
                text=etiqueta,
                marker_color_circle=color_circulo,
                marker_color_outside=color_exterior,
                text_color="black",
                font=("Arial", 9, "bold"),
                command=lambda m, info=texto_popup: messagebox.showinfo("Aeropuerto", info)
            )
            self._markers.append(marker)

        # Trazamos la polyline del recorrido si hay al menos 2 puntos
        if len(coordenadas) >= 2:
            path = self.widget_mapa.set_path(
                coordenadas,
                color="#3498db",
                width=3
            )
            self._paths.append(path)

            # Ajustamos la vista para que se vea todo el camino
            lats = [c[0] for c in coordenadas]
            lons = [c[1] for c in coordenadas]
            lat_centro = (max(lats) + min(lats)) / 2
            lon_centro = (max(lons) + min(lons)) / 2
            self.widget_mapa.set_position(lat_centro, lon_centro)
            self.widget_mapa.set_zoom(3)


# ============================================================
# VENTANA: INFO DE AEROPUERTO
# ============================================================
class VentanaInfoAeropuerto(tk.Toplevel):
    """Muestra los datos de un aeropuerto y sus rutas directas."""

    def __init__(self, parent, airport, grafo):
        super().__init__(parent)
        self.title(f"Aeropuerto - {airport.code}")
        self.geometry("500x420")
        self.configure(bg=COLOR_PANEL)
        self.resizable(True, True)

        frame = tk.Frame(self, bg=COLOR_PANEL)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(frame, text=airport.name, font=("Arial", 12, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON, wraplength=460).pack(anchor="w", pady=(0, 10))

        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True)

        # Pestaña 1: Datos del aeropuerto
        tab1 = tk.Frame(notebook, bg=COLOR_TARJETA)
        notebook.add(tab1, text="Datos del Aeropuerto")

        vecinos = grafo.obtener_vecinos(airport.code)
        campos = [
            ("Código IATA:",    airport.code),
            ("Nombre:",         airport.name),
            ("Ciudad:",         airport.city),
            ("País:",           airport.country),
            ("Latitud:",        f"{airport.lat:.6f}"),
            ("Longitud:",       f"{airport.lon:.6f}"),
            ("Rutas directas:", str(len(vecinos))),
        ]
        for i, (etq, val) in enumerate(campos):
            bg = COLOR_TARJETA if i % 2 == 0 else COLOR_PANEL
            fila = tk.Frame(tab1, bg=bg)
            fila.pack(fill="x")
            tk.Label(fila, text=etq, width=18, anchor="e",
                     bg=bg, fg=COLOR_TEXTO_SEC).pack(side="left", padx=5, pady=3)
            tk.Label(fila, text=val, anchor="w",
                     bg=bg, fg=COLOR_TEXTO).pack(side="left", padx=5, pady=3)

        # Pestaña 2: Rutas directas
        tab2 = tk.Frame(notebook, bg=COLOR_TARJETA)
        notebook.add(tab2, text=f"Rutas Directas ({len(vecinos)})")

        cols = ("code", "city", "country", "dist_km")
        tabla = ttk.Treeview(tab2, columns=cols, show="headings", height=10)
        for col, txt, w in [("code","Código",70), ("city","Ciudad",130),
                             ("country","País",130), ("dist_km","Dist. (km)",90)]:
            tabla.heading(col, text=txt)
            tabla.column(col, width=w, anchor="center" if col in ("code","dist_km") else "w")
        sb = ttk.Scrollbar(tab2, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        for v, d in sorted(vecinos, key=lambda x: x[1]):
            tabla.insert("", "end", values=(v.code, v.city, v.country, f"{d:.1f}"))

        tk.Button(frame, text="Cerrar", command=self.destroy,
                  bg=COLOR_BOTON, fg="white", width=15).pack(pady=10)


# ============================================================
# VENTANA: RESULTADOS GENERALES
# ============================================================
class VentanaResultados(tk.Toplevel):
    """Lista de aeropuertos con doble clic para ver su información."""

    def __init__(self, parent, grafo, aeropuertos, titulo="Resultados"):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("720x420")
        self.configure(bg=COLOR_PANEL)
        self.grafo       = grafo
        self.aeropuertos = {a.code: a for a in aeropuertos}

        header = tk.Frame(self, bg=COLOR_PANEL)
        header.pack(fill="x", padx=10, pady=8)
        tk.Label(header, text=titulo, font=("Arial", 11, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON).pack(side="left")
        tk.Label(header, text=f"  ({len(aeropuertos)} resultados)",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC).pack(side="left")

        cols = ("code", "name", "city", "country", "grado")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for col, txt, w in [("code","Código",70), ("name","Nombre",200),
                             ("city","Ciudad",120), ("country","País",120),
                             ("grado","Rutas",70)]:
            self.tabla.heading(col, text=txt)
            self.tabla.column(col, width=w, anchor="center" if col in ("code","grado") else "w")
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        sb.pack(side="left", fill="y", pady=10, padx=(0, 10))

        for a in aeropuertos:
            self.tabla.insert("", "end", iid=a.code, values=(
                a.code, a.name[:35], a.city, a.country, grafo.grado(a.code)
            ))

        self.tabla.bind("<Double-1>", self._mostrar_info)
        tk.Label(self, text="Doble clic para ver detalles del aeropuerto",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC, font=("Arial", 9)).pack(pady=(0, 8))

    def _mostrar_info(self, event):
        sel = self.tabla.selection()
        if sel and sel[0] in self.aeropuertos:
            VentanaInfoAeropuerto(self, self.aeropuertos[sel[0]], self.grafo)


# ============================================================
# VENTANA: MST
# ============================================================
class VentanaMST(tk.Toplevel):
    """Muestra el resultado del MST (Kruskal) por cada componente."""

    def __init__(self, parent, resultados):
        super().__init__(parent)
        self.title("Árbol de Expansión Mínima (Kruskal)")
        self.geometry("650x500")
        self.configure(bg=COLOR_PANEL)

        tk.Label(self, text="Árbol de Expansión Mínima por Componente",
                 font=("Arial", 12, "bold"), bg=COLOR_PANEL, fg=COLOR_ALERTA).pack(pady=8)

        txt = scrolledtext.ScrolledText(self, bg=COLOR_TARJETA, fg=COLOR_TEXTO,
                                        width=80, height=25, font=("Courier", 9))
        txt.pack(padx=10, pady=5, fill="both", expand=True)

        peso_global = 0
        for r in resultados:
            txt.insert("end", f"\n{'='*55}\n")
            txt.insert("end", f"Componente {r['componente']}  —  {len(r['vertices'])} aeropuertos\n")
            txt.insert("end", f"Peso MST: {r['peso_mst']:,.1f} km   |   Aristas: {len(r['aristas_mst'])}\n")
            txt.insert("end", f"{'─'*55}\n")
            for u, v, p in r['aristas_mst'][:30]:
                txt.insert("end", f"  {u:>4}  ──({p:>9,.1f} km)──  {v}\n")
            if len(r['aristas_mst']) > 30:
                txt.insert("end", f"  ... y {len(r['aristas_mst'])-30} aristas más\n")
            peso_global += r['peso_mst']

        txt.insert("end", f"\n{'='*55}\n")
        txt.insert("end", f"PESO TOTAL GLOBAL: {peso_global:,.1f} km\n")
        txt.configure(state="disabled")

        tk.Button(self, text="Cerrar", command=self.destroy,
                  bg=COLOR_BOTON, fg="white", width=15).pack(pady=8)


# ============================================================
# VENTANA: VÉRTICE 1 — INFO + TOP 10 CAMINOS MÁS LARGOS
# ============================================================
class VentanaVertice1(tk.Toplevel):
    """
    Muestra toda la información del aeropuerto seleccionado como
    vértice 1, y la tabla con los 10 aeropuertos cuyos caminos
    mínimos desde ese vértice son los más largos.
    """

    def __init__(self, parent, grafo, airport, distancias):
        super().__init__(parent)
        self.title(f"Vértice 1 — {airport.code}")
        self.geometry("680x560")
        self.configure(bg=COLOR_PANEL)
        self.resizable(True, True)

        tk.Label(self,
                 text=f"Aeropuerto seleccionado: {airport.code}",
                 font=("Arial", 13, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON).pack(pady=(12, 2))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=6)

        # Pestaña 1: Información del aeropuerto
        tab_info = tk.Frame(notebook, bg=COLOR_TARJETA)
        notebook.add(tab_info, text="Información del Aeropuerto")

        campos = [
            ("Código IATA:",  airport.code),
            ("Nombre:",       airport.name),
            ("Ciudad:",       airport.city),
            ("País:",         airport.country),
            ("Latitud:",      f"{airport.lat:.6f}"),
            ("Longitud:",     f"{airport.lon:.6f}"),
            ("Rutas directas:", str(grafo.grado(airport.code))),
        ]
        for i, (etq, val) in enumerate(campos):
            bg = COLOR_TARJETA if i % 2 == 0 else COLOR_PANEL
            fila = tk.Frame(tab_info, bg=bg)
            fila.pack(fill="x")
            tk.Label(fila, text=etq, width=18, anchor="e",
                     bg=bg, fg=COLOR_TEXTO_SEC,
                     font=("Arial", 10)).pack(side="left", padx=8, pady=5)
            tk.Label(fila, text=val, anchor="w",
                     bg=bg, fg=COLOR_TEXTO,
                     font=("Arial", 10, "bold")).pack(side="left", padx=8, pady=5)

        # Pestaña 2: Top 10 caminos más largos
        tab_top = tk.Frame(notebook, bg=COLOR_TARJETA)
        notebook.add(tab_top, text="Top 10 — Caminos más largos")

        tk.Label(tab_top,
                 text=f"Los 10 aeropuertos más lejanos desde {airport.code} (por camino mínimo):",
                 bg=COLOR_TARJETA, fg=COLOR_ALERTA,
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

        alcanzables = [
            (dist, code)
            for code, dist in distancias.items()
            if dist != float("inf") and code != airport.code
        ]
        top10 = sorted(alcanzables, reverse=True)[:10]

        cols = ("rank", "code", "name", "city", "country", "lat", "lon", "distancia")
        tabla = ttk.Treeview(tab_top, columns=cols, show="headings", height=12)
        tabla.heading("rank",      text="#")
        tabla.heading("code",      text="Código")
        tabla.heading("name",      text="Nombre")
        tabla.heading("city",      text="Ciudad")
        tabla.heading("country",   text="País")
        tabla.heading("lat",       text="Latitud")
        tabla.heading("lon",       text="Longitud")
        tabla.heading("distancia", text="Distancia (km)")

        tabla.column("rank",      width=30,  anchor="center")
        tabla.column("code",      width=55,  anchor="center")
        tabla.column("name",      width=160, anchor="w")
        tabla.column("city",      width=100, anchor="w")
        tabla.column("country",   width=90,  anchor="w")
        tabla.column("lat",       width=70,  anchor="center")
        tabla.column("lon",       width=70,  anchor="center")
        tabla.column("distancia", width=100, anchor="center")

        sb = ttk.Scrollbar(tab_top, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)
        sb.pack(side="left", fill="y", pady=6, padx=(0, 8))

        for i, (dist, code) in enumerate(top10, 1):
            a = grafo.airport_by_code(code)
            if not a:
                continue
            tabla.insert("", "end", values=(
                i, a.code, a.name[:25], a.city, a.country,
                f"{a.lat:.4f}", f"{a.lon:.4f}",
                f"{dist:,.1f}"
            ))

        tk.Button(self, text="Cerrar", command=self.destroy,
                  bg=COLOR_BOTON, fg="white", width=15).pack(pady=8)


# ============================================================
# VENTANA: CAMINO MÍNIMO
# ============================================================
class VentanaCamino(tk.Toplevel):
    """
    Muestra el camino mínimo entre dos aeropuertos:
    distancia total, número de escalas e información
    detallada de cada vértice intermedio.
    """

    def __init__(self, parent, grafo, camino, distancia_total):
        super().__init__(parent)
        self.title("Camino Mínimo — Dijkstra")
        self.geometry("660x480")
        self.configure(bg=COLOR_PANEL)

        origen  = grafo.airport_by_code(camino[0])
        destino = grafo.airport_by_code(camino[-1])

        tk.Label(self,
                 text=f"Ruta: {camino[0]}  →  {camino[-1]}",
                 font=("Arial", 13, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_ALERTA).pack(pady=(10, 2))
        tk.Label(self,
                 text=f"{origen.city}, {origen.country}   ✈   {destino.city}, {destino.country}",
                 font=("Arial", 10),
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC).pack(pady=(0, 4))

        resumen = tk.Frame(self, bg=COLOR_TARJETA)
        resumen.pack(fill="x", padx=15, pady=5)
        tk.Label(resumen,
                 text=(f"Distancia total: {distancia_total:,.1f} km   |   "
                       f"Escalas: {len(camino) - 2}   |   "
                       f"Aeropuertos: {len(camino)}"),
                 bg=COLOR_TARJETA, fg=COLOR_EXITO,
                 font=("Arial", 10, "bold")).pack(pady=6)

        tk.Label(self, text="Detalle del recorrido:",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO,
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=15)

        cols = ("paso", "code", "name", "city", "country", "lat", "lon")
        tabla = ttk.Treeview(self, columns=cols, show="headings", height=12)
        tabla.heading("paso",    text="#")
        tabla.heading("code",    text="Código")
        tabla.heading("name",    text="Nombre")
        tabla.heading("city",    text="Ciudad")
        tabla.heading("country", text="País")
        tabla.heading("lat",     text="Latitud")
        tabla.heading("lon",     text="Longitud")
        tabla.column("paso",    width=35,  anchor="center")
        tabla.column("code",    width=60,  anchor="center")
        tabla.column("name",    width=180, anchor="w")
        tabla.column("city",    width=110, anchor="w")
        tabla.column("country", width=100, anchor="w")
        tabla.column("lat",     width=75,  anchor="center")
        tabla.column("lon",     width=75,  anchor="center")

        sb = ttk.Scrollbar(self, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=5)
        sb.pack(side="left", fill="y", pady=5, padx=(0, 10))

        for i, code in enumerate(camino):
            a = grafo.airport_by_code(code)
            if not a:
                continue
            if i == 0:
                rol = "🟢 Origen"
            elif i == len(camino) - 1:
                rol = "🔴 Destino"
            else:
                rol = f"   Escala {i}"
            tabla.insert("", "end", values=(
                rol, a.code, a.name[:28], a.city, a.country,
                f"{a.lat:.4f}", f"{a.lon:.4f}"
            ))

        tk.Button(self, text="Cerrar", command=self.destroy,
                  bg=COLOR_BOTON, fg="white", width=15).pack(pady=8)


# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================
class AplicacionGrafo(tk.Tk):
    ## Ventana principal del Laboratorio 2.
    ## Estructura de tres paneles:
    ##   - Izquierdo: controles (cargar CSV, buscar aeropuerto, navegación)
    ##   - Central:   mapa interactivo con los aeropuertos geolocalizados
    ##   - Derecho:   análisis (conexidad, bipartito, MST) y log
    

    def __init__(self):
        super().__init__()
        self.title("Laboratorio 2 - Grafo de Aeropuertos (Vuelos)")
        self.geometry("1300x780")
        self.configure(bg=COLOR_FONDO)

        self.grafo      = Graph()
        self.analizador = GrafoAnalizador()
        self.loader     = FlightLoader()

        # Lista de componentes (para navegación)
        self._componentes = []
        self._comp_idx    = 0
        self._comp_dict   = {}

        self._crear_menu()
        self._crear_panel_izquierdo()
        self._crear_panel_central()
        self._crear_panel_derecho()
        self._log("Sistema iniciado. Cargue el archivo flights_final.csv para comenzar.")

        if not MAPA_DISPONIBLE:
            self._log(
                "AVISO: tkintermapview no está instalado. "
                "Ejecuta: pip install tkintermapview",
                "alerta"
            )

    # ── Menú ──────────────────────────────────────────────────────────────────
    def _crear_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        m_arch = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=m_arch)
        m_arch.add_command(label="Cargar CSV de vuelos", command=self._cargar_csv)
        m_arch.add_separator()
        m_arch.add_command(label="Salir", command=self.quit)

        m_vista = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Vista", menu=m_vista)
        m_vista.add_command(label="Mostrar todos los aeropuertos en el mapa",
                            command=self._mostrar_todos_en_mapa)
        m_vista.add_command(label="Limpiar mapa", command=self._limpiar_mapa)

        m_ayuda = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=m_ayuda)
        m_ayuda.add_command(label="Acerca de", command=self._acerca_de)

    # ── Panel izquierdo ───────────────────────────────────────────────────────
    def _crear_panel_izquierdo(self):
        panel = tk.Frame(self, bg=COLOR_PANEL, width=310)
        panel.pack(side="left", fill="y", padx=10, pady=10)
        panel.pack_propagate(False)

        tk.Label(panel, text="Operaciones", font=("Arial", 12, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON).pack(pady=10)

        # Dataset
        self._seccion(panel, "Dataset")
        tk.Button(panel, text="Cargar CSV de Vuelos", command=self._cargar_csv,
                  bg=COLOR_BOTON, fg="white", width=28).pack(pady=5)
        self.lbl_dataset = tk.Label(panel, text="Sin dataset cargado",
                                    bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC, wraplength=290)
        self.lbl_dataset.pack(pady=5)

        # Buscar aeropuerto
        self._seccion(panel, "Buscar Aeropuerto")
        tk.Label(panel, text="Código IATA (ej. BOG, MIA):",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", padx=20)
        self.entry_buscar = tk.Entry(panel, width=30)
        self.entry_buscar.pack(pady=5)
        tk.Button(panel, text="Buscar y Marcar en Mapa", command=self._buscar_aeropuerto,
                  bg=COLOR_EXITO, fg="white", width=28).pack(pady=3)
        tk.Button(panel, text="Ver Info + Top 10 más lejanos",
                  command=self._ver_vertice1,
                  bg=COLOR_ALERTA, fg="white", width=28).pack(pady=3)

        # Mostrar en mapa
        self._seccion(panel, "Vista del Mapa")
        tk.Label(panel, text= "Cantidad máxima de Pines (entero):",
                 bg=COLOR_PANEL, fg= COLOR_TEXTO).pack(anchor="w", padx=20)
        self.entry_pines = tk.Entry(panel, width=30)
        self.entry_pines.pack(pady=5)
        tk.Button(panel, text="Mostrar pines en el mapa",
                  command=self._mostrar_todos_en_mapa,
                  bg="#9b59b6", fg="white", width=28).pack(pady=3)
        tk.Button(panel, text="Limpiar mapa",
                  command=self._limpiar_mapa,
                  bg=COLOR_BORDE, fg="white", width=28).pack(pady=3)

        # Camino mínimo
        self._seccion(panel, "Camino Mínimo (Dijkstra)")
        tk.Label(panel, text="Origen (código IATA):",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", padx=20)
        self.entry_origen = tk.Entry(panel, width=30)
        self.entry_origen.pack(pady=3)
        tk.Label(panel, text="Destino (código IATA):",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", padx=20)
        self.entry_destino = tk.Entry(panel, width=30)
        self.entry_destino.pack(pady=3)
        tk.Button(panel, text="Calcular y Mostrar en Mapa",
                  command=self._calcular_camino,
                  bg=COLOR_ERROR, fg="white", width=28).pack(pady=5)

        # Estadísticas rápidas
        self._seccion(panel, "Estadísticas")
        tk.Button(panel, text="Top 10 Hubs (más rutas)",
                  command=self._top_hubs, bg="#9b59b6", fg="white",
                  width=28).pack(pady=4)
        tk.Button(panel, text="Mostrar todos los aeropuertos",
                  command=self._mostrar_todos, bg="#9b59b6", fg="white",
                  width=28).pack(pady=4)

    # ── Panel central (mapa) ──────────────────────────────────────────────────
    def _crear_panel_central(self):
        panel = tk.Frame(self, bg=COLOR_FONDO)
        panel.pack(side="left", fill="both", expand=True, pady=10)

        header = tk.Frame(panel, bg=COLOR_FONDO)
        header.pack(fill="x", padx=10, pady=5)
        tk.Label(header, text="Mapa de Rutas Aéreas",
                 font=("Arial", 11, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side="left")
        self.lbl_contador = tk.Label(header, text="Vértices: 0  |  Aristas: 0",
                                     bg=COLOR_FONDO, fg=COLOR_EXITO)
        self.lbl_contador.pack(side="right")

        # El mapa ocupa el resto del panel central
        self.mapa = VisualizadorMapa(panel)
        self.mapa.pack(fill="both", expand=True, padx=10, pady=5)

    # ── Panel derecho ─────────────────────────────────────────────────────────
    def _crear_panel_derecho(self):
        panel = tk.Frame(self, bg=COLOR_PANEL, width=310)
        panel.pack(side="right", fill="y", padx=10, pady=10)
        panel.pack_propagate(False)

        tk.Label(panel, text="Análisis del Grafo", font=("Arial", 12, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_ALERTA).pack(pady=10)

        self._seccion(panel, "1. Conexidad (DFS)")
        tk.Button(panel, text="Analizar Conexidad", command=self._analizar_conexidad,
                  bg=COLOR_BOTON, fg="white", width=32).pack(pady=5)

        self._seccion(panel, "2. Bipartito (BFS)")
        tk.Button(panel, text="Verificar Bipartito (comp. mayor)",
                  command=self._analizar_bipartito, bg=COLOR_BOTON, fg="white",
                  width=32).pack(pady=5)

        self._seccion(panel, "3. MST – Kruskal")
        tk.Button(panel, text="Calcular MST por Componente",
                  command=self._calcular_mst, bg=COLOR_ALERTA, fg="white",
                  width=32).pack(pady=5)

        self._seccion(panel, "Registro de Operaciones")
        self.txt_log = scrolledtext.ScrolledText(panel, width=37, height=18,
                                                  bg=COLOR_TARJETA, fg=COLOR_TEXTO)
        self.txt_log.pack(padx=5, pady=5, fill="both", expand=True)
        self.txt_log.configure(state="disabled")

    # ── Utilidades UI ─────────────────────────────────────────────────────────
    def _seccion(self, parent, titulo):
        tk.Frame(parent, bg=COLOR_BORDE, height=2).pack(fill="x", padx=10, pady=12)
        tk.Label(parent, text=titulo, font=("Arial", 10, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON).pack(anchor="w", padx=10)

    def _log(self, mensaje, tipo="info"):
        self.txt_log.configure(state="normal")
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        tag_map = {"error": COLOR_ERROR, "exito": COLOR_EXITO, "alerta": COLOR_ALERTA}
        self.txt_log.tag_configure(tipo, foreground=tag_map.get(tipo, COLOR_TEXTO))
        self.txt_log.insert("end", f"[{hora}] {mensaje}\n", tipo)
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _actualizar_contador(self):
        self.lbl_contador.configure(
            text=f"Vértices: {self.grafo.num_vertices()}  |  Aristas: {self.grafo.num_aristas()}"
        )

    # ── Acciones de mapa ──────────────────────────────────────────────────────
    def _mostrar_todos_en_mapa(self):
        ## Coloca un pin por cada aeropuerto del grafo
        try:
            pins = int(self.entry_pines.get().strip())
        except ValueError:
            pins = 300
        
        default_pin = pins
        
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        self._log(f"Mostrando {self.grafo.num_vertices()} aeropuertos en el mapa "
                  f"(max. {default_pin} pines)...")
        self.update()
        self.mapa.grafo = self.grafo
        self.mapa.mostrar_aeropuertos(self.grafo.vertices)
        self._log("Mapa actualizado. Haga clic en un pin para ver info.", "exito")

    def _limpiar_mapa(self):
        self.mapa.limpiar()
        self._log("Mapa limpiado.")

    # ── Acciones principales ──────────────────────────────────────────────────
    def _cargar_csv(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar flights_final.csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")]
        )
        if not ruta:
            return
        self._log("Cargando dataset (puede tardar unos segundos)...")
        self.update()
        exito, grafo, mensaje = self.loader.cargar(ruta)
        if exito:
            self.grafo = grafo
            self.mapa.grafo = grafo
            self.lbl_dataset.configure(
                text=f"{os.path.basename(ruta)}\n{mensaje}")
            self._log(mensaje, "exito")
            self._actualizar_contador()
            self._recalcular_componentes()
            # Mostramos todos los aeropuertos en el mapa al cargar
            self._log("Cargando pins en el mapa...")
            self.update()
            self.mapa.mostrar_aeropuertos(self.grafo.vertices)
            self._log("¡Listo! Aeropuertos visibles en el mapa.", "exito")
        else:
            self._log(mensaje, "error")

    def _buscar_aeropuerto(self):
        code = self.entry_buscar.get().strip().upper()
        if not code:
            self._log("Ingrese un código IATA", "error")
            return
        a = self.grafo.airport_by_code(code)
        if not a:
            self._log(f"Aeropuerto '{code}' no encontrado", "error")
            return
        self._log(
            f"Encontrado: {a.name} ({a.city}, {a.country}) — {self.grafo.grado(code)} rutas",
            "exito"
        )
        # Mostramos todos pero resaltamos el buscado
        self.mapa.mostrar_aeropuertos(self.grafo.vertices, resaltar=code)

    def _ver_vertice1(self):
        """
        Muestra la información completa del aeropuerto ingresado como
        vértice 1, y calcula con Dijkstra los 10 destinos cuyos caminos
        mínimos desde ese vértice son los más largos.
        """
        code = self.entry_buscar.get().strip().upper()
        if not code:
            self._log("Ingrese un código IATA en el campo de búsqueda", "error")
            return
        a = self.grafo.airport_by_code(code)
        if not a:
            self._log(f"Aeropuerto '{code}' no encontrado", "error")
            return

        self._log(f"Calculando caminos mínimos desde {code} (Dijkstra)...")
        self.update()

        grafo_pesos = self.grafo.to_dict_pesos()
        distancias, _ = self.analizador.dijkstra(grafo_pesos, code)

        alcanzables = [d for d in distancias.values() if d != float("inf") and d > 0]
        self._log(
            f"Vértice 1: {a.name} ({a.city}) — "
            f"{len(alcanzables)} aeropuertos alcanzables", "exito"
        )

        VentanaVertice1(self, self.grafo, a, distancias)

    def _analizar_conexidad(self):
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        grafo_d = self.grafo.to_dict_grafo()
        conexo, num, tamaños, _ = self.analizador.es_conexo(grafo_d)
        if conexo:
            self._log(f"El grafo ES CONEXO — {self.grafo.num_vertices()} vértices", "exito")
        else:
            self._log(f"El grafo NO ES CONEXO — {num} componentes", "alerta")
            for i, t in enumerate(sorted(tamaños, reverse=True)[:5], 1):
                self._log(f"  Comp. {i}: {t} aeropuertos")
            if len(tamaños) > 5:
                self._log(f"  ... y {len(tamaños)-5} componentes más")
        messagebox.showinfo(
            "Análisis de Conexidad",
            f"El grafo {'ES' if conexo else 'NO ES'} conexo.\n"
            f"Componentes conexas: {num}\n"
            f"Componente más grande: {max(tamaños)} aeropuertos\n"
            f"Componente más pequeña: {min(tamaños)} aeropuertos"
        )

    def _analizar_bipartito(self):
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        grafo_d  = self.grafo.to_dict_grafo()
        _, _, tamaños, comps = self.analizador.es_conexo(grafo_d)
        mayor    = comps[tamaños.index(max(tamaños))]
        es_bip   = self.analizador.es_bipartito(grafo_d, mayor)
        tipo     = "exito" if es_bip else "alerta"
        self._log(
            f"Componente mayor ({len(mayor)} nodos) "
            f"{'ES' if es_bip else 'NO ES'} BIPARTITA", tipo
        )
        messagebox.showinfo(
            "Análisis Bipartito",
            f"Componente más grande: {len(mayor)} aeropuertos\n\n"
            f"Resultado: {'ES BIPARTITA ✔' if es_bip else 'NO ES BIPARTITA ✘'}\n\n"
            "Un grafo bipartito no tiene ciclos de longitud impar.\n"
            "Una red de vuelos generalmente NO es bipartita porque\n"
            "existen rutas triangulares entre aeropuertos."
        )

    def _calcular_mst(self):
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        self._log("Calculando MST con Kruskal (puede tardar)...")
        self.update()
        grafo_d    = self.grafo.to_dict_grafo()
        aristas    = self.grafo.obtener_aristas()
        resultados = self.analizador.mst_por_componente(grafo_d, aristas)
        peso_total = sum(r['peso_mst'] for r in resultados)
        self._log(
            f"MST calculado: {len(resultados)} componentes — "
            f"Peso total: {peso_total:,.1f} km", "exito"
        )
        VentanaMST(self, resultados)

    def _top_hubs(self):
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        top = sorted(self.grafo.vertices,
                     key=lambda a: self.grafo.grado(a.code),
                     reverse=True)[:10]
        self._log("Top 10 hubs:")
        for a in top:
            self._log(f"  {a.code}: {self.grafo.grado(a.code)} rutas — {a.city}")
        VentanaResultados(self, self.grafo, top, "Top 10 Hubs (más rutas directas)")
        # Marcamos los hubs en el mapa
        self.mapa.mostrar_aeropuertos(top)

    def _mostrar_todos(self):
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        VentanaResultados(self, self.grafo, self.grafo.vertices, "Todos los Aeropuertos")

    def _calcular_camino(self):
        """
        Ejecuta Dijkstra desde el origen, reconstruye el camino hasta
        el destino y lo muestra sobre el mapa con una línea azul.
        """
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return

        origen  = self.entry_origen.get().strip().upper()
        destino = self.entry_destino.get().strip().upper()

        if not origen or not destino:
            self._log("Ingrese origen y destino", "error")
            return
        if not self.grafo.airport_by_code(origen):
            self._log(f"Aeropuerto origen '{origen}' no encontrado", "error")
            return
        if not self.grafo.airport_by_code(destino):
            self._log(f"Aeropuerto destino '{destino}' no encontrado", "error")
            return
        if origen == destino:
            self._log("Origen y destino son el mismo aeropuerto", "error")
            return

        self._log(f"Calculando camino mínimo {origen} → {destino}...")
        self.update()

        grafo_pesos = self.grafo.to_dict_pesos()
        distancias, previos = self.analizador.dijkstra(grafo_pesos, origen)
        camino = self.analizador.reconstruir_camino(previos, origen, destino)

        if not camino:
            self._log(f"No existe camino entre {origen} y {destino}", "alerta")
            messagebox.showwarning(
                "Sin camino",
                f"No existe ruta entre {origen} y {destino}.\n"
                "Puede que pertenezcan a componentes distintas."
            )
            return

        distancia_total = distancias[destino]
        self._log(
            f"Camino encontrado: {' → '.join(camino)}  "
            f"({distancia_total:,.1f} km, {len(camino)-2} escalas)", "exito"
        )

        # Mostrar el camino en el mapa
        self.mapa.mostrar_camino(self.grafo, camino)

        # Abrir ventana de detalle
        VentanaCamino(self, self.grafo, camino, distancia_total)

    def _recalcular_componentes(self):
        """Recalcula las componentes conexas y las ordena por tamaño."""
        grafo_dict = self.grafo.to_dict_grafo()
        _, _, _, comps = self.analizador.es_conexo(grafo_dict)
        comps.sort(key=len, reverse=True)
        self._componentes = comps
        self._comp_idx    = 0
        self._comp_dict   = {
            code: idx
            for idx, comp in enumerate(comps)
            for code in comp
        }

    def _acerca_de(self):
        messagebox.showinfo(
            "Acerca de",
            "Laboratorio 2 - Estructura de Datos II\n"
            "Universidad del Norte\n\n"
            "Grafo de rutas aéreas — Análisis de conexidad,\n"
            "bipartito y MST (Kruskal) con mapa interactivo.\n\n"
            "Implementado con Python, tkinter y tkintermapview."
        )


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    app = AplicacionGrafo()
    app.mainloop()