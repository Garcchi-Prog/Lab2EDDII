import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import csv
import os
import math
import random
from collections import deque
import datetime

# ============================================================
# COLORES GLOBALES (mismo esquema visual que Lab1)
# ============================================================
COLOR_FONDO      = "#2c3e50"   # Azul oscuro: fondo principal
COLOR_PANEL      = "#34495e"   # Azul medio: paneles laterales
COLOR_TARJETA    = "#1C2128"   # Negro oscuro: áreas de texto
COLOR_BORDE      = "#7f8c8d"   # Gris: separadores
COLOR_BOTON      = "#3498db"   # Azul brillante: acción principal
COLOR_EXITO      = "#2ecc71"   # Verde: operaciones exitosas
COLOR_ERROR      = "#e74c3c"   # Rojo: errores / eliminar
COLOR_ALERTA     = "#f39c12"   # Naranja: alertas / MST
COLOR_TEXTO      = "#ecf0f1"   # Blanco suave: texto principal
COLOR_TEXTO_SEC  = "#bdc3c7"   # Gris claro: texto secundario


# ============================================================
# HAVERSINE
# ============================================================
def haversine(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos coordenadas geográficas."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ============================================================
# MODELOS DE DATOS
# ============================================================
class Airport:
    def __init__(self, code, name, city, country, lat, lon):
        self.code    = code
        self.name    = name
        self.city    = city
        self.country = country
        self.lat     = float(lat)
        self.lon     = float(lon)

    def __repr__(self):
        return f"{self.code} ({self.city}, {self.country})"


# ============================================================
# GRAFO (Matriz de adyacencia)
# ============================================================
class Graph:
    def __init__(self):
        self.vertices   = []   # lista de Airport
        self.adyacencia = []   # matriz NxN de distancias (None = sin arista)

    def _indice(self, code):
        for i, a in enumerate(self.vertices):
            if a.code == code:
                return i
        return -1

    def agregar_vertice(self, airport):
        n = len(self.vertices)
        self.vertices.append(airport)
        self.adyacencia.append([None] * (n + 1))
        for fila in self.adyacencia[:-1]:
            fila.append(None)

    def agregar_arista(self, code1, code2):
        i1, i2 = self._indice(code1), self._indice(code2)
        if i1 == -1 or i2 == -1 or i1 == i2:
            return
        if self.adyacencia[i1][i2] is not None:
            return
        dist = haversine(
            self.vertices[i1].lat, self.vertices[i1].lon,
            self.vertices[i2].lat, self.vertices[i2].lon
        )
        self.adyacencia[i1][i2] = dist
        self.adyacencia[i2][i1] = dist

    def obtener_vecinos(self, code):
        idx = self._indice(code)
        if idx == -1:
            return []
        return [
            (self.vertices[j], self.adyacencia[idx][j])
            for j in range(len(self.vertices))
            if self.adyacencia[idx][j] is not None
        ]

    def num_vertices(self):
        return len(self.vertices)

    def num_aristas(self):
        count = 0
        n = len(self.vertices)
        for i in range(n):
            for j in range(i + 1, n):
                if self.adyacencia[i][j] is not None:
                    count += 1
        return count

    def grado(self, code):
        return len(self.obtener_vecinos(code))

    def obtener_aristas(self):
        """Retorna lista de (distancia, code1, code2) sin duplicados."""
        aristas = []
        n = len(self.vertices)
        for i in range(n):
            for j in range(i + 1, n):
                if self.adyacencia[i][j] is not None:
                    aristas.append((
                        self.adyacencia[i][j],
                        self.vertices[i].code,
                        self.vertices[j].code
                    ))
        return aristas

    def airport_by_code(self, code):
        idx = self._indice(code)
        return self.vertices[idx] if idx != -1 else None

    def to_dict_grafo(self):
        """Devuelve {code: [vecinos_codes]} para los algoritmos."""
        grafo = {}
        for a in self.vertices:
            grafo[a.code] = [v.code for v, _ in self.obtener_vecinos(a.code)]
        return grafo


# ============================================================
# UNION-FIND (para Kruskal)
# ============================================================
class UnionFind:
    def __init__(self, elementos):
        self.padre = {x: x for x in elementos}
        self.rango  = {x: 0 for x in elementos}

    def encontrar(self, x):
        if self.padre[x] != x:
            self.padre[x] = self.encontrar(self.padre[x])
        return self.padre[x]

    def unir(self, x, y):
        rx, ry = self.encontrar(x), self.encontrar(y)
        if rx == ry:
            return False
        if self.rango[rx] < self.rango[ry]:
            self.padre[rx] = ry
        elif self.rango[rx] > self.rango[ry]:
            self.padre[ry] = rx
        else:
            self.padre[ry] = rx
            self.rango[rx] += 1
        return True


# ============================================================
# ANALIZADOR DE GRAFO
# ============================================================
class GrafoAnalizador:

    # --- 1. DFS – Conexidad y componentes ---
    def es_conexo(self, grafo):
        visitados   = set()
        componentes = []
        for vertice in grafo:
            if vertice not in visitados:
                comp  = []
                pila  = [vertice]
                visitados.add(vertice)
                while pila:
                    actual = pila.pop()
                    comp.append(actual)
                    for vecino in grafo[actual]:
                        if vecino not in visitados:
                            visitados.add(vecino)
                            pila.append(vecino)
                componentes.append(comp)
        num = len(componentes)
        return num == 1, num, [len(c) for c in componentes], componentes

    # --- 2. BFS – Bipartito ---
    def es_bipartito(self, grafo, vertices=None):
        if vertices is None:
            vertices = list(grafo.keys())
        color = {}
        for inicio in vertices:
            if inicio in color:
                continue
            cola = deque([inicio])
            color[inicio] = 0
            while cola:
                actual = cola.popleft()
                for vecino in grafo[actual]:
                    if vecino not in color:
                        color[vecino] = 1 - color[actual]
                        cola.append(vecino)
                    elif color[vecino] == color[actual]:
                        return False
        return True

    # --- 3. Kruskal – MST ---
    def kruskal_mst(self, vertices, aristas):
        uf = UnionFind(vertices)
        aristas_ord = sorted(aristas, key=lambda x: x[0])
        peso_total, mst = 0, []
        for peso, u, v in aristas_ord:
            if uf.unir(u, v):
                mst.append((u, v, peso))
                peso_total += peso
                if len(mst) == len(vertices) - 1:
                    break
        return peso_total, mst

    def mst_por_componente(self, grafo, aristas):
        _, num_comp, _, componentes = self.es_conexo(grafo)
        resultados = []
        for i, comp in enumerate(componentes, 1):
            comp_set = set(comp)
            aristas_c = [(p, u, v) for p, u, v in aristas if u in comp_set and v in comp_set]
            peso, mst = self.kruskal_mst(comp, aristas_c)
            resultados.append({
                'componente': i,
                'vertices':   comp,
                'peso_mst':   peso,
                'aristas_mst': mst
            })
        return resultados


# ============================================================
# CARGADOR DE CSV
# ============================================================
class FlightLoader:
    """Lee el CSV y construye el grafo."""

    def cargar(self, ruta):
        grafo = Graph()
        aeropuertos = {}   # code -> Airport
        try:
            with open(ruta, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for fila in reader:
                    # Aeropuerto origen
                    cs = fila['Source Airport Code'].strip()
                    if cs and cs not in aeropuertos:
                        a = Airport(
                            cs,
                            fila['Source Airport Name'].strip(),
                            fila['Source Airport City'].strip(),
                            fila['Source Airport Country'].strip(),
                            fila['Source Airport Latitude'].strip() or '0',
                            fila['Source Airport Longitude'].strip() or '0',
                        )
                        aeropuertos[cs] = a
                        grafo.agregar_vertice(a)

                    # Aeropuerto destino
                    cd = fila['Destination Airport Code'].strip()
                    if cd and cd not in aeropuertos:
                        a = Airport(
                            cd,
                            fila['Destination Airport Name'].strip(),
                            fila['Destination Airport City'].strip(),
                            fila['Destination Airport Country'].strip(),
                            fila['Destination Airport Latitude'].strip() or '0',
                            fila['Destination Airport Longitude'].strip() or '0',
                        )
                        aeropuertos[cd] = a
                        grafo.agregar_vertice(a)

                    # Arista
                    if cs and cd:
                        grafo.agregar_arista(cs, cd)

            return True, grafo, f"Dataset cargado: {grafo.num_vertices()} aeropuertos, {grafo.num_aristas()} rutas"
        except Exception as e:
            return False, None, f"Error al cargar: {e}"


# ============================================================
# VISUALIZADOR DEL GRAFO (Canvas)
# ============================================================
class VisualizadorGrafo(tk.Canvas):
    """
    Dibuja el grafo como un diagrama circular.
    Cada aeropuerto es un nodo; las aristas son las rutas.
    Solo muestra los nodos de una componente a la vez para no saturar.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="white", highlightthickness=1, **kwargs)
        self.grafo         = None
        self.nodo_resaltado = None
        self.posiciones    = {}    # code -> (x, y)
        self.config(scrollregion=(0, 0, 2000, 2000))
        self.bind("<ButtonPress-1>",   self._iniciar_drag)
        self.bind("<B1-Motion>",       self._drag)
        self._drag_inicio  = None

    # --- Arrastre del canvas ---
    def _iniciar_drag(self, event):
        self._drag_inicio = (event.x, event.y)

    def _drag(self, event):
        if self._drag_inicio:
            dx = event.x - self._drag_inicio[0]
            dy = event.y - self._drag_inicio[1]
            self.xview_scroll(-dx // 5, "units")
            self.yview_scroll(-dy // 5, "units")
            self._drag_inicio = (event.x, event.y)

    # --- Dibujo principal ---
    def dibujar_subgrafo(self, grafo, nodos_a_mostrar, nodo_resaltado=None, max_nodos=80):
        self.delete("all")
        self.grafo          = grafo
        self.nodo_resaltado = nodo_resaltado
        self.posiciones     = {}

        if not nodos_a_mostrar:
            self.create_text(400, 300, text="Sin nodos para mostrar",
                             font=("Arial", 14), fill="#555")
            return

        # Limitar cantidad para no saturar la pantalla
        muestra = nodos_a_mostrar[:max_nodos]
        n       = len(muestra)

        cx, cy, radio = 600, 500, min(400, 60 * n // 6 + 150)

        for i, code in enumerate(muestra):
            angulo = 2 * math.pi * i / n
            x = cx + radio * math.cos(angulo)
            y = cy + radio * math.sin(angulo)
            self.posiciones[code] = (x, y)

        # Dibujar aristas
        for code in muestra:
            x1, y1 = self.posiciones[code]
            for vecino, dist in grafo.obtener_vecinos(code):
                if vecino.code in self.posiciones and vecino.code > code:
                    x2, y2 = self.posiciones[vecino.code]
                    self.create_line(x1, y1, x2, y2, fill="#b0bec5", width=1)

        # Dibujar nodos
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

        # Leyenda
        self._dibujar_leyenda(n, len(nodos_a_mostrar))

    def _dibujar_leyenda(self, mostrados, total):
        self.create_rectangle(10, 10, 260, 100, fill=COLOR_PANEL, outline=COLOR_BORDE)
        self.create_text(135, 25, text="Leyenda de nodos", fill=COLOR_TEXTO,
                         font=("Arial", 9, "bold"))
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
# VENTANA DE INFO DE AEROPUERTO
# ============================================================
class VentanaInfoAeropuerto(tk.Toplevel):
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

        # Pestaña 1: Datos
        tab1 = tk.Frame(notebook, bg=COLOR_TARJETA)
        notebook.add(tab1, text="Datos del Aeropuerto")

        vecinos = grafo.obtener_vecinos(airport.code)
        campos = [
            ("Código IATA:",   airport.code),
            ("Nombre:",        airport.name),
            ("Ciudad:",        airport.city),
            ("País:",          airport.country),
            ("Latitud:",       f"{airport.lat:.6f}"),
            ("Longitud:",      f"{airport.lon:.6f}"),
            ("Rutas directas:", str(len(vecinos))),
        ]
        for i, (etq, val) in enumerate(campos):
            fila = tk.Frame(tab1, bg=COLOR_TARJETA if i % 2 == 0 else COLOR_PANEL)
            fila.pack(fill="x")
            tk.Label(fila, text=etq, width=18, anchor="e",
                     bg=fila["bg"], fg=COLOR_TEXTO_SEC).pack(side="left", padx=5, pady=3)
            tk.Label(fila, text=val, anchor="w",
                     bg=fila["bg"], fg=COLOR_TEXTO).pack(side="left", padx=5, pady=3)

        # Pestaña 2: Vecinos
        tab2 = tk.Frame(notebook, bg=COLOR_TARJETA)
        notebook.add(tab2, text=f"Rutas Directas ({len(vecinos)})")

        cols = ("code", "city", "country", "dist_km")
        tabla = ttk.Treeview(tab2, columns=cols, show="headings", height=10)
        tabla.heading("code",    text="Código")
        tabla.heading("city",    text="Ciudad")
        tabla.heading("country", text="País")
        tabla.heading("dist_km", text="Dist. (km)")
        tabla.column("code",    width=70,  anchor="center")
        tabla.column("city",    width=130, anchor="w")
        tabla.column("country", width=130, anchor="w")
        tabla.column("dist_km", width=90,  anchor="center")
        sb = ttk.Scrollbar(tab2, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=sb.set)
        tabla.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        for v, d in sorted(vecinos, key=lambda x: x[1]):
            tabla.insert("", "end", values=(v.code, v.city, v.country, f"{d:.1f}"))

        tk.Button(frame, text="Cerrar", command=self.destroy,
                  bg=COLOR_BOTON, fg="white", width=15).pack(pady=10)


# ============================================================
# VENTANA DE RESULTADOS GENERALES
# ============================================================
class VentanaResultados(tk.Toplevel):
    def __init__(self, parent, grafo, aeropuertos, titulo="Resultados"):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("720x420")
        self.configure(bg=COLOR_PANEL)
        self.grafo = grafo
        self.aeropuertos = {a.code: a for a in aeropuertos}

        header = tk.Frame(self, bg=COLOR_PANEL)
        header.pack(fill="x", padx=10, pady=8)
        tk.Label(header, text=titulo, font=("Arial", 11, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON).pack(side="left")
        tk.Label(header, text=f"  ({len(aeropuertos)} resultados)",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC).pack(side="left")

        cols = ("code", "name", "city", "country", "grado")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        self.tabla.heading("code",    text="Código")
        self.tabla.heading("name",    text="Nombre")
        self.tabla.heading("city",    text="Ciudad")
        self.tabla.heading("country", text="País")
        self.tabla.heading("grado",   text="Rutas")
        self.tabla.column("code",    width=70,  anchor="center")
        self.tabla.column("name",    width=200, anchor="w")
        self.tabla.column("city",    width=120, anchor="w")
        self.tabla.column("country", width=120, anchor="w")
        self.tabla.column("grado",   width=70,  anchor="center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        self.tabla.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        sb.pack(side="left", fill="y", pady=10, padx=(0, 10))

        for a in aeropuertos:
            self.tabla.insert("", "end", iid=a.code, values=(
                a.code, a.name[:35], a.city, a.country,
                grafo.grado(a.code)
            ))

        self.tabla.bind("<Double-1>", self._mostrar_info)
        tk.Label(self, text="Doble clic para ver detalles del aeropuerto",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC, font=("Arial", 9)).pack(pady=(0, 8))

    def _mostrar_info(self, event):
        sel = self.tabla.selection()
        if sel and sel[0] in self.aeropuertos:
            VentanaInfoAeropuerto(self, self.aeropuertos[sel[0]], self.grafo)


# ============================================================
# VENTANA MST
# ============================================================
class VentanaMST(tk.Toplevel):
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
            for u, v, p in r['aristas_mst'][:30]:  # limitar a 30 por componente
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
# APLICACIÓN PRINCIPAL
# ============================================================
class AplicacionGrafo(tk.Tk):
    """
    Ventana principal del Laboratorio 2 - Grafos de Vuelos.
    Misma estructura visual que Lab1:
      - Panel izquierdo:  controles (cargar CSV, buscar aeropuerto)
      - Panel central:    visualización del grafo (canvas)
      - Panel derecho:    análisis (conexidad, bipartito, MST, log)
    """

    def __init__(self):
        super().__init__()
        self.title("Laboratorio 2 - Grafo de Aeropuertos (Vuelos)")
        self.geometry("1300x780")
        self.configure(bg=COLOR_FONDO)

        self.grafo     = Graph()
        self.analizador = GrafoAnalizador()
        self.loader    = FlightLoader()

        # Componentes calculadas (para navegación)
        self._componentes    = []
        self._comp_idx       = 0
        self._comp_dict      = {}  # code -> componente idx

        self._crear_menu()
        self._crear_panel_izquierdo()
        self._crear_panel_central()
        self._crear_panel_derecho()
        self._log("Sistema iniciado. Cargue el archivo flights_final.csv para comenzar.")

    # --------------------------------------------------------
    # MENÚ
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # PANEL IZQUIERDO
    # --------------------------------------------------------
    def _crear_panel_izquierdo(self):
        panel = tk.Frame(self, bg=COLOR_PANEL, width=310)
        panel.pack(side="left", fill="y", padx=10, pady=10)
        panel.pack_propagate(False)

        tk.Label(panel, text="Operaciones", font=("Arial", 12, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON).pack(pady=10)

        # --- Dataset ---
        self._seccion(panel, "Dataset")
        tk.Button(panel, text="Cargar CSV de Vuelos", command=self._cargar_csv,
                  bg=COLOR_BOTON, fg="white", width=28).pack(pady=5)
        self.lbl_dataset = tk.Label(panel, text="Sin dataset cargado",
                                    bg=COLOR_PANEL, fg=COLOR_TEXTO_SEC, wraplength=290)
        self.lbl_dataset.pack(pady=5)

        # --- Buscar aeropuerto ---
        self._seccion(panel, "Buscar Aeropuerto")
        tk.Label(panel, text="Código IATA (ej. BOG, MIA):",
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(anchor="w", padx=20)
        self.entry_buscar = tk.Entry(panel, width=30)
        self.entry_buscar.pack(pady=5)
        tk.Button(panel, text="Buscar y Resaltar", command=self._buscar_aeropuerto,
                  bg=COLOR_EXITO, fg="white", width=28).pack(pady=3)
        tk.Button(panel, text="Ver Info Completa", command=self._ver_info_aeropuerto,
                  bg=COLOR_BOTON, fg="white", width=28).pack(pady=3)

        # --- Navegación de componentes ---
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

        # --- Aleatorio ---
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

    # --------------------------------------------------------
    # PANEL CENTRAL (Canvas)
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # PANEL DERECHO
    # --------------------------------------------------------
    def _crear_panel_derecho(self):
        panel = tk.Frame(self, bg=COLOR_PANEL, width=310)
        panel.pack(side="right", fill="y", padx=10, pady=10)
        panel.pack_propagate(False)

        tk.Label(panel, text="Análisis del Grafo", font=("Arial", 12, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_ALERTA).pack(pady=10)

        # --- Conexidad ---
        self._seccion(panel, "1. Conexidad (DFS)")
        tk.Button(panel, text="Analizar Conexidad", command=self._analizar_conexidad,
                  bg=COLOR_BOTON, fg="white", width=32).pack(pady=5)

        # --- Bipartito ---
        self._seccion(panel, "2. Bipartito (BFS)")
        tk.Button(panel, text="Verificar Bipartito (comp. mayor)",
                  command=self._analizar_bipartito, bg=COLOR_BOTON, fg="white",
                  width=32).pack(pady=5)

        # --- MST ---
        self._seccion(panel, "3. MST – Kruskal")
        tk.Button(panel, text="Calcular MST por Componente",
                  command=self._calcular_mst, bg=COLOR_ALERTA, fg="white",
                  width=32).pack(pady=5)

        # --- Estadísticas ---
        self._seccion(panel, "Estadísticas del Grafo")
        tk.Button(panel, text="Mostrar Top 10 Hubs (más rutas)",
                  command=self._top_hubs, bg="#9b59b6", fg="white",
                  width=32).pack(pady=4)
        tk.Button(panel, text="Mostrar todos los aeropuertos",
                  command=self._mostrar_todos, bg="#9b59b6", fg="white",
                  width=32).pack(pady=4)

        # --- Log ---
        self._seccion(panel, "Registro de Operaciones")
        self.txt_log = scrolledtext.ScrolledText(panel, width=37, height=14,
                                                  bg=COLOR_TARJETA, fg=COLOR_TEXTO)
        self.txt_log.pack(padx=5, pady=5)
        self.txt_log.configure(state="disabled")

    # --------------------------------------------------------
    # UTILIDADES UI
    # --------------------------------------------------------
    def _seccion(self, parent, titulo):
        tk.Frame(parent, bg=COLOR_BORDE, height=2).pack(fill="x", padx=10, pady=12)
        tk.Label(parent, text=titulo, font=("Arial", 10, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_BOTON).pack(anchor="w", padx=10)

    def _log(self, mensaje, tipo="info"):
        self.txt_log.configure(state="normal")
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        tag_map = {"error": COLOR_ERROR, "exito": COLOR_EXITO, "alerta": COLOR_ALERTA}
        color = tag_map.get(tipo, COLOR_TEXTO)
        self.txt_log.tag_configure(tipo, foreground=color)
        self.txt_log.insert("end", f"[{hora}] {mensaje}\n", tipo)
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _actualizar_contador(self):
        self.lbl_contador.configure(
            text=f"Vértices: {self.grafo.num_vertices()}  |  Aristas: {self.grafo.num_aristas()}"
        )

    def _actualizar_vista(self, nodos=None, resaltar=None):
        """Redibuja el canvas con la lista de códigos dada."""
        if nodos is None:
            # Mostrar la primera componente por defecto
            if self._componentes:
                nodos = self._componentes[self._comp_idx]
            else:
                nodos = [a.code for a in self.grafo.vertices[:80]]
        self.canvas.dibujar_subgrafo(self.grafo, nodos, nodo_resaltado=resaltar)

    def _recalcular_componentes(self):
        grafo_dict = self.grafo.to_dict_grafo()
        _, _, _, comps = self.analizador.es_conexo(grafo_dict)
        # Ordenar por tamaño descendente
        comps.sort(key=len, reverse=True)
        self._componentes = comps
        self._comp_idx    = 0
        self._comp_dict   = {}
        for idx, comp in enumerate(comps):
            for code in comp:
                self._comp_dict[code] = idx
        self.lbl_comp.configure(text=f"1/{len(comps)}")

    # --------------------------------------------------------
    # ACCIONES
    # --------------------------------------------------------
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
            nombre = os.path.basename(ruta)
            self.lbl_dataset.configure(text=f"{nombre}\n{mensaje}")
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
        self._log(f"Encontrado: {a.name} ({a.city}, {a.country}) — {self.grafo.grado(code)} rutas", "exito")

        # Mostrar la componente que contiene este aeropuerto
        idx = self._comp_dict.get(code, 0)
        self._comp_idx = idx
        self.lbl_comp.configure(text=f"{idx+1}/{len(self._componentes)}")
        self._actualizar_vista(nodos=self._componentes[idx], resaltar=code)

    def _ver_info_aeropuerto(self):
        code = self.entry_buscar.get().strip().upper()
        a = self.grafo.airport_by_code(code)
        if not a:
            self._log(f"Código '{code}' no encontrado", "error")
            return
        VentanaInfoAeropuerto(self, a, self.grafo)

    # --- Navegación de componentes ---
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
        comp = self._componentes[self._comp_idx]
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
        muestra = random.sample([a.code for a in self.grafo.vertices],
                                 min(n, self.grafo.num_vertices()))
        self._log(f"Mostrando {len(muestra)} aeropuertos aleatorios")
        self._actualizar_vista(nodos=muestra)

    # --- Análisis ---
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
        mayor = comps[tamaños.index(max(tamaños))]
        es_bip = self.analizador.es_bipartito(grafo_d, mayor)
        if es_bip:
            self._log(f"Componente mayor ({len(mayor)} nodos) ES BIPARTITA", "exito")
        else:
            self._log(f"Componente mayor ({len(mayor)} nodos) NO ES BIPARTITA", "alerta")
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
        grafo_d  = self.grafo.to_dict_grafo()
        aristas  = self.grafo.obtener_aristas()
        resultados = self.analizador.mst_por_componente(grafo_d, aristas)
        peso_total = sum(r['peso_mst'] for r in resultados)
        self._log(f"MST calculado: {len(resultados)} componentes — Peso total: {peso_total:,.1f} km", "exito")
        VentanaMST(self, resultados)

    def _top_hubs(self):
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        aeropuertos_ord = sorted(
            self.grafo.vertices,
            key=lambda a: self.grafo.grado(a.code),
            reverse=True
        )[:10]
        self._log(f"Top 10 hubs:")
        for a in aeropuertos_ord:
            self._log(f"  {a.code}: {self.grafo.grado(a.code)} rutas — {a.city}")
        VentanaResultados(self, self.grafo, aeropuertos_ord, "Top 10 Hubs (más rutas directas)")
        self._actualizar_vista(nodos=[a.code for a in aeropuertos_ord])

    def _mostrar_todos(self):
        if not self.grafo.vertices:
            self._log("Cargue un dataset primero", "error")
            return
        VentanaResultados(self, self.grafo, self.grafo.vertices, "Todos los Aeropuertos")

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