from collections import deque


# ============================================================
# UNION-FIND (para Kruskal)
# ============================================================

class UnionFind:
    ##   Estructura de conjuntos disjuntos con compresión de camino
    ##   y unión por rango. Se usa en el algoritmo de Kruskal para
    ##   detectar ciclos al construir el MST.

    def __init__(self, elementos):
        self.padre = {x: x for x in elementos}
        self.rango  = {x: 0 for x in elementos}

    def encontrar(self, x):
        ##   Encuentra la raíz del conjunto de x con compresión de camino.
        if self.padre[x] != x:
            self.padre[x] = self.encontrar(self.padre[x])
        return self.padre[x]

    def unir(self, x, y):
        ##    Une los conjuntos de x e y. 
        ##    Retorna Verdadero si se unieron, Falso si ya pertenecían al mismo
        ##    conjunto (es decir, agregar la arista formaría un ciclo).
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
# ANALIZADOR PRINCIPAL
# ============================================================

class GrafoAnalizador:
    ##    Contiene los algoritmos de análisis del grafo:
    ##    1. DFS  → conexidad y componentes conexas.
    ##    2. BFS  → verificación de grafo bipartito.
    ##    3. Kruskal → árbol de expansión mínima (MST).
    ##    No usa librerías externas para ninguno de estos algoritmos.
    
    ## --------------------------------------------------------
    ## 1. DFS – Conexidad y componentes
    ## --------------------------------------------------------

    def es_conexo(self, grafo):
        ##    Determina si el grafo es conexo usando DFS iterativo.

        ##    Este es el parámetro:
        ##        grafo: dict {código: [lista de códigos vecinos]}
        
        visitados   = set()
        componentes = []

        for vertice in grafo:
            if vertice not in visitados:
                comp = []
                pila = [vertice]
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

        ##    Esto es lo que retorna:
        ##        (bool_conexo, num_componentes, lista_tamaños, lista_componentes)
        
        return num == 1, num, [len(c) for c in componentes], componentes

    ## --------------------------------------------------------
    ## 2. BFS – Bipartito
    ## --------------------------------------------------------

    def es_bipartito(self, grafo, vertices = None):
        ##    Verifica si el subgrafo inducido por "vertices" es bipartito.
        ##    Usa BFS con coloreo de dos colores (0 y 1).

        ##    Estos son los parámetros:
        ##        grafo:    dict {código: [vecinos]}
        ##        vertices: lista de códigos a revisar (None == todos)

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

        ##    Esto es lo que retorna:
        ##        Verdadero si es bipartito, Falso en caso contrario.   

                        return False  ##    Ciclo de longitud impar → no bipartito
        return True

    ## --------------------------------------------------------
    ## 3. Kruskal – MST
    ## --------------------------------------------------------

    def kruskal_mst(self, vertices, aristas):
        ##    Calcula el árbol de expansión mínima usando el algoritmo de Kruskal.

        ##    Estos son los parámetros:
        ##        vertices: lista de códigos de aeropuertos (nodos del subgrafo)
        ##        aristas:  lista de (peso, code1, code2)

        uf = UnionFind(vertices)
        aristas_ord = sorted(aristas, key=lambda x: x[0])
        peso_total, mst = 0, []

        for peso, u, v in aristas_ord:
            if uf.unir(u, v):
                mst.append((u, v, peso))
                peso_total += peso
                # El MST de N vértices tiene exactamente N-1 aristas
                if len(mst) == len(vertices) - 1:
                    break

        ##    Esto es lo que retorna:
        ##        (peso_total_km, lista de (code1, code2, peso))

        return peso_total, mst

    def mst_por_componente(self, grafo, aristas):
        ##    Calcula el MST de cada componente conexa del grafo.
        
        _, num_comp, _, componentes = self.es_conexo(grafo)
        resultados = []

        for i, comp in enumerate(componentes, 1):
            comp_set  = set(comp)
            # Filtramos solo las aristas que pertenecen a esta componente
            aristas_c = [(p, u, v) for p, u, v in aristas
                         if u in comp_set and v in comp_set]
            peso, mst = self.kruskal_mst(comp, aristas_c)
            resultados.append({
                'componente':  i,
                'vertices':    comp,
                'peso_mst':    peso,
                'aristas_mst': mst
            })

        ##    Este metodo retorna lista de dicts con:
        ##        'componente', 'vertices', 'peso_mst', 'aristas_mst'

        return resultados

    ## --------------------------------------------------------
    ## 4. Dijkstra – Caminos mínimos
    ## --------------------------------------------------------

    def dijkstra(self, grafo_pesos, origen):
        ##    Calcula los caminos mínimos desde el "origen" a todos los demás
        ##    vértices usando el algoritmo de Dijkstra con cola de prioridad
        ##    implementada manualmente (sin heapq).

        ##    Estos son los parámetros:
        ##        grafo_pesos: dict {code: [(vecino_code, peso), ...]}
        ##        origen:      código del aeropuerto de origen
        
        distancias = {v: float('inf') for v in grafo_pesos}
        distancias[origen] = 0.0
        previos   = {v: None for v in grafo_pesos}

        ##    Cola de prioridad manual: lista de (distancia, vertice)
        cola     = [(0.0, origen)]
        visitados = set()

        while cola:
            ##    Extraemos el nodo con menor distancia acumulada
            cola.sort(key=lambda x: x[0])
            dist_actual, actual = cola.pop(0)

            if actual in visitados:
                continue
            visitados.add(actual)

            # Relajamos cada arista del nodo actual
            for vecino, peso in grafo_pesos[actual]:
                if vecino in visitados:
                    continue
                nueva_dist = dist_actual + peso
                if nueva_dist < distancias[vecino]:
                    distancias[vecino] = nueva_dist
                    previos[vecino]    = actual
                    cola.append((nueva_dist, vecino))

        ##    Esto es lo que retorna:
        ##        distancias: dict {code: distancia_total_km}
        ##        previos:    dict {code: code_anterior}  (para reconstruir el camino)

        return distancias, previos

    def reconstruir_camino(self, previos, origen, destino):
        ##   Reconstruye la secuencia de vértices del camino mínimo
        ##   usando el dict de previos generado por Dijkstra.
        
        camino = []
        actual = destino

        while actual is not None:
            camino.append(actual)
            actual = previos[actual]

        camino.reverse()

        if not camino or camino[0] != origen:
        
        ##   Retorna una lista [origen, ..., destino], o una lista vacia si no existe camino.

            return []   ##    No hay camino entre el origen y el destino

        return camino
