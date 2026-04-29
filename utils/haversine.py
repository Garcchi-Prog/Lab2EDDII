import math


def haversine(lat1, lon1, lat2, lon2):
    # Calcula la distancia en kilómetros entre dos coordenadas geográficas
    # usando la fórmula del Haversine.

    # Parámetros:
    #    lat1, lon1: Latitud y longitud del punto de origen (en grados decimales).
    #    lat2, lon2: Latitud y longitud del punto de destino (en grados decimales).

    # Retorna:
    #    Distancia en kilómetros (float).
    
    R = 6371.0  # Radio de la Tierra en km

    # Convertimos a radianes
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
