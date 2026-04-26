"""
Lab2.py
───────
Punto de entrada del Laboratorio 2 - Estructura de Datos II
Universidad del Norte

Ejecutar:
    python Lab2.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import math
import random
import datetime

# ── Módulos propios ───────────────────────────────────────────────────────────
from models.graph           import Graph
from models.grafo_analizador import GrafoAnalizador
from models.Importcsv       import FlightLoader

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


# ============================================================
# VISUALIZADOR DEL GRAFO (Canvas)
# ============================================================
class VisualizadorGrafo(tk.Canvas):
    """
    Dibuja el grafo como un diagrama circular.
    Muestra una componente a la vez para no saturar la pantalla.
    Soporta arrastre con el mouse.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="white", highlightthickness=1, **kwargs)
        self.grafo          = None
        self.nodo_resaltado = None
        self.posiciones     = {}
        self.config(scrollregion=(0, 0, 2000, 2000))
        self.bind("<ButtonPress-1>", self._iniciar_drag)
        self.bind("<B1-Motion>",     self._drag)
        self._drag_inicio = None

    def _iniciar_drag(self, event):
        self._drag_inicio = (event.x, event.y)

    def _drag(self, event):
        if self._drag_inicio:
            dx = event.x - self._drag_inicio[0]
            dy = event.y - self._drag_inicio[1]
            self.xview_scroll(-dx // 5, "units")
            self.yview_scroll(-dy // 5, "units")
            self._drag_inicio = (event.x, event.y)

    def dibujar_subgrafo(self, grafo, nodos_a_mostrar, nodo_resaltado=None, max_nodos=80):
        """
        Dibuja hasta max_nodos nodos del grafo en disposición circular.
        Resalta el nodo indicado en nodo_resaltado si se provee.
        """
        self.delete("all")
        self.grafo          = grafo
        self.nodo_resaltado = nodo_resaltado
        self.posiciones     = {}

        if not nodos_a_mostrar:
            self.create_text(400, 300, text="Sin nodos para mostrar",
                             font=("Arial", 14), fill="#555")
            return

        muestra = nodos_a_mostrar[:max_nodos]
        n       = len(muestra)
        cx, cy  = 600, 500
        radio   = min(400, 60 * n // 6 + 150)

        # Posiciones en círculo
        for i, code in enumerate(muestra):
            angulo = 2 * math.pi * i / n
            self.posiciones[code] = (
                cx + radio * math.cos(angulo),
                cy + radio * math.sin(angulo)
            )

        # Aristas
        for code in muestra:
            x1, y1 = self.posiciones[code]
            for vecino, _ in grafo.obtener_vecinos(code):
                if vecino.code in self.posiciones and vecino.code > code:
                    x2, y2 = self.posiciones[vecino.code]
                    self.create_line(x1, y1, x2, y2, fill="#b0bec5", width=1)

        # Nodos
        r = 18
        for code in muestra:
            x, y = self.posiciones[code]
            if code == nodo_resaltado:
                fill, outline = "#fff3cd", COLOR_ALERTA
            else:
                grado = grafo.grado(code)
                if grado >= 20:
                    fill, outline = "#d5f4e6", COLOR_EXITO
                elif grado >= 5:
                    fill, outline = "#d6eaf8", COLOR_BOTON
                else:
                    fill, outline = "#f2f3f4", COLOR_BORDE

            self.create_oval(x-r, y-r, x+r, y+r,
                             fill=fill, outline=outline, width=2)
            self.create_text(x, y, text=code[:4],
                             font=("Arial", 7, "bold"), fill="#2c3e50")

        self._dibujar_leyenda(n, len(nodos_a_mostrar))

    def dibujar_camino(self, grafo, camino, max_nodos=80):
        """
        Resalta el camino mínimo sobre el grafo.
        - Verde: origen, Rojo: destino, Naranja: intermedios.
        - Aristas del camino en rojo con flecha.
        """
        if not camino:
            return

        camino_set    = set(camino)
        vecinos_extra = []
        for code in camino:
            for v, _ in grafo.obtener_vecinos(code):
                if v.code not in camino_set:
                    vecinos_extra.append(v.code)

        todos = camino + [c for c in vecinos_extra if c not in camino_set][: max_nodos - len(camino)]
        self.dibujar_subgrafo(grafo, todos, max_nodos=max_nodos)

        r = 18
        for i, code in enumerate(camino):
            if code not in self.posiciones:
                continue
            x, y = self.posiciones[code]
            if i == 0:
                fill, outline, lw = "#27ae60", "#1a7a44", 3
            elif i == len(camino) - 1:
                fill, outline, lw = "#e74c3c", "#922b21", 3
            else:
                fill, outline, lw = "#f39c12", "#d68910", 2

            self.create_oval(x - r, y - r, x + r, y + r,
                             fill=fill, outline=outline, width=lw)
            self.create_text(x, y, text=code[:4],
                             font=("Arial", 7, "bold"), fill="white")

        for i in range(len(camino) - 1):
            c1, c2 = camino[i], camino[i + 1]
            if c1 in self.posiciones and c2 in self.posiciones:
                x1, y1 = self.posiciones[c1]
                x2, y2 = self.posiciones[c2]
                self.create_line(x1, y1, x2, y2,
                                 fill=COLOR_ERROR, width=3, arrow=tk.LAST,
                                 arrowshape=(10, 12, 4))

        self._dibujar_leyenda_camino(len(camino))

    def _dibujar_leyenda_camino(self, n_pasos):
        self.create_rectangle(10, 10, 260, 115, fill=COLOR_PANEL, outline=COLOR_BORDE)
        self.create_text(135, 25, text="Camino Mínimo",
                         fill=COLOR_TEXTO, font=("Arial", 9, "bold"))
        items = [
            ("#27ae60", "Origen"),
            (COLOR_ERROR,  "Destino"),
            (COLOR_ALERTA, "Intermedios"),
            (COLOR_BORDE,  "Otros nodos"),
        ]
        for i, (color, texto) in enumerate(items):
            y = 38 + i * 14
            self.create_rectangle(18, y - 5, 28, y + 5, fill=color, outline=color)
            self.create_text(140, y, text=texto, fill=COLOR_TEXTO, font=("Arial", 8))
        self.create_text(135, 112, fill=COLOR_EXITO, font=("Arial", 8),
                         text=f"Camino: {n_pasos} aeropuertos  ({n_pasos - 1} vuelos)")


    def _dibujar_leyenda(self, mostrados, total):
        self.create_rectangle(10, 10, 260, 100, fill=COLOR_PANEL, outline=COLOR_BORDE)
        self.create_text(135, 25, text="Leyenda de nodos",
                         fill=COLOR_TEXTO, font=("Arial", 9, "bold"))
        items = [
            (COLOR_EXITO,  "Hub  (≥20 rutas)"),
            (COLOR_BOTON,  "Regional (5-19 rutas)"),
            (COLOR_BORDE,  "Local (<5 rutas)"),
            (COLOR_ALERTA, "Seleccionado"),
        ]
        for i, (color, texto) in enumerate(items):
            y = 38 + i * 14
            self.create_rectangle(18, y-5, 28, y+5, fill=color, outline=color)
            self.create_text(140, y, text=texto, fill=COLOR_TEXTO, font=("Arial", 8))
        if mostrados < total:
            self.create_text(135, 107, fill=COLOR_ALERTA, font=("Arial", 8),
                             text=f"Mostrando {mostrados} de {total} nodos")


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

        # ── Título ──────────────────────────────────────────────────────────
        tk.Label(self,
                 text=f"Aeropuerto seleccionado: {airport.code}",
                 font=("Arial", 13, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON).pack(pady=(12, 2))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=6)

        # ── Pestaña 1: Información del aeropuerto ───────────────────────────
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

        # ── Pestaña 2: Top 10 caminos más largos ────────────────────────────
        tab_top = tk.Frame(notebook, bg=COLOR_TARJETA)
        notebook.add(tab_top, text="Top 10 — Caminos más largos")

        tk.Label(tab_top,
                 text=f"Los 10 aeropuertos más lejanos desde {airport.code} (por camino mínimo):",
                 bg=COLOR_TARJETA, fg=COLOR_ALERTA,
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

        # Filtramos los 10 destinos alcanzables con mayor distancia
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

        # ── Encabezado ──────────────────────────────────────────────────────
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
                 text=f"Distancia total: {distancia_total:,.1f} km   |   "
                      f"Escalas: {len(camino) - 2}   |   "
                      f"Aeropuertos: {len(camino)}",
                 bg=COLOR_TARJETA, fg=COLOR_EXITO,
                 font=("Arial", 10, "bold")).pack(pady=6)

        # ── Tabla de vértices ────────────────────────────────────────────────
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
    """
    Ventana principal del Laboratorio 2.
    Estructura de tres paneles:
      - Izquierdo: controles (cargar CSV, buscar aeropuerto, navegación)
      - Central:   visualización del grafo (canvas interactivo)
      - Derecho:   análisis (conexidad, bipartito, MST) y log
    """

    def __init__(self):
        super().__init__()
        self.title("Laboratorio 2 - Grafo de Aeropuertos (Vuelos)")
        self.geometry("1300x780")
        self.configure(bg=COLOR_FONDO)

        self.grafo      = Graph()
        self.analizador = GrafoAnalizador()
        self.loader     = FlightLoader()

        # Estado de navegación por componentes
        self._componentes = []
        self._comp_idx    = 0
        self._comp_dict   = {}  # code -> índice de componente

        self._crear_menu()
        self._crear_panel_izquierdo()
        self._crear_panel_central()
        self._crear_panel_derecho()
        self._log("Sistema iniciado. Cargue el archivo flights_final.csv para comenzar.")

    # ── Menú ──────────────────────────────────────────────────────────────────
    def _crear_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        m_arch = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=m_arch)
        m_arch.add_command(label="Cargar CSV de vuelos", command=self._cargar_csv)
        m_arch.add_separator()
        m_arch.add_command(label="Salir", command=self.quit)

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
        tk.Button(panel, text="Buscar y Resaltar en Grafo", command=self._buscar_aeropuerto,
                  bg=COLOR_EXITO, fg="white", width=28).pack(pady=3)
        tk.Button(panel, text="Ver Info + Top 10 más lejanos",
                  command=self._ver_vertice1,
                  bg=COLOR_ALERTA, fg="white", width=28).pack(pady=3)

        # Navegación de componentes
        self._seccion(panel, "Componentes Conexas")
        tk.Label(panel, text="Ver componente #:",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", padx=20)
        frame_nav = tk.Frame(panel, bg=COLOR_PANEL)
        frame_nav.pack(pady=5)
        tk.Button(frame_nav, text="◀ Ant.", command=self._comp_anterior,
                  bg=COLOR_PANEL, fg=COLOR_TEXTO, width=8).pack(side="left", padx=3)
        self.lbl_comp = tk.Label(frame_nav, text="—", bg=COLOR_PANEL, fg=COLOR_ALERTA,
                                  font=("Arial", 11, "bold"), width=6)
        self.lbl_comp.pack(side="left")
        tk.Button(frame_nav, text="Sig. ▶", command=self._comp_siguiente,
                  bg=COLOR_PANEL, fg=COLOR_TEXTO, width=8).pack(side="left", padx=3)

        tk.Label(panel, text="O ir a componente #:",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC).pack(anchor="w", padx=20, pady=(8, 0))
        frame_ir = tk.Frame(panel, bg=COLOR_PANEL)
        frame_ir.pack(pady=3)
        self.entry_comp = tk.Entry(frame_ir, width=6)
        self.entry_comp.pack(side="left", padx=5)
        tk.Button(frame_ir, text="Ir", command=self._ir_a_componente,
                  bg=COLOR_BOTON, fg="white").pack(side="left")

        # Camino mínimo
        self._seccion(panel, "4. Camino Mínimo (Dijkstra)")
        tk.Label(panel, text="Origen (código IATA):",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", padx=20)
        self.entry_origen = tk.Entry(panel, width=30)
        self.entry_origen.pack(pady=3)
        tk.Label(panel, text="Destino (código IATA):",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", padx=20)
        self.entry_destino = tk.Entry(panel, width=30)
        self.entry_destino.pack(pady=3)
        tk.Button(panel, text="Calcular y Mostrar Camino",
                  command=self._calcular_camino,
                  bg=COLOR_ERROR, fg="white", width=28).pack(pady=5)

        # Visualización rápida
        self._seccion(panel, "Visualización Rápida")
        tk.Button(panel, text="Mostrar aeropuertos aleatorios",
                  command=self._mostrar_aleatorios, bg="#9b59b6", fg="white",
                  width=28).pack(pady=5)
        frame_n = tk.Frame(panel, bg=COLOR_PANEL)
        frame_n.pack(pady=3)
        tk.Label(frame_n, text="Cantidad:", bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(side="left")
        self.entry_n = tk.Entry(frame_n, width=6)
        self.entry_n.insert(0, "40")
        self.entry_n.pack(side="left", padx=5)

    # ── Panel central (canvas) ────────────────────────────────────────────────
    def _crear_panel_central(self):
        panel = tk.Frame(self, bg=COLOR_FONDO)
        panel.pack(side="left", fill="both", expand=True, pady=10)

        header = tk.Frame(panel, bg=COLOR_FONDO)
        header.pack(fill="x", padx=10, pady=5)
        tk.Label(header, text="Visualización del Grafo de Vuelos",
                 font=("Arial", 11, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side="left")
        self.lbl_contador = tk.Label(header, text="Vértices: 0  |  Aristas: 0",
                                     bg=COLOR_FONDO, fg=COLOR_EXITO)
        self.lbl_contador.pack(side="right")

        frame_canvas = tk.Frame(panel, bg="white")
        frame_canvas.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = VisualizadorGrafo(frame_canvas, width=860, height=640)
        hbar = ttk.Scrollbar(frame_canvas, orient="horizontal", command=self.canvas.xview)
        vbar = ttk.Scrollbar(frame_canvas, orient="vertical",   command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)

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

        self._seccion(panel, "Estadísticas del Grafo")
        tk.Button(panel, text="Mostrar Top 10 Hubs (más rutas)",
                  command=self._top_hubs, bg="#9b59b6", fg="white", width=32).pack(pady=4)
        tk.Button(panel, text="Mostrar todos los aeropuertos",
                  command=self._mostrar_todos, bg="#9b59b6", fg="white", width=32).pack(pady=4)

        self._seccion(panel, "Registro de Operaciones")
        self.txt_log = scrolledtext.ScrolledText(panel, width=37, height=14,
                                                  bg=COLOR_TARJETA, fg=COLOR_TEXTO)
        self.txt_log.pack(padx=5, pady=5)
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

    def _actualizar_vista(self, nodos=None, resaltar=None):
        if nodos is None:
            nodos = self._componentes[self._comp_idx] if self._componentes else [
                a.code for a in self.grafo.vertices[:80]
            ]
        self.canvas.dibujar_subgrafo(self.grafo, nodos, nodo_resaltado=resaltar)

    def _recalcular_componentes(self):
        """Recalcula las componentes conexas y ordena por tamaño descendente."""
        grafo_dict = self.grafo.to_dict_grafo()
        _, _, _, comps = self.analizador.es_conexo(grafo_dict)
        comps.sort(key=len, reverse=True)
        self._componentes = comps
        self._comp_idx    = 0
        self._comp_dict   = {code: idx
                             for idx, comp in enumerate(comps)
                             for code in comp}
        self.lbl_comp.configure(text=f"1/{len(comps)}")

    # ── Acciones ──────────────────────────────────────────────────────────────
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
            self.lbl_dataset.configure(
                text=f"{os.path.basename(ruta)}\n{mensaje}")
            self._log(mensaje, "exito")
            self._actualizar_contador()
            self._recalcular_componentes()
            self._actualizar_vista()
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
        idx = self._comp_dict.get(code, 0)
        self._comp_idx = idx
        self.lbl_comp.configure(text=f"{idx+1}/{len(self._componentes)}")
        self._actualizar_vista(nodos=self._componentes[idx], resaltar=code)

    def _ver_info_aeropuerto(self):
        """Abre la ventana de info básica (usada internamente por otras ventanas)."""
        code = self.entry_buscar.get().strip().upper()
        a = self.grafo.airport_by_code(code)
        if not a:
            self._log(f"Código '{code}' no encontrado", "error")
            return
        VentanaInfoAeropuerto(self, a, self.grafo)

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

    def _comp_anterior(self):
        if not self._componentes:
            return
        self._comp_idx = (self._comp_idx - 1) % len(self._componentes)
        self._mostrar_componente_actual()

    def _comp_siguiente(self):
        if not self._componentes:
            return
        self._comp_idx = (self._comp_idx + 1) % len(self._componentes)
        self._mostrar_componente_actual()

    def _ir_a_componente(self):
        try:
            n = int(self.entry_comp.get()) - 1
            if 0 <= n < len(self._componentes):
                self._comp_idx = n
                self._mostrar_componente_actual()
            else:
                self._log("Número de componente fuera de rango", "error")
        except ValueError:
            self._log("Ingrese un número válido", "error")

    def _mostrar_componente_actual(self):
        if not self._componentes:
            return
        comp  = self._componentes[self._comp_idx]
        total = len(self._componentes)
        self.lbl_comp.configure(text=f"{self._comp_idx+1}/{total}")
        self._log(f"Componente {self._comp_idx+1}/{total} — {len(comp)} aeropuertos")
        self._actualizar_vista(nodos=comp)

    def _mostrar_aleatorios(self):
        try:
            n = int(self.entry_n.get())
        except ValueError:
            n = 40
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        muestra = random.sample(
            [a.code for a in self.grafo.vertices],
            min(n, self.grafo.num_vertices())
        )
        self._log(f"Mostrando {len(muestra)} aeropuertos aleatorios")
        self._actualizar_vista(nodos=muestra)

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
        self._actualizar_vista(nodos=[a.code for a in top])

    def _mostrar_todos(self):
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        VentanaResultados(self, self.grafo, self.grafo.vertices, "Todos los Aeropuertos")


    def _calcular_camino(self):
        """
        Ejecuta Dijkstra desde el origen, reconstruye el camino hasta
        el destino, lo muestra en el canvas y abre VentanaCamino.
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
                f"No existe ruta entre {origen} y {destino}.\nPuede que pertenezcan a componentes distintas."
            )
            return

        distancia_total = distancias[destino]
        self._log(
            f"Camino encontrado: {' → '.join(camino)}  "
            f"({distancia_total:,.1f} km, {len(camino)-2} escalas)", "exito"
        )

        # Mostrar en el canvas
        self.canvas.dibujar_camino(self.grafo, camino)

        # Abrir ventana de detalle
        VentanaCamino(self, self.grafo, camino, distancia_total)

    def _acerca_de(self):
        messagebox.showinfo(
            "Acerca de",
            "Laboratorio 2 - Estructura de Datos II\n"
            "Universidad del Norte\n\n"
            "Grafo de rutas aéreas — Análisis de conexidad,\n"
            "bipartito y MST (Kruskal)\n"
            "Implementado con Python y tkinter"
        )


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    app = AplicacionGrafo()
    app.mainloop()
