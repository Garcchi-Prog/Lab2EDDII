"""
csvprueba.py
────────────
Script de prueba para verificar que el CSV se carga correctamente
y que el grafo queda bien construido.

Uso:
    python csvprueba.py                        # usa la ruta por defecto
    python csvprueba.py data/flights_final.csv # ruta personalizada
"""

import sys
import os

# Añadimos la raíz del proyecto al path para que los imports funcionen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.Importcsv import FlightLoader


def main():
    # ── Ruta del CSV ──────────────────────────────────────────────────────────
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/flights_final.csv"
    print(f"\n{'='*55}")
    print(f"  PRUEBA DE CARGA: {ruta}")
    print(f"{'='*55}\n")

    # ── Cargar ────────────────────────────────────────────────────────────────
    loader = FlightLoader()
    exito, grafo, mensaje = loader.cargar(ruta)

    if not exito:
        print(f"[ERROR] {mensaje}")
        sys.exit(1)

    print(f"[OK] {mensaje}\n")

    # ── Estadísticas básicas ──────────────────────────────────────────────────
    print(f"{'─'*55}")
    print(f"  Vértices (aeropuertos) : {grafo.num_vertices()}")
    print(f"  Aristas  (rutas)       : {grafo.num_aristas()}")
    print(f"{'─'*55}\n")

    # ── Top 5 hubs (mayor cantidad de rutas) ─────────────────────────────────
    print("Top 5 aeropuertos con más rutas directas:")
    top5 = sorted(grafo.vertices, key=lambda a: grafo.grado(a.code), reverse=True)[:5]
    for i, a in enumerate(top5, 1):
        print(f"  {i}. {a.code:>4}  {a.name[:35]:<35}  "
              f"{a.city}, {a.country}  — {grafo.grado(a.code)} rutas")

    # ── Muestra de vecinos del hub principal ─────────────────────────────────
    hub = top5[0]
    vecinos = grafo.obtener_vecinos(hub.code)[:5]
    print(f"\nPrimeros 5 vecinos de {hub.code} ({hub.city}):")
    for v, dist in vecinos:
        print(f"  → {v.code:>4}  {v.city:<20}  {dist:>9,.1f} km")

    # ── Verificación de un aeropuerto específico ──────────────────────────────
    print("\nBúsqueda de aeropuerto 'BOG':")
    bog = grafo.airport_by_code("BOG")
    if bog:
        print(f"  Encontrado: {bog.name}, {bog.city}, {bog.country}")
        print(f"  Coordenadas: ({bog.lat:.4f}, {bog.lon:.4f})")
        print(f"  Rutas directas: {grafo.grado('BOG')}")
    else:
        print("  'BOG' no encontrado en el dataset.")

    print(f"\n{'='*55}")
    print("  Prueba completada exitosamente.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
