from collections import deque


# ============================================================
# UNION-FIND (FUERA DE LA CLASE)
# ============================================================

class UnionFind:
    """Estructura de conjuntos disjuntos para detectar ciclos."""
    
    def __init__(self, elementos):
        self.padre = {x: x for x in elementos}
        self.rango = {x: 0 for x in elementos}
    
    def encontrar(self, x):
        """Encuentra la raíz con compresión de camino."""
        if self.padre[x] != x:
            self.padre[x] = self.encontrar(self.padre[x])
        return self.padre[x]
    
    def unir(self, x, y):
        """
        Une dos conjuntos. Retorna True si se unieron,
        False si ya estaban en el mismo conjunto (hay ciclo).
        """
        raiz_x = self.encontrar(x)
        raiz_y = self.encontrar(y)
        
        if raiz_x == raiz_y:
            return False
        
        if self.rango[raiz_x] < self.rango[raiz_y]:
            self.padre[raiz_x] = raiz_y
        elif self.rango[raiz_x] > self.rango[raiz_y]:
            self.padre[raiz_y] = raiz_x
        else:
            self.padre[raiz_y] = raiz_x
            self.rango[raiz_x] += 1
        
        return True


# ============================================================
# CLASE PRINCIPAL
# ============================================================

class GrafoAnalizador:
    """
    Laboratorio 2 - Estructura de Datos II
    Algoritmos: Conexidad, Bipartito, MST (Kruskal)
    NO se usan librerías externas para los algoritmos de grafos.
    """
    
    # --------------------------------------------------------
    # 1. DFS - CONEXIDAD Y COMPONENTES
    # --------------------------------------------------------
    
    def es_conexo(self, grafo):
        """
        Determina si un grafo es conexo usando DFS.
        
        Parámetros:
            grafo: dict {vértice: [lista de vecinos]}
        
        Retorna:
            (bool_conexo, num_componentes, lista_tamaños, lista_componentes)
        """
        visitados = set()
        componentes = []
        
        for vertice in grafo:
            if vertice not in visitados:
                componente_actual = []
                pila = [vertice]
                visitados.add(vertice)
                
                while pila:
                    actual = pila.pop()
                    componente_actual.append(actual)
                    
                    for vecino in grafo[actual]:
                        if vecino not in visitados:
                            visitados.add(vecino)
                            pila.append(vecino)
                
                componentes.append(componente_actual)
        
        num_componentes = len(componentes)
        es_conexo = (num_componentes == 1)
        tamaños = [len(c) for c in componentes]
        
        return es_conexo, num_componentes, tamaños, componentes
    
    
    # --------------------------------------------------------
    # 2. BFS - BIPARTITO
    # --------------------------------------------------------
    
    def es_bipartito(self, grafo, vertices_a_revisar=None):
        """
        Determina si un conjunto de vértices forma un grafo bipartito.
        Usa BFS con coloreo (0 y 1).
        """
        if vertices_a_revisar is None:
            vertices_a_revisar = list(grafo.keys())
        
        color = {}
        
        for inicio in vertices_a_revisar:
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
    
    
    def verificar_componente_mas_grande(self, grafo):
        """Encuentra la componente más grande y verifica si es bipartita."""
        _, num_comp, tamaños, componentes = self.es_conexo(grafo)
        
        idx_mas_grande = tamaños.index(max(tamaños))
        comp_mas_grande = componentes[idx_mas_grande]
        
        print(f"\n{'='*50}")
        print("ANÁLISIS DE BIPARTITO")
        print(f"{'='*50}")
        print(f"Total de componentes: {num_comp}")
        print(f"Componente más grande: #{idx_mas_grande + 1}")
        print(f"Vértices en componente más grande: {len(comp_mas_grande)}")
        print(f"Vértices: {sorted(comp_mas_grande)}")
        
        if self.es_bipartito(grafo, comp_mas_grande):
            print("Resultado: La componente más grande ES BIPARTITA")
            return True
        else:
            print("Resultado: La componente más grande NO ES BIPARTITA ❌")
            return False
    
    
    # --------------------------------------------------------
    # 3. KRUSKAL - MST
    # --------------------------------------------------------
    
    def kruskal_mst(self, grafo, aristas):
        """
        Calcula el MST usando Kruskal.
        
        Parámetros:
            grafo: dict {vértice: [vecinos]}
            aristas: lista de (peso, origen, destino)
        
        Retorna:
            (peso_total, aristas_del_mst)
        """
        vertices = list(grafo.keys())
        aristas_ordenadas = sorted(aristas, key=lambda x: x[0])
        
        uf = UnionFind(vertices)
        
        peso_total = 0
        aristas_mst = []
        
        for peso, origen, destino in aristas_ordenadas:
            if uf.unir(origen, destino):
                aristas_mst.append((origen, destino, peso))
                peso_total += peso
                
                if len(aristas_mst) == len(vertices) - 1:
                    break
        
        return peso_total, aristas_mst
    
    
    def mst_por_componente(self, grafo, aristas):
        """Calcula MST para cada componente conexa."""
        _, num_comp, _, componentes = self.es_conexo(grafo)
        
        print(f"\n{'='*50}")
        print("ANÁLISIS DE MST (ÁRBOL DE EXPANSIÓN MÍNIMA)")
        print(f"{'='*50}")
        print(f"Total de componentes: {num_comp}")
        
        resultados = []
        
        for i, comp in enumerate(componentes, 1):
            comp_set = set(comp)
            
            aristas_comp = []
            for peso, origen, destino in aristas:
                if origen in comp_set and destino in comp_set:
                    aristas_comp.append((peso, origen, destino))
            
            subgrafo = {v: [] for v in comp}
            for peso, origen, destino in aristas_comp:
                subgrafo[origen].append(destino)
                subgrafo[destino].append(origen)
            
            peso_mst, aristas_mst = self.kruskal_mst(subgrafo, aristas_comp)
            
            print(f"\n--- Componente {i} ({len(comp)} vértices) ---")
            print(f"Vértices: {sorted(comp)}")
            print(f"Peso del MST: {peso_mst}")
            print(f"Aristas en MST: {len(aristas_mst)}")
            for u, v, p in aristas_mst:
                print(f"  {u} --({p})--> {v}")
            
            resultados.append({
                'componente': i,
                'vertices': len(comp),
                'peso_mst': peso_mst,
                'aristas_mst': aristas_mst
            })
        
        peso_total_global = sum(r['peso_mst'] for r in resultados)
        print(f"\n{'='*50}")
        print(f"PESO TOTAL DE TODOS LOS MST: {peso_total_global}")
        print(f"{'='*50}")
        
        return resultados
    
    
    # --------------------------------------------------------
    # AUXILIARES
    # --------------------------------------------------------
    
    def analizar_conexidad(self, grafo):
        """Muestra resultados del análisis de conexidad."""
        conexo, num_comp, tamaños, componentes = self.es_conexo(grafo)
        
        print(f"\n{'='*50}")
        print("ANÁLISIS DE CONEXIDAD")
        print(f"{'='*50}")
        
        if conexo:
            print("Resultado: El grafo ES CONEXO")
            print(f"Vértices totales: {sum(tamaños)}")
        else:
            print(f"Resultado: El grafo NO ES CONEXO ❌")
            print(f"Número de componentes: {num_comp}")
            print("\nDetalle de componentes:")
            for i, (tam, comp) in enumerate(zip(tamaños, componentes), 1):
                print(f"  Componente {i}: {tam} vértices")
                print(f"    Vértices: {sorted(comp)}")
        
        return conexo, num_comp, tamaños, componentes
    
    
    def construir_grafo_no_dirigido(self, aristas_dirigidas):
        """
        Convierte aristas dirigidas a grafo no dirigido.
        Elimina duplicados y auto-bucles.
        """
        grafo = {}
        aristas_set = set()
        
        for peso, origen, destino in aristas_dirigidas:
            if origen == destino:
                continue
            
            u, v = sorted([origen, destino])
            clave = (u, v)
            
            if clave not in aristas_set:
                aristas_set.add(clave)
                
                if u not in grafo:
                    grafo[u] = []
                if v not in grafo:
                    grafo[v] = []
                
                grafo[u].append(v)
                grafo[v].append(u)
        
        aristas_unicas = []
        for u, v in aristas_set:
            pesos = [p for p, o, d in aristas_dirigidas 
                    if sorted([o, d]) == [u, v]]
            peso_min = min(pesos) if pesos else 0
            aristas_unicas.append((peso_min, u, v))
        
        return grafo, aristas_unicas
    