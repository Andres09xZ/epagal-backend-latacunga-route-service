#!/usr/bin/env python3
"""Script de prueba para verificar la conexión con OSRM"""
from app.osrm_service import OSRMService

print("=" * 50)
print("TEST OSRM SERVICE")
print("=" * 50)

# Inicializar servicio
osrm = OSRMService()
print(f"✓ OSRM URL configurada: {osrm.base_url}")

# Test 1: Health check
print("\n[Test 1] Health Check")
health = osrm.health_check()
print(f"  Resultado: {'✓ OK' if health else '✗ ERROR'}")

# Test 2: Calcular ruta simple (2 puntos en Latacunga)
print("\n[Test 2] Cálculo de ruta simple")
print("  Punto A: Parque Vicente León (-78.6167, -0.9333)")
print("  Punto B: Terminal Terrestre (-78.6200, -0.9400)")

route = osrm.calculate_route([
    (-78.6167, -0.9333),  # Parque Vicente León
    (-78.6200, -0.9400)   # Terminal Terrestre
])

if route:
    print(f"  ✓ Ruta calculada exitosamente")
    print(f"  Distancia: {route['distance']:.1f} metros ({route['distance']/1000:.2f} km)")
    print(f"  Duración: {route['duration']:.1f} segundos ({route['duration']/60:.1f} minutos)")
    print(f"  Geometría incluida: {'✓' if route.get('geometry') else '✗'}")
else:
    print(f"  ✗ ERROR: No se pudo calcular la ruta")

# Test 3: Calcular ruta con múltiples puntos
print("\n[Test 3] Cálculo de ruta con 4 puntos")
route_multi = osrm.calculate_route([
    (-78.6167, -0.9333),  # Parque Vicente León
    (-78.6150, -0.9350),  # Punto intermedio 1
    (-78.6180, -0.9380),  # Punto intermedio 2
    (-78.6200, -0.9400)   # Terminal Terrestre
])

if route_multi:
    print(f"  ✓ Ruta multi-punto calculada exitosamente")
    print(f"  Distancia total: {route_multi['distance']:.1f} metros")
    print(f"  Duración total: {route_multi['duration']:.1f} segundos")
    print(f"  Número de segmentos: {len(route_multi.get('legs', []))}")
else:
    print(f"  ✗ ERROR: No se pudo calcular la ruta multi-punto")

print("\n" + "=" * 50)
print("FIN DE LAS PRUEBAS")
print("=" * 50)
