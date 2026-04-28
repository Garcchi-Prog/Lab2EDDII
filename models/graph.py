from utils.haversine import haversine


class Graph:
    
    ##    Grafo simple, no dirigido y ponderado representado mediante
    ##    una matriz de adyacencia. Cada vértice es un objeto Airport
    ##    y el peso de cada arista es la distancia Haversine en km.
    

    def __init__(self):
        self.vertices   = []   # lista de Aeropuetos
        self.adyacencia = []   # matriz NxN; None = sin arista

    # --------------------------------------------------------
    # ÍNDICE INTERNO
    # --------------------------------------------------------
    def _indice(self, code):
        ##    Retorna el índice del aeropuerto con ese código en la lista
        ##    de vértices, recorriendo la lista de forma lineal O(n).
        ##    Retorna -1 si el código no existe.
        
        for i, a in enumerate(self.vertices):
            if a.code == code:
                return i
        return -1

    # --------------------------------------------------------
    # VÉRTICES Y ARISTAS
    # --------------------------------------------------------
    def agregar_vertice(self, airport):
        ##    Agrega un aeropuerto como nuevo vértice y expande la matriz.

        n = len(self.vertices)
        self.vertices.append(airport)
        # Nueva fila para el vértice agregado
        self.adyacencia.append([None] * (n + 1))
        # Nueva columna en todas las filas anteriores
        for fila in self.adyacencia[:-1]:
            fila.append(None)

    def agregar_arista(self, code1, code2):
        ##    Conecta dos aeropuertos con una arista ponderada por distancia Haversine.
        ##    Ignora bucles y aristas duplicadas.
        ##    La búsqueda de índices es O(1) gracias a _indices.
        
        i1, i2 = self._indice(code1), self._indice(code2)
        if i1 == -1 or i2 == -1 or i1 == i2:
            return
        if self.adyacencia[i1][i2] is not None:
            return
        dist = haversine(
            self.vertices[i1].lat, self.vertices[i1].lon,
            self.vertices[i2].lat, self.vertices[i2].lon
        )
        # Grafo no dirigido: la matriz es simétrica
        self.adyacencia[i1][i2] = dist
        self.adyacencia[i2][i1] = dist

    # --------------------------------------------------------
    # CONSULTAS
    # --------------------------------------------------------
    def obtener_vecinos(self, code):
        """Retorna lista de (Airport, distancia_km) para el aeropuerto dado."""
        idx = self._indice(code)
        if idx == -1:
            return []
        return [
            (self.vertices[j], self.adyacencia[idx][j])
            for j in range(len(self.vertices))
            if self.adyacencia[idx][j] is not None
        ]

    def num_vertices(self):
        """Cantidad total de vértices en el grafo."""
        return len(self.vertices)

    def num_aristas(self):
        """Cantidad total de aristas (sin duplicados)."""
        n = len(self.vertices)
        return sum(
            1 for i in range(n)
              for j in range(i + 1, n)
              if self.adyacencia[i][j] is not None
        )

    def grado(self, code):
        """Número de rutas directas del aeropuerto."""
        return len(self.obtener_vecinos(code))

    def obtener_aristas(self):
        """Retorna lista de (distancia_km, code1, code2) sin duplicados."""
        n = len(self.vertices)
        return [
            (self.adyacencia[i][j], self.vertices[i].code, self.vertices[j].code)
            for i in range(n)
            for j in range(i + 1, n)
            if self.adyacencia[i][j] is not None
        ]

    def airport_by_code(self, code):
        """Retorna el objeto Airport del código dado, o None si no existe."""
        idx = self._indice(code)
        return self.vertices[idx] if idx != -1 else None

    def to_dict_grafo(self):
        """Devuelve {code: [vecinos_codes]} para ser usado por GrafoAnalizador."""
        return {
            a.code: [v.code for v, _ in self.obtener_vecinos(a.code)]
            for a in self.vertices
        }

    def to_dict_pesos(self):
        """Devuelve {code: [(vecino_code, distancia_km), ...]} para Dijkstra."""
        return {
            a.code: [(v.code, d) for v, d in self.obtener_vecinos(a.code)]
            for a in self.vertices
        }
