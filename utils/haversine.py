import math
import heapq

# Fórmula de Haversine para calcular distancia entre dos coordenadas geográficas
# Investigamos que esta es la fórmula estándar para distancias en la Tierra
def haversine(lat1, lon1, lat2, lon2):
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertimos a radianes tanto las latitudes como longitudes 
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencias entre coordenadas
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Aplicamos la fórmula del haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Distancia final en kilómetros
    distancia = R * c
    return distancia