"""
Script para crear incidencias de ejemplo en Latacunga
Ejecutar: python crear_incidencias_ejemplo.py
"""
import requests
import json

API_URL = "http://localhost:9000/api/incidencias/"

# Incidencias de ejemplo para Latacunga
incidencias = [
    # ZONA ORIENTAL
    {
        "tipo": "acopio",
        "gravedad": 5,
        "descripcion": "Acumulación grande de basura en esquina principal del sector La Matriz",
        "foto_url": "https://example.com/foto1.jpg",
        "lat": -0.9346,
        "lon": -78.6157,
        "zona": "oriental",
        "usuario_id": 1
    },
    {
        "tipo": "zona_critica",
        "gravedad": 3,
        "descripcion": "Punto crítico de acumulación de desechos en calle principal",
        "foto_url": "https://example.com/foto2.jpg",
        "lat": -0.9298,
        "lon": -78.6135,
        "zona": "oriental",
        "usuario_id": 1
    },
    {
        "tipo": "animal_muerto",
        "gravedad": 1,
        "descripcion": "Perro fallecido en la vía pública",
        "foto_url": "https://example.com/foto3.jpg",
        "lat": -0.9387,
        "lon": -78.6189,
        "zona": "oriental",
        "usuario_id": 2
    },
    {
        "tipo": "acopio",
        "gravedad": 3,
        "descripcion": "Basura en el parque Vicente León",
        "foto_url": "https://example.com/foto4.jpg",
        "lat": -0.9323,
        "lon": -78.6165,
        "zona": "oriental",
        "usuario_id": 2
    },
    {
        "tipo": "zona_critica",
        "gravedad": 5,
        "descripcion": "Punto crítico con basura desbordada cerca del mercado",
        "foto_url": "https://example.com/foto5.jpg",
        "lat": -0.9411,
        "lon": -78.6123,
        "zona": "oriental",
        "usuario_id": 1
    },
    
    # ZONA OCCIDENTAL
    {
        "tipo": "acopio",
        "gravedad": 3,
        "descripcion": "Acumulación de basura en zona residencial",
        "foto_url": "https://example.com/foto6.jpg",
        "lat": -0.9356,
        "lon": -78.6245,
        "zona": "occidental",
        "usuario_id": 3
    },
    {
        "tipo": "animal_muerto",
        "gravedad": 5,
        "descripcion": "Ganado muerto en la vía principal",
        "foto_url": "https://example.com/foto7.jpg",
        "lat": -0.9289,
        "lon": -78.6278,
        "zona": "occidental",
        "usuario_id": 3
    },
    {
        "tipo": "zona_critica",
        "gravedad": 1,
        "descripcion": "Pequeña acumulación de desechos orgánicos",
        "foto_url": "https://example.com/foto8.jpg",
        "lat": -0.9423,
        "lon": -78.6234,
        "zona": "occidental",
        "usuario_id": 2
    },
    {
        "tipo": "acopio",
        "gravedad": 5,
        "descripcion": "Basura acumulada en esquina de avenida principal",
        "foto_url": "https://example.com/foto9.jpg",
        "lat": -0.9367,
        "lon": -78.6212,
        "zona": "occidental",
        "usuario_id": 1
    },
    {
        "tipo": "zona_critica",
        "gravedad": 3,
        "descripcion": "Punto de acumulación recurrente de basura",
        "foto_url": "https://example.com/foto10.jpg",
        "lat": -0.9445,
        "lon": -78.6256,
        "zona": "occidental",
        "usuario_id": 3
    }
]

def crear_incidencias():
    """Crear todas las incidencias de ejemplo"""
    print("🚀 Creando incidencias de ejemplo para Latacunga...\n")
    
    creadas = 0
    errores = 0
    
    for i, incidencia in enumerate(incidencias, 1):
        try:
            response = requests.post(API_URL, json=incidencia)
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Incidencia {i}/10 creada - ID: {data['id']} | {incidencia['tipo']} | Gravedad: {incidencia['gravedad']} | Zona: {incidencia['zona']}")
                creadas += 1
            else:
                print(f"❌ Error {i}/10: {response.status_code} - {response.text}")
                errores += 1
                
        except Exception as e:
            print(f"❌ Error al crear incidencia {i}: {str(e)}")
            errores += 1
    
    print(f"\n📊 Resumen:")
    print(f"   ✅ Creadas: {creadas}")
    print(f"   ❌ Errores: {errores}")
    print(f"   📍 Total: {len(incidencias)}")
    
    if creadas > 0:
        print(f"\n🎯 Puedes consultar las incidencias en: {API_URL}")
        print(f"   - Oriental: {API_URL}?zona=oriental")
        print(f"   - Occidental: {API_URL}?zona=occidental")
        print(f"   - Pendientes: {API_URL}?estado=pendiente")

if __name__ == "__main__":
    try:
        crear_incidencias()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error general: {str(e)}")
