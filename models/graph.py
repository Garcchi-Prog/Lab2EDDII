from utils.haversine import Haversine

class Graph:
    def __init__(self):
        # Almacenamos la lista de los vertices y de las aristas
        self.vertices = []
        self.adyacencia = []

    def agregar_vertice(self, airport):
        # Se  agrega un nuevo aeropuerto al grafo
        self.vertices.append(airport)
        
        # Agrandar la matriz de adyacencia
        # Agregar una nueva fila para el nuevo vértice
        new_row = [None] * len(self.vertices)
        self.adyacencia.append(new_row)
        
        # Agregar una nueva columna a todas las filas existentes
        for fila in self.adyacencia:
            fila.append(None)
    
    def buscar_indice(self, code):
        #Se Busca el índice de un aeropuerto por su códig
        for i, airport in enumerate(self.vertices):
            if airport.code == code:
                return i
        return -1
    
    def agregar_arista(self, code1, code2):
        #Se agrega una conexión entre dos aeropuertos
        id1 = self.buscar_indice(code1)
        id2 = self.buscar_indice(code2)
        if id1 == -1 or id2 == -1:
            return
        
        if self.adyacencia[id1][id2] is not None:
            return
        
        
        # Calcular distancia con Haversine
        airport1 = self.vertices[id1]
        airport2 = self.vertices[id2]
        distancia = Haversine(airport1.lat, airport1.lon, airport2.lat, airport2.lon)
        
        #Verificamos adicionalmente si la matriz es simétrica
        self.adyacencia[id1][id2] = distancia
        self.adyacencia[id2][id1] = distancia
    
    def obtener_vecinos(self, code):
        #Devuolvemoslos aeropuertos conectados a uno dado
        id = self.buscar_indice(code)
        if id == -1:
            return []
        
        vecinos = []
        for i in range(len(self.vertices)):
            if self.adyacencia[id][i] is not None:
                vecinos.append((self.vertices[i], self.adyacencia[id][i]))
        return vecinos

    