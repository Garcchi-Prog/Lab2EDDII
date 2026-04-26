import csv
from models.airport import Airport
from models.graph import Graph

# Ruta por defecto del dataset
CSV_PATH = "data/flights_final.csv"


class FlightLoader:
    """
    Lee el archivo CSV de vuelos y construye el grafo de aeropuertos.

    Hace dos pasadas sobre los datos:
      - Primera:  registra todos los aeropuertos únicos como vértices.
      - Segunda:  conecta los aeropuertos con aristas ponderadas por distancia.
    """

    def cargar(self, ruta=CSV_PATH):
        """
        Carga el CSV y retorna (exito, grafo, mensaje).

        Parámetros:
            ruta: ruta al archivo flights_final.csv

        Retorna:
            (True, Graph, str_info)  si se cargó correctamente.
            (False, None, str_error) si ocurrió un error.
        """
        grafo = Graph()
        aeropuertos = {}  # code -> Airport  (para evitar duplicados en O(1))

        try:
            with open(ruta, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for fila in reader:
                    # ---- Aeropuerto origen ----
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

                    # ---- Aeropuerto destino ----
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

                    # ---- Arista ----
                    if cs and cd:
                        grafo.agregar_arista(cs, cd)

            msg = (f"Dataset cargado: {grafo.num_vertices()} aeropuertos, "
                   f"{grafo.num_aristas()} rutas")
            print(f"[INFO] {msg}")
            return True, grafo, msg

        except Exception as e:
            msg = f"Error al cargar '{ruta}': {e}"
            print(f"[ERROR] {msg}")
            return False, None, msg
