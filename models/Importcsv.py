import csv
from models.airport import Airport
from models.graph import Graph

# Ruta del archivo CSV con los datos de vuelos
# La definimos como constante global para poder cambiarla facilmente
# sin tener que buscarla dentro del codigo
CSV_PATH = "data/flights_final.csv"

def cargar_grafo(csv_path=CSV_PATH):
    """
    Leemos el archivo CSV de vuelos y construimos el grafo de aeropuertos.
    Hacemos dos pasadas sobre los datos:
      - Primer recorrido: registramos todos los aeropuertos unicos como vertices
      - Segundo recorrido: conectamos los aeropuertos con aristas ponderadas por distancia
    Retornamos el grafo ya construido y listo para usar.
    """
    grafo = Graph()

    # Usamos un conjunto para rastrear que codigos ya agregamos como vertice
    # Esto nos permite verificar duplicados en O(1) sin recorrer el grafo
    codigos_agregados = set()

    # Abrimos el archivo y cargamos todas las filas en memoria
    # Lo hacemos asi para poder hacer dos pasadas sin releer el archivo del disco
    with open(csv_path, newline='', encoding='utf-8') as archivo:
        lector = csv.reader(archivo)
        next(lector)  # Saltamos el encabezado (primera fila con nombres de columnas)
        filas = list(lector)

    # Primer recorrido: agregamos todos los vertices unicos

    # Recorremos cada fila y extraemos los datos de origen y destino
    # Solo agregamos un aeropuerto si su codigo no lo hemos visto antes
    for fila in filas:
        # Los indices corresponden al orden de columnas del CSV:
        # 0: Source Code, 1: Source Name, 2: Source City,    3: Source Country
        # 4: Source Lat,  5: Source Lon,  6: Dest Code,      7: Dest Name
        # 8: Dest City,   9: Dest Country, 10: Dest Lat,     11: Dest Lon

        code_src = fila[0].strip()
        if code_src not in codigos_agregados:
            aeropuerto_origen = Airport(
                code    = code_src,
                name    = fila[1].strip(),
                city    = fila[2].strip(),
                country = fila[3].strip(),
                lat     = float(fila[4]),
                lon     = float(fila[5])
            )
            grafo.agregar_vertice(aeropuerto_origen)
            codigos_agregados.add(code_src)

        code_dst = fila[6].strip()
        if code_dst not in codigos_agregados:
            aeropuerto_destino = Airport(
                code    = code_dst,
                name    = fila[7].strip(),
                city    = fila[8].strip(),
                country = fila[9].strip(),
                lat     = float(fila[10]),
                lon     = float(fila[11])
            )
            grafo.agregar_vertice(aeropuerto_destino)
            codigos_agregados.add(code_dst)

    print(f"[INFO] Vertices cargados: {len(grafo.vertices)} aeropuertos unicos")

    # Segundo recorrido: Agregamos todas las aristas
    
    # Hacemos esta pasada despues de tener todos los vertices cargados
    # para garantizar que agregar_arista siempre encuentre ambos extremos
    # El metodo agregar_arista ya ignora conexiones duplicadas internamente
    for fila in filas:
        code_src = fila[0].strip()
        code_dst = fila[6].strip()
        grafo.agregar_arista(code_src, code_dst)

    print(f"[INFO] Grafo construido exitosamente.")

    return grafo
